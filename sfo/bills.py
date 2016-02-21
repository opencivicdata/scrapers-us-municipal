from legistar.bills import LegistarBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
from collections import defaultdict
import pytz

class SFBillScraper(LegistarBillScraper):
    LEGISLATION_URL = 'https://sfgov.legistar.com/Legislation.aspx'
    BASE_URL = 'https://sfgov.legistar.com/'
    TIMEZONE = "US/Pacific"

    VOTE_OPTIONS = {'aye' : 'yes',
                    'no' : 'no',
                    'absent' : 'absent'}

    CURRENT_YEAR = 2016

    SESSION_STARTS = range(CURRENT_YEAR, 1997, -1)

    def sessions(self, action_date) :
        for session in self.SESSION_STARTS :
            if action_date >= datetime.datetime(session, 1, 1,
                                               tzinfo=pytz.timezone(self.TIMEZONE)) :
                return str(session)

    def scrape(self):
        for leg_summary in self.legislation(created_after=datetime.datetime(2016, 1, 1)) :
            leg_type = BILL_TYPES[leg_summary['Type']]

            bill = Bill(identifier=leg_summary['File\xa0#'],
                        title=leg_summary['Title'],
                        legislative_session=None,
                        classification=leg_type,
                        from_organization={"name": self.jurisdiction.council_name})
            bill.add_source(leg_summary['url'], note='web')

            leg_details = self.legDetails(leg_summary['url'])
            history = self.history(leg_summary['url'])

            bill.add_title(leg_details['Name'],
                           note='created by administrative staff')

            if 'Summary' in leg_details :
                bill.add_abstract(leg_details['Summary'], note='')

            if leg_details['Enactment #'] :
                bill.add_identifier(leg_details['Enactment #'],
                                    note='enactment number')

            for sponsorship in self._sponsors(leg_details.get('Sponsors', [])) :
                sponsor, sponsorship_type, primary = sponsorship
                bill.add_sponsorship(sponsor, sponsorship_type,
                                     'person', primary)

            for attachment in leg_details.get('Attachments', []) :
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
                if responsible_org in ['Board of Supervisors', 'Clerk of the Board', 'President'] :
                    responsible_org = self.jurisdiction.council_name

                if action_class :
                    act = bill.add_action(action_description,
                                          action_date,
                                          organization={'name': responsible_org},
                                          classification=action_class)

                    if 'url' in action['Action\xa0Details'] :
                        action_detail_url = action['Action\xa0Details']['url']
                        if action_class == 'committee-referral' :
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

            if type(sponsor) == dict :
                sponsor_name = sponsor['label']
            else :
                sponsor_name = sponsor

            if sponsor_name.startswith(('(in conjunction with',
                                        '(by request of')) :
                continue

            yield sponsor_name, sponsorship_type, primary

BILL_TYPES = {'Charter Amendment': None,
              'Communication': None,
              'Discussion': None,
              'Hearing': None,
              'Motion': None,
              'Ordinance': 'ordinance',
              'Report': None,
              'Resolution'   : 'resolution'}


ACTION_CLASSIFICATION = {
    'ADOPTED': 'passage',
    'ADOPTED AS AMENDED': 'passage',
    'ADOPTED AS AMENDED AND DIVIDED': 'passage',
    'ADOPTED AS DIVIDED': 'passage',
    'ADOPTED OVER THE MAYOR\'S VETO': 'veto-override-passage',
    'AMENDED': None,
    'AMENDED, AN AMENDMENT OF THE WHOLE BEARING NEW TITLE': None,
    'AMENDED, AN AMENDMENT OF THE WHOLE BEARING SAME TITLE': None,
    'APPEAL FILED': None,
    'APPROVED': None,
    'APPROVED AND FILED': None,
    'APPROVED AS AMENDED': None,
    'APPROVED AS DIVIDED': None,
    'APPROVED IN COMMITTEE': 'committee-passage',
    'APPROVED IN COMMITTEE AS AMENDED': 'committee-passage',
    'APPROVED OVER THE MAYOR\'S VETO': None,
    'ASSIGNED': 'committee-referral',
    'ASSIGNED UNDER 30 DAY RULE': 'committee-referral',
    'ASSIGNED UNDER 30 DAY RULE PENDING APPROVAL AS TO FORM': None,
    'AWARDED': None,
    'CALLED FROM COMMITTEE': None,
    'CLERICAL CORRECTION': None,
    'COMBINED': None,
    'COMBINED WITH EXISTING FILE': None,
    'CONTINUED': None,
    'CONTINUED AS AMENDED': None,
    'CONTINUED AS AMENDED ON FINAL PASSAGE': None,
    'CONTINUED AS AMENDED ON FIRST READING': None,
    'CONTINUED AS DIVIDED': None,
    'CONTINUED ON FINAL PASSAGE': None,
    'CONTINUED ON FIRST READING': None,
    'CONTINUED ON FIRST READING AS AMENDED': None,
    'CONTINUED ON OVERTURN OF VETO': None,
    'CONTINUED OPEN': None,
    'CONTINUED TO CALL OF THE CHAIR': None,
    'CONTINUED TO CALL OF THE CHAIR AS AMENDED': None,
    'DISAPPROVED': None,
    'DISCUSSED AND FILED': None,
    'DIVIDED': None,
    'DUPLICATED': None,
    'DUPLICATED AND AMENDED': None,
    'DUPLICATED AS AMENDED': None,
    'ERRATA PREPARED AND SIGNED BY CLERK OF THE BOARD': None,
    'FILED': None,
    'FILED PURSUANT TO RULE 3.40': None,
    'FILED PURSUANT TO RULE 3.41': None,
    'FILED PURSUANT TO RULE 5.36': None,
    'FILED PURSUANT TO RULE 5.37': None,
    'FILED PURSUANT TO RULE 5.38': None,
    'FILED PURSUANT TO RULE 5.39': None,
    'FILED PURSUANT TO RULE 5.40': None,
    'FINALLY PASSED': 'committee-passage',
    'FINALLY PASSED AS AMENDED': 'committee-passage',
    'FINALLY PASSED AS DIVIDED': 'committee-passage',
    'HEARD AND FILED': None,
    'HEARD AND RELEASED': None,
    'HEARD AND TABLED': None,
    'HEARD AT PUBLIC HEARING': None,
    'HEARD IN CLOSED SESSION': None,
    'HEARD IN COMMITTEE': None,
    'HEARD IN COMMITTEE AND FILED': None,
    'MEETING CANCELLED': None,
    'MEETING RECESSED': None,
    'MOTION': None,
    'NO ACTION TAKEN.  CALLED FROM COMMITTEE.': None,
    'NO ACTION TAKEN.  LACK OF QUORUM.': None,
    'NO ACTION TAKEN.  PENDING IN COMMITTEE.': None,
    'NOT RETURNED WITHIN TIME LIMIT': None,
    'NOTICED': None,
    'ORDERED SUBMITTED': None,
    'OVERTURN MAYORAL VETO': None,
    'PASS THE CONSENT AGENDA': None,
    'PASSED AS EMERGENCY MEASURE': None,
    'PASSED ON FIRST READING': 'reading-1',
    'PASSED ON FIRST READING AS AMENDED': None,
    'PASSED ON FIRST READING AS DIVIDED': None,
    'PASSED, ON FIRST READING': 'reading-1',
    'PREPARED IN COMMITTEE AS A MOTION': None,
    'PREPARED IN COMMITTEE AS A RESOLUTION': None,
    'PREPARED IN COMMITTEE AS A RESOLUTION APPROVING THE REQUEST': None,
    'PREPARED IN COMMITTEE AS A RESOLUTION APPROVING THE REQUEST WITH CONDITIONS': None,
    'PREPARED IN COMMITTEE AS A RESOLUTION DISAPPROVING THE REQUEST': None,
    'PREPARED IN COMMITTEE AS A RESOLUTION OPPOSING THE REQUEST': None,
    'PREPARED IN COMMITTEE AS AN ORDINANCE': None,
    'PREVIOUS VOTE RESCINDED': None,
    'RE-REFERRED': 'committee-referral',
    'RE-REFERRED AS AMENDED': None,
    'RE-REFERRED WITH PENDING AMENDMENT': None,
    'REACTIVATED PURSUANT TO CITY ATTORNEY INSTRUCTIONS': None,
    'REACTIVATED PURSUANT TO RULE 3.42': None,
    'REACTIVATED PURSUANT TO RULE 4.31': None,
    'REACTIVATED PURSUANT TO RULE 5.23': None,
    'REACTIVATED PURSUANT TO RULE 5.24': None,
    'REACTIVATED PURSUANT TO RULE 5.25': None,
    'REACTIVATED PURSUANT TO RULE 5.31': None,
    'RECEIVED AND ASSIGNED': None,
    'RECEIVED FROM DEPARTMENT': None,
    'RECOMMENDED': 'committee-passage',
    'RECOMMENDED "DO NOT PASS"': 'committee-passage-unfavorable',
    'RECOMMENDED "DO NOT SUBMIT"': 'committee-passage-unfavorable',
    'RECOMMENDED "DO SUBMIT"': 'committee-passage-favorable',
    'RECOMMENDED AS AMENDED': 'committee-passage',
    'RECOMMENDED AS AMENDED "DO NOT PASS"': 'committee-passage-unfavorable',
    'RECOMMENDED AS AMENDED AND DIVIDED': 'committee-passage',
    'RECOMMENDED AS AMENDED AS A COMMITTEE REPORT': None,
    'RECOMMENDED AS AMENDED..': 'committee-passage',
    'RECOMMENDED AS COMMITTEE REPORT': None,
    'RECOMMENDED AS DIVIDED': None,
    'RECOMMENDED AS DIVIDED..': None,
    'RECOMMENDED..': 'committee-passage',
    'RECORDED': None,
    'REFERRED': 'committee-referral',
    'REFERRED AS AMENDED': None,
    'REFERRED FOR ADOPTION WITHOUT COMMITTEE REFERENCE AGENDA AT THE NEXT BOARD MEETING': None,
    'REFERRED TO BOARD SITTING AS A COMMITTEE OF THE WHOLE': None,
    'REFERRED TO DEPARTMENT': None,
    'REFERRED WITHOUT RECOMMENDATION': None,
    'REFERRED WITHOUT RECOMMENDATION AS AMENDED': None,
    'REFERRED WITHOUT RECOMMENDATION AS AMENDED AS A COMMITTEE REPORT': None,
    'REFERRED WITHOUT RECOMMENDATION AS COMMITTEE REPORT': None,
    'REFERRED WITHOUT RECOMMENDATION AS COMMITTEE REPORT AS AMENDED': None,
    'REFERRED WITHOUT RECOMMENDATION AS DIVIDED AND AMENDED AS A COMMITTEE REPORT': None,
    'REMAIN ACTIVE': None,
    'REPEALED': None,
    'RESPONSE RECEIVED': None,
    'RETURNED UNSIGNED': None,
    'RETURNED UNSIGNED AND WAIVED': None,
    'SCHEDULED FOR PUBLIC HEARING': None,
    'SEVERED FROM COMMITTEE CONSENT AGENDA': None,
    'SEVERED FROM CONSENT AGENDA': None,
    'SEVERED FROM FOR ADOPTION WITHOUT COMMITTEE REFERENCE AGENDA': None,
    'SUBSTITUTED': None,
    'SUBSTITUTED AND ASSIGNED': 'committee-referral',
    'SUBSTITUTED AND ASSIGNED UNDER 30 DAY RULE': 'committee-referral',
    'SUBSTITUTED, AND ASSIGNED': 'committee-referral',
    'TABLED': 'failure',
    'TABLED BY OPERATION OF LAW': 'failure',
    'TO BE SCHEDULED FOR PUBLIC HEARING': None,
    'TRANSFERRED': 'committee-referral',
    'VETOED': 'executive-veto',
    'VETOED - LINE ITEM': None,
    'WITHDRAWN AND FILED': None,
}
