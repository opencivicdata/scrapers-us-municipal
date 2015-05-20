from .legistar import LegistarScraper
import lxml
import lxml.etree
import datetime
import pytz

from pupa.scrape import Bill, Vote


class ChicagoBillScraper(LegistarScraper):
    base_url = 'https://chicago.legistar.com/'
    legislation_url = 'https://chicago.legistar.com/Legislation.aspx'
    timezone = "US/Central"

    def session(self, action_date) :
        if action_date < datetime.datetime(2011, 5, 18, 
                                           tzinfo=pytz.timezone(self.timezone)) :
            return "2007"
        elif action_date < datetime.datetime(2015, 5, 18,
                                             tzinfo=pytz.timezone(self.timezone)) :
            return "2011"
        else :
            return "2015"



    def searchLegislation(self, search_text='', created_after=None,
                          created_before=None, num_pages = None):
        """
        Submit a search query on the legislation search page, and return a list
        of summary results.
        """
        page = self.lxmlize(self.legislation_url)

        payload = {}

        # Enter the search parameters TODO: Each of the possible form
        # fields should be represented as keyword arguments to this
        # function. The default query string should be for the the
        # default 'Legislative text' field.
        payload['ctl00$ContentPlaceHolder1$txtText'] = search_text

        if created_after and created_before :
            payload.update(dateWithin(created_after, created_before))

        elif created_before :
            payload.update(dateBound(created_before))
            payload['ctl00$ContentPlaceHolder1$radFileCreated'] = '<'

        elif created_after :
            payload.update(dateBound(created_after))
            payload['ctl00$ContentPlaceHolder1$radFileCreated'] = '>'


        # Return up to one million search results
        payload['ctl00_ContentPlaceHolder1_lstMax_ClientState'] = '{"value":"1000000"}'
        payload['ctl00$ContentPlaceHolder1$btnSearch'] = 'Search Legislation'
        payload['ctl00$ContentPlaceHolder1$lstYearsAdvanced'] = 'All Years'


        payload.update(self.sessionSecrets(page))

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

        for page in self.searchLegislation(created_after=datetime.datetime(2014, 1, 1), created_before=datetime.datetime(2014, 2, 1)) :
            for legislation_summary in self.parseSearchResults(page) :
                title = legislation_summary['Title'].strip()

                if not title or not legislation_summary['Intro\xa0Date'] :
                    continue
                    # https://chicago.legistar.com/LegislationDetail.aspx?ID=1800754&GUID=29575A7A-5489-4D8B-8347-4FC91808B201&Options=Advanced&Search=
                    # doesn't have an intro date
                    

                if legislation_summary['Type'].lower() in ('order', 
                                                           'claim', 
                                                           'communication', 
                                                           'report', 
                                                           'oath of office') :
                    bill_type = None
                else :
                    bill_type = legislation_summary['Type'].lower()

                bill_session = self.session(self.toTime(legislation_summary['Intro\xa0Date']))

                bill = Bill(identifier=legislation_summary['Record #'],
                            legislative_session=bill_session,
                            title=title,
                            classification=bill_type,
                            from_organization={"name":"Chicago City Council"})

                bill.add_source(legislation_summary['url'])

                bill, votes = self.addDetails(bill, legislation_summary['url'])

                yield bill
                for vote in votes :
                    yield vote
        


    def extractVotes(self, action_detail_url) :
        action_detail_page = self.lxmlize(action_detail_url)
        try:
            vote_table = action_detail_page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridVote_ctl00']")[0]
        except IndexError:
            self.warning("No votes found in table")
            return None, []
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
            try :
                action_date =  self.toTime(action['Date']).date().isoformat()
            except AttributeError : # https://chicago.legistar.com/LegislationDetail.aspx?ID=1424866&GUID=CEC53337-B991-4268-AE8A-D4D174F8D492
                continue

            if action_description :
                act = bill.add_action(action_description,
                                action_date,
                                classification=ACTION_CLASSIFICATION[action_description])
                act.add_related_entity(action['Action\xa0By']['label'],
                                      entity_type="organization")
                if 'url' in action['Action\xa0Details'] :
                    action_detail_url = action['Action\xa0Details']['url']
                    result, votes = self.extractVotes(action_detail_url)

                    if votes and result : # see https://github.com/datamade/municipal-scrapers-us/issues/15
                        action_vote = Vote(legislative_session=bill.legislative_session, 
                                           motion_text=action_description,
                                           classification=None,
                                           start_date=action_date,
                                           result=result,
                                           bill=bill)
                        action_vote.add_source(action_detail_url)
                        for option, voter in votes :
                            action_vote.vote(option, voter)
                        
                        all_votes.append(action_vote)


        return all_votes


    def addDetails(self, bill, detail_url) :
        detail_page = self.lxmlize(detail_url)
        detail_div = detail_page.xpath(".//div[@id='ctl00_ContentPlaceHolder1_pageDetails']")[0]

        legislation_details = self.parseDetails(detail_div)
        
        for related_bill in legislation_details.get('Related files', []) :
            title = bill.title
            if ("sundry" in title.lower()
                or "miscellaneous" in title.lower()): #these are ominbus
                bill.add_related_bill(identifier = related_bill['label'],
                                  legislative_session = bill.legislative_session,
                                  relation_type='replaces')
            #for now we're skipping related bills if they
            #don't contain words that make us think they're
            #in a ominbus relationship with each other

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
            if attachment['label'] :
                bill.add_version_link(attachment['label'],
                                      attachment['url'],
                                      media_type="application/pdf")

        history_table = detail_page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridLegislation_ctl00']")[0]

        
        votes = self.addBillHistory(bill, history_table)

        return bill, votes

        


ACTION_CLASSIFICATION = {'Referred' : 'committee-referral',
                         'Re-Referred' : 'committee-referral',
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
                         'Withdrawn' : 'withdrawal',
                         'Signed by Mayor' : 'executive-signature',
                         'Appointment' : 'appointment',
                         'Direct Introduction' : None,
                         'Remove Co-Sponsor(s)' : None,
                         'Add Co-Sponsor(s)' : None,
                         'Tabled' : None,
                         'Rules Suspended - Immediate Consideration' : None,
                         'Committee Discharged' : None,
                         'Held in Committee' : None,
                         'Recommended for Re-Referral' : None,
                         'Published in Special Pamphlet' : None,
                         'Adopted as Substitute' : None,
                         'Deferred and Published' : None,
                         'Approved as Amended' : 'passage',
}

VOTE_OPTIONS = {'yea' : 'yes',
                'rising vote' : 'yes',
                'nay' : 'no',
                'recused' : 'excused'}
        
    
def dateWithin(created_after, created_before) :
    payload = dateBound(created_after)

    payload['ctl00$ContentPlaceHolder1$txtFileCreated2'] =\
        '{d.year}-{d.month:02}-{d.day:02}'.format(d=created_before)
    payload['ctl00$ContentPlaceHolder1$txtFileCreated2$dateInput'] =\
        '{d.month}/{d.day}/{d.year}'.format(d=created_before)

    payload['ctl00_ContentPlaceHolder1_txtFileCreated2_dateInput_ClientState'] =\
        '{{"enabled":true, "emptyMessage":"","validationText":"{d.year}-{d.month:02}-{d.day:02}-00-00-00","valueAsString":"{d.year}-{d.month:02}-{d.day:02}-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00", "lastSetTextBoxValue":"{d.month}/{d.day}/{d.year}"}}'.format(d=created_before)

    payload['ctl00$ContentPlaceHolder1$radFileCreated'] = 'between'

    return payload



def dateBound(creation_date) :
    payload = {}

    payload['ctl00$ContentPlaceHolder1$txtFileCreated1'] =\
        '{d.year}-{d.month:02}-{d.day:02}'.format(d=creation_date)
    payload['ctl00$ContentPlaceHolder1$txtFileCreated1$dateInput'] =\
        '{d.month}/{d.day}/{d.year}'.format(d=creation_date)

    payload['ctl00_ContentPlaceHolder1_txtFileCreated1_dateInput_ClientState'] =\
        '{{"enabled":true, "emptyMessage":"","validationText":"{d.year}-{d.month:02}-{d.day:02}-00-00-00","valueAsString":"{d.year}-{d.month:02}-{d.day:02}-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00", "lastSetTextBoxValue":"{d.month}/{d.day}/{d.year}"}}'.format(d=creation_date)

    return payload

