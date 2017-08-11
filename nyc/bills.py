from legistar.bills import LegistarBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
from collections import defaultdict
import pytz

class NYCBillScraper(LegistarBillScraper):
    LEGISLATION_URL = 'http://legistar.council.nyc.gov/Legislation.aspx'
    BASE_URL = 'http://legistar.council.nyc.gov/'
    TIMEZONE = "US/Eastern"

    VOTE_OPTIONS = {'affirmative' : 'yes',
                    'negative' : 'no',
                    'conflict' : 'absent',
                    'maternity': 'excused',
                    'paternity' : 'excused',
                    'bereavement': 'excused',
                    'non-voting' : 'not voting',
                    'jury duty' : 'excused',
                    'absent' : 'absent',
                    'medical' : 'excused'}

    SESSION_STARTS = (2014, 2010, 2006, 2002, 1996)

    def sessions(self, action_date) :
        for session in self.SESSION_STARTS :
            if action_date >= datetime.datetime(session, 1, 1, 
                                               tzinfo=pytz.timezone(self.TIMEZONE)) :
                return str(session)


    def scrape(self):
        for leg_summary in self.legislation(created_after=datetime.datetime(2014, 1, 1)) :
            leg_type = BILL_TYPES[leg_summary['Type']]
            
            bill = Bill(identifier=leg_summary['File\xa0#'],
                        title=leg_summary['Title'],
                        legislative_session=None,
                        classification=leg_type,
                        from_organization={"name":"New York City Council"})
            bill.add_source(leg_summary['url'], note='web')

            leg_details = self.legDetails(leg_summary['url'])
            history = self.history(leg_summary['url'])

            if leg_details['Name']:
                bill.add_title(leg_details['Name'],
                               note='created by administrative staff')

            if 'Summary' in leg_details :
                bill.add_abstract(leg_details['Summary'], note='')

            if leg_details['Law number'] :
                bill.add_identifier(leg_details['Law number'], 
                                    note='law number')

            for sponsorship in self._sponsors(leg_details.get('Sponsors', [])) :
                sponsor, sponsorship_type, primary = sponsorship
                bill.add_sponsorship(sponsor, sponsorship_type,
                                     'person', primary)

            
            for attachment in leg_details.get('Attachments', []) :
                if attachment['label']:
                    bill.add_document_link(attachment['label'],
                                           attachment['url'],
                                           media_type="application/pdf")

            history = list(history)

            if history :
                earliest_action = min(self.toTime(action['Date']) 
                                      for action in history)

                bill.legislative_session = self.sessions(earliest_action)
            else :
                bill.legislative_session = str(self.SESSION_STARTS[0])

            for action in history :
                action_description = action['Action']
                if not action_description :
                    continue
                    
                action_class = ACTION_CLASSIFICATION[action_description]

                action_date = self.toDate(action['Date'])
                responsible_org = action['Action\xa0By']
                if responsible_org == 'City Council' :
                    responsible_org = 'New York City Council'
                elif responsible_org == 'Administration' :
                    responsible_org = 'Mayor'
                   
                if responsible_org == 'Town Hall Meeting' :
                    continue
                else :
                    act = bill.add_action(action_description,
                                          action_date,
                                          organization={'name': responsible_org},
                                          classification=action_class)

                if 'url' in action['Action\xa0Details'] :
                    action_detail_url = action['Action\xa0Details']['url']
                    if action_class == 'referral-committee' :
                        action_details = self.actionDetails(action_detail_url)
                        referred_committee = action_details['Action text'].rsplit(' to the ', 1)[-1]
                        act.add_related_entity(referred_committee,
                                               'organization',
                                               entity_id = _make_pseudo_id(name=referred_committee))
                    result, votes = self.extractVotes(action_detail_url)
                    if result and votes :
                        action_vote = VoteEvent(legislative_session=bill.legislative_session, 
                                           motion_text=action_description,
                                           organization={'name': responsible_org},
                                           classification=action_class,
                                           start_date=action_date,
                                           result=result,
                                           bill=bill)
                        action_vote.add_source(action_detail_url, note='web')

                        for option, voter in votes :
                            action_vote.vote(option, voter)


                        yield action_vote
            
            text = self.text(leg_summary['url'])

            if text :
                bill.extras = {'local_classification' : leg_summary['Type'],
                               'full_text' : text}
            else :
                bill.extras = {'local_classification' : leg_summary['Type']}

            yield bill


    def _sponsors(self, sponsors) :
        for i, sponsor in enumerate(sponsors) :
            if i == 0 :
                primary = True
                sponsorship_type = "Primary"
            else :
                primary = False
                sponsorship_type = "Regular"
            
            sponsor_name = sponsor['label']
            if sponsor_name.startswith(('(in conjunction with',
                                        '(by request of')) :
                continue 

            if sponsor_name == 'Letitia James' :
                sponsor_name = 'Letitia Ms. James'

            yield sponsor_name, sponsorship_type, primary
                

BILL_TYPES = {'Introduction' : 'bill',
              'Resolution'   : 'resolution',
              'Land Use Application': None, 
              'Oversight': None, 
              'Land Use Call-Up': None, 
              'Communication': None, 
              "Mayor's Message": None, 
              'Local Laws 2015': 'bill', 
              'Commissioner of Deeds' : None,
              'Town Hall Meeting' : None,
              'Tour': None, 
              'Petition': 'petition', 
              'SLR': None,
              'City Agency Report': None}


ACTION_CLASSIFICATION = {
    'Tour Held by Committee' : None,
    'Hearing on P-C Item by Comm' : None,
    'Approved by Committee with Modifications and Referred to CPC' : 'committee-passage',
    'Approved by Committee with Modifications' : 'committee-passage',
    'Approved by Subcommittee with Modifications' : 'committee-passage',
    'Hearing Scheduled by Mayor' : None,
    'P-C Item Approved by Comm' : 'committee-passage',
    'P-C Item Approved by Subcommittee with Companion Resolution' : 'committee-passage',
    'Recessed' : None,
    'Amendment Proposed by Comm' : 'amendment-introduction',
    'P-C Item Laid Over by Comm' : 'deferral',
    'Approved by Subcommittee with Modifications and Referred to CPC' : 'committee-passage',
    'Re-referred to Committee by Council' : 'referral-committee',
    'Approved by Subcommittee' : 'committee-passage',
    'Amended by Committee' : 'amendment-passage',
    'Referred to Comm by Council' : 'referral-committee',
    'Sent to Mayor by Council' : None,
    'P-C Item Approved by Committee with Companion Resolution' : 'committee-passage',
    'P-C Item Filed by Subcommittee with Companion Resolution' : 'filing',
    'Approved by Council' : 'passage',
    'Hearing Held by Mayor' : None,
    'Approved, by Council' : 'passage',
    'Introduced by Council' : 'introduction',
    'Approved by Committee with Companion Resolution' : 'committee-passage',
    'Rcvd, Ord, Prnt, Fld by Council' : 'filing',
    'Disapproved by Committee with Companion Resolution' : 'committee-failure',
    'Disapproved by Committee' : 'committee-failure',
    'Disapproved by Subcommittee' : 'committee-failure',
    'P-C Item Disapproved by Subcommittee with Companion Resolution' : 'committee-failure',
    'Laid Over by Subcommittee' : 'deferral',
    'Laid Over by Committee' : 'deferral',
    'Town Hall Meeting Filed' : None,
    'Filed by Council' : 'filing',
    'Town Hall Meeting Held' : None,
    'Filed by Subcommittee' : 'filing',
    'Filed by Committee with Companion Resolution' : 'filing',
    'Hearing Held by Committee' : None,
    'Approved by Committee' : 'committee-passage',
    'P-C Item Approved by Subcommittee with Modifications and Referred to CPC' : ' committee-passage',
    'Approved with Modifications and Referred to the City Planning Commission pursuant to Rule 11.70(b) of the Rules of the Council and Section 197-(d) of the New York City Charter.' : None,
    'Approved by Subcommittee with Modifications and Referred pursuant to Rule 11.20(b) of the Rules of the Council and Section 197(d) of the New York City Charter' : 'committee-passage',
    'Filed, by Committee' : 'filing',
    'Recved from Mayor by Council' : 'executive-receipt',
    'Signed Into Law by Mayor' : 'executive-signature',
    'Filed by Committee' : 'filing',
    'City Charter Rule Adopted' : None,
    'Withdrawn by Mayor' : None,
    'Laid Over by Council' : 'deferral',
    'Disapproved by Council' : 'failure',
    'Bill Signing Scheduled by Mayor' : None,
    'Sine Die (Filed, End of Session)' : 'failure',
}


