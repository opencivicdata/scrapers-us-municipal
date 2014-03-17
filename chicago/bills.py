from .legistar import LegistarScraper
import lxml
import lxml.etree

from pupa.models import Bill


class ChicagoBillScraper(LegistarScraper):
    base_url = 'https://chicago.legistar.com/'
    legislation_url = 'https://chicago.legistar.com/Legislation.aspx'

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

    def expandLegislationSummary(self, summary):
        """
        Take a row as given from the searchLegislation method and retrieve the
        details of the legislation summarized by that row.
        """
        return self.expandSummaryRow(summary,
                                     self.parseLegislationDetail)

    def expandHistorySummary(self, action):
        """
        Take a row as given from the parseLegislationDetail method and
        retrieve the details of the history event summarized by that
        row.
        """
        return self.expandSummaryRow(action,
                                     self.parseHistoryDetail)

    def expandSummaryRow(self, row, parse_function):
        """
        Take a row from a data table and use the URL value from that row to
        retrieve more details. Parse those details with parse_function.
        """
        print(row['URL'])
        page = self.lxmlize(row['URL'])

        return parse_function(page)

    def _get_general_details(self, detail_div) :
        """
        Parse the data in the top section of a detail page.
        """
        key_query = ".//span[contains(@id, 'ctl00_ContentPlaceHolder1_lbl') "\
                    "        and not(contains(@id, '2'))]"

        value_query = ".//*[(contains(@id, 'ctl00_ContentPlaceHolder1_lbl') "\
                      "     or contains(@id, 'ctl00_ContentPlaceHolder1_hyp')) "\
                      "     and contains(@id, '2')]"


        keys = [span.text_content().replace(':', '').strip()
                for span
                in detail_div.xpath(key_query)]

        values = [element.text_content().strip()
                  for element
                  in detail_div.xpath(value_query)]

        return dict(zip(keys, values))


    def parseLegislationDetail(self, page):
        """
        Take a legislation detail page and return a dictionary of
        the different data appearing on the page

        Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
        """

        # Pull out the top matter
        detail_div = page.xpath("//div[@id='ctl00_ContentPlaceHolder1_pageDetails']")[0]
        details = self._get_general_details(detail_div)

        details[u'Attachments'] = []

        attachment_url = detail_div.xpath(".//span[@id='ctl00_ContentPlaceHolder1_lblAttachments2']/a")

        for attachment in attachment_url :
            details[u'Attachments'].append({
                'url' : attachment.attrib['href'],
                'label' : attachment.text_content()})

        if u'Related files' in details :
            details[u'Related files'] = details[u'Related files'].split(',')

        if u'Sponsors' in details :
            details[u'Sponsors'] = details[u'Sponsors'].split(',')

        if u'Topics' in details :
            details[u'Topics'] = details[u'Topics'].split(',')

        return details


    def get_bills(self):
        for i, page in enumerate(self.searchLegislation()) :
            for legislation_summary in self.parseSearchResults(page) :
                if title.strip() == "":
                    continue

                bill = Bill(name=legislation_summary['Record #'],
                            session=self.session,
                            title=legislation_summary['Title'],
                            type = [legislation_summary['Type'].lower()],
                            organization=self.jurisdiction.name)

                bill.add_source(legislation_summary['URL'])

                legislation_details = self.expandLegislationSummary(legislation_summary)

                for related_bill in legislation_details.get('Related files', []) :
                    bill.add_related_bill(name = related_bill,
                                          session = self.session,
                                          relation='other-session',
                                          chamber=None)

                for i, sponsor in enumerate(legislation_details.get('Sponsors', [])) :
                    if i == 0 :
                        primary = True
                        sponsorship_type = "Primary"
                    else :
                        primary = False
                        sponsorship_type = "Regular"

                    bill.add_sponsor(sponsor, sponsorship_type,
                                     'person', primary)

                for subject in legislation_details.get(u'Topics', []) :
                    bill.add_subject(subject)

                for attachment in legislation_details.get(u'Attachments', []) :
                    bill.add_version_link('PDF',
                                          attachment['url'],
                                          mimetype="application/pdf")


                yield bill
