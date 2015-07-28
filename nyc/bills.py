from legistar.bills import LegistarBillScraper
from pupa.scrape import Bill, Vote
import datetime
from collections import defaultdict

class NYCBillScraper(LegistarBillScraper):
    LEGISLATION_URL = 'http://legistar.council.nyc.gov/Legislation.aspx'
    BASE_URL = 'http://legistar.council.nyc.gov/'
    TIMEZONE = "US/Eastern"

    VOTE_OPTIONS = {'affirmative' : 'yes',
                    'absent' : 'absent',
                    'medical' : 'absent'}

    def scrape(self):

        counter = defaultdict(int)
        for leg_summary in self.legislation(created_after=datetime.datetime(2015, 1, 1)) :
            leg_type = BILL_TYPES.get(leg_summary['Type'], 
                                              None)

            bill = Bill(identifier=leg_summary['File\xa0#'],
                        title=leg_summary['Title'],
                        legislative_session='2015',
                        classification=leg_type,
                        from_organization={"name":"New York City Council"})
            bill.add_source(leg_summary['url'])

            leg_details, history = self.details(leg_summary['url'])

            for sponsorship in self._sponsors(leg_details.get('Sponsors', [])) :
                sponsor, sponsorship_type, primary = sponsorship
                bill.add_sponsorship(sponsor, sponsorship_type,
                                     'person', primary)


            for i, attachment in enumerate(leg_details.get(u'Attachments', [])) :
                if i == 0 :
                    bill.add_version_link(attachment['label'],
                                          attachment['url'],
                                          media_type="application/pdf")
                else :
                    bill.add_document_link(attachment['label'],
                                           attachment['url'],
                                           media_type="application/pdf")

            for action in history :
                action_description = action['Action']
                action_date = self.toDate(action['Date'])
                responsible_org = action['Action\xa0By']
                if responsible_org == 'City Council' :
                    responsible_org = 'New York City Council'
                act = bill.add_action(action_description,
                                      action_date,
                                      organization={'name': responsible_org},
                                      classification=None)

                if 'url' in action['Action\xa0Details'] :
                    action_detail_url = action['Action\xa0Details']['url']
                    result, votes = self.extractVotes(action_detail_url)
                    if votes :
                        action_vote = Vote(legislative_session=bill.legislative_session, 
                                           motion_text=action_description,
                                           organization={'name': responsible_org},
                                           classification=None,
                                           start_date=action_date,
                                           result=result,
                                           bill=bill)
                        action_vote.add_source(action_detail_url)

                        yield action_vote
                
            yield bill

            counter[leg_summary['Type']] += 1

        print(counter)

    def _sponsors(self, sponsors) :
        for i, sponsor in enumerate(sponsors) :
            if i == 0 :
                primary = True
                sponsorship_type = "Primary"
            else :
                primary = False
                sponsorship_type = "Regular"
            yield sponsor['label'], sponsorship_type, primary
                

BILL_TYPES = {'Introduction' : 'bill',
              'Resolution'   : 'resolution'}


ACTION_CLASSIFICATION = {}
