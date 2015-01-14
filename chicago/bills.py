from .legistar import LegistarScraper
import lxml
import lxml.etree

from pupa.scrape import Bill, Vote


class ChicagoBillScraper(LegistarScraper):
    base_url = 'https://chicago.legistar.com/'
    legislation_url = 'https://chicago.legistar.com/Legislation.aspx'
    timezone = "US/Central"


    def searchLegislation(self, search_text='', created_before=None,
                          created_after=None, num_pages = None):
        """
        Submit a search query on the legislation search page, and return a list
        of summary results.
        """

        page = self.lxmlize(self.legislation_url)

        payload = self.sessionSecrets(page)

        # Enter the search parameters TODO: Each of the possible form
        # fields should be represented as keyword arguments to this
        # function. The default query string should be for the the
        # default 'Legislative text' field.
        payload['ctl00$ContentPlaceHolder1$txtText'] = search_text

        if created_before or created_after:
            if created_before :
                creation_date = created_before
                relation = '[<]'
            else:
                creation_date = created_after
                relation = '[>]'

            payload['ctl00$ContentPlaceHolder1$radFileCreated'] = relation
            payload['ctl00_ContentPlaceHolder1_txtFileCreated1_dateInput_ClientState'] = '{"enabled":true,"emptyMessage":"","validationText":"%s-00-00-00","valueAsString":"%s-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}' % (creation_date, creation_date)

        # Return up to one million search results
        payload['ctl00_ContentPlaceHolder1_lstMax_ClientState'] = '{"value":"1000000"}'

        payload['ctl00$ContentPlaceHolder1$btnSearch'] = 'Search Legislation'
        payload['ctl00_ContentPlaceHolder1_lstYearsAdvanced_ClientState'] = '{"logEntries":[],"value":"All","text":"All Years","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'

        return self.pages(self.legislation_url, payload)

    def parseSearchResults(self, page) :
        """Take a page of search results and return a sequence of data
        of tuples about the legislation, of the form

        ('Document ID', 'Document URL', 'Type', 'Status', 'Introduction Date'
        'Passed Date', 'Main Sponsor', 'Title')
        """
        table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridMain_ctl00']")[0]
        for legislation, headers, row in self.parseDataTable(table):
            # Do legislation search-specific stuff
            # ------------------------------------
            # First column should be the ID of the record.
            id_key = headers[0]
            try:
                legislation_id = legislation[id_key]['label']
            except TypeError:
                continue
            legislation_url = legislation[id_key]['url'].split(self.base_url)[-1]
            legislation[id_key] = legislation_id
            legislation['URL'] = self.base_url + legislation_url.split('&Options')[0]

            yield legislation


    def parseLegislationDetail(self, page):
        """
        Take a legislation detail page and return a dictionary of
        the different data appearing on the page

        Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
        """

        # Pull out the top matter
        detail_div = page.xpath("//div[@id='ctl00_ContentPlaceHolder1_pageDetails']")[0]
        details = self.parseDetails(detail_div)

        

        return details

    def scrape(self):
        self.session = '2011'

        for i, page in enumerate(self.searchLegislation()) :
            for legislation_summary in self.parseSearchResults(page) :
                title = legislation_summary['Title'].strip()
                if title == "":
                    continue

                if legislation_summary['Type'].lower() in ('order', 'ordinance', 'claim', 'communication', 'report', 'oath of office') :
                    bill_type = 'concurrent order'
                else :
                    bill_type = legislation_summary['Type'].lower()

                bill = Bill(identifier=legislation_summary['Record #'],
                            legislative_session=self.session,
                            title=title,
                            #classification=[legislation_summary['Type'].lower()],
                            classification=bill_type,
                            from_organization=self.jurisdiction.name)

                bill.add_source(legislation_summary['URL'])


                try :
                    detail_page = self.lxmlize(legislation_summary['URL'])
                    detail_div = detail_page.xpath(".//div[@id='ctl00_ContentPlaceHolder1_pageDetails']")[0]
                except IndexError :
                    print(legislation_summary)
                    continue

                legislation_details = self.parseDetails(detail_div)
                history_table = detail_page.xpath(
                        "//table[@id='ctl00_ContentPlaceHolder1_gridLegislation_ctl00']")[0]
                history = self.parseDataTable(history_table)

                for related_bill in legislation_details.get('Related files', []) :
                    # need different relation_type
                    bill.add_related_bill(identifier = related_bill,
                                          legislative_session = self.session,
                                          relation_type='replaces')

                for i, sponsor in enumerate(legislation_details.get('Sponsors', [])) :
                    if i == 0 :
                        primary = True
                        sponsorship_type = "Primary"
                    else :
                        primary = False
                        sponsorship_type = "Regular"

                    bill.add_sponsorship(sponsor['label'], sponsorship_type,
                                         'person', primary)

                if u'Topics' in legislation_details :
                    for subjuct in legislation_details[u'Topics'].split(',') :
                        bill.add_subject(subject)

                for attachment in legislation_details.get(u'Attachments', []) :
                    bill.add_version_link('PDF',
                                          attachment['url'],
                                          mimetype="application/pdf")

                for action, _, _ in history :
                    action_description = action['Action']
                    try :
                        if action_description :
                            bill.add_action(action_description,
                                            action['Date'].date().isoformat(),
                                            organization=action['Action\xa0By'],
                                            classification=action_classification[action_description])
                    except KeyError :
                        if action_description not in ('Direct Introduction',
                                                      'Remove Co-Sponsor(s)',
                                                      'Held in Committee',
                                                      'Deferred and Published') :
                            print(action_description)
                            raise
                                    

                yield bill


action_classification = {'Referred' : 'committee-referral',
                         'Recommended to Pass' : 'committee-passage-favorable',
                         'Passed as Substitute' : 'passage',
                         'Adopted' : 'passage',
                         'Approved' : 'passage',
                         'Passed'  : 'passage',
                         'Substituted in Committee' : 'substitution',
                         'Failed to Pass' : 'failure',
                         'Recommended Do Not Pass' : 'committee-passage-unfavorable',
                         'Amended in Committee' : 'amendment-passage',
                         'Placed on File' : 'filing',
                         'Signed by Mayor' : 'executive-signature',
                         'Appointment' : 'appointment'}
