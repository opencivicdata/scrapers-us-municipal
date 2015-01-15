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
            legislation['url'] = self.base_url + legislation_url.split('&Options')[0]

            yield legislation


    def scrape(self):
        self.session = '2011'
        # while True :
        #     while True :
        #         bill = Bill('1','2','3')
        #         bill.add_source('foo')
        #         url = 'https://chicago.legistar.com/LegislationDetail.aspx?ID=2102554&GUID=34916110-5459-47D7-887C-629CC2784FBB'
        #         bill, votes = self.addDetails(bill, url)

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
                            classification=bill_type,
                            from_organization=self.jurisdiction.name)

                bill.add_source(legislation_summary['url'])

                bill, votes = self.addDetails(bill, legislation_summary['url'])

                yield bill
                for vote in votes :
                    yield vote
        


    def extractVotes(self, action_detail_url) :
        action_detail_page = self.lxmlize(action_detail_url)
        vote_table = action_detail_page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridVote_ctl00']")[0]
        votes = list(self.parseDataTable(vote_table))
        vote_list = []
        for vote, _, _ in votes :
            raw_option = vote['Vote'].lower()
            vote_list.append((VOTE_OPTIONS.get(raw_option, raw_option), 
                              vote['Person Name']['label']))

        action_detail_div = action_detail_page.xpath(".//div[@id='ctl00_ContentPlaceHolder1_pageTop1']")[0]
        action_details = self.parseDetails(action_detail_div)
        result = action_details['Result'].lower()

        return result, vote_list



    def addBillHistory(self, bill, history_table) :
        all_votes = []
        
        history = self.parseDataTable(history_table)

        for action, _, _ in history :
            action_description = action['Action']
            action_date =  action['Date'].date().isoformat()
            try :
                if action_description :
                    bill.add_action(action_description,
                                    action_date,
                                    organization=action['Action\xa0By'],
                                    classification=ACTION_CLASSIFICATION[action_description])
                    if 'url' in action['Action\xa0Details'] :
                        action_detail_url = action['Action\xa0Details']['url']
                        result, votes = self.extractVotes(action_detail_url)

                        if votes :
                            action_vote = Vote(legislative_session=self.session, 
                                               motion_text=action_description,
                                               classification='bill-passage',
                                               start_date=action_date,
                                               result=result,
                                               bill=bill.identifier)
                            action_vote.add_source(action_detail_url)
                            for option, voter in votes :
                                action_vote.vote(option, voter)
                        
                            all_votes.append(action_vote)

            except KeyError :
                if action_description not in ('Direct Introduction',
                                              'Remove Co-Sponsor(s)',
                                              'Held in Committee',
                                              'Deferred and Published') :
                    print(action_description)
                    raise


        return all_votes


    def addDetails(self, bill, detail_url) :
        detail_page = self.lxmlize(detail_url)
        detail_div = detail_page.xpath(".//div[@id='ctl00_ContentPlaceHolder1_pageDetails']")[0]

        legislation_details = self.parseDetails(detail_div)
        

        for related_bill in legislation_details.get('Related files', []) :
            # need different relation_type
            bill.add_related_bill(identifier = related_bill['label'],
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
            bill.add_version_link(attachment['label'],
                                  attachment['url'],
                                  media_type="application/pdf")

        history_table = detail_page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridLegislation_ctl00']")[0]

        
        votes = self.addBillHistory(bill, history_table)

        return bill, votes

        


ACTION_CLASSIFICATION = {'Referred' : 'committee-referral',
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

VOTE_OPTIONS = {'yea' : 'yes'}
