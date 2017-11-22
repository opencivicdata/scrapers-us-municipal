from collections import defaultdict
import datetime
import json
import pytz

from legistar.bills import LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id

from .secrets import TOKEN

class NYCBillScraper(LegistarAPIBillScraper):
    LEGISLATION_URL = 'http://legistar.council.nyc.gov/Legislation.aspx'
    BASE_URL = 'https://webapi.legistar.com/v1/nyc'
    BASE_WEB_URL = 'http://legistar.council.nyc.gov'
    TIMEZONE = 'US/Eastern'

    VOTE_OPTIONS = {'affirmative': 'yes',
                    'negative': 'no',
                    'conflict': 'absent',
                    'maternity': 'excused',
                    'paternity': 'excused',
                    'bereavement': 'excused',
                    'non-voting': 'not voting',
                    'jury duty': 'excused',
                    'absent': 'absent',
                    'medical': 'excused',
                    'recused': 'abstain'}

    # The Council session is usually a 4-year term. However, every 20 years
    # the Council has an extra election due to redistricting, so instead of a
    # 4-year term, there are two consecutive 2-year terms. The last time this
    # happened was in 2002 and 2004, with the extra election in 2003. The
    # next time this will happen is in 2022 and 2024, with the extra election
    # in 2023, unless the statute is changed between now (Nov. 2017) and then.

    SESSION_STARTS = (2014, 2010, 2006, 2004, 2002, 1998, 1994)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add required URL parameter
        self.params = {'Token': TOKEN}


    def sessions(self, action_date):
        for session in self.SESSION_STARTS:
            if action_date >= datetime.datetime(session, 1, 1,
                                               tzinfo=pytz.timezone(self.TIMEZONE)):
                return str(session)


    def actions(self, matter_id):
        vote_fields = ('MatterHistoryEventId',
                       'MatterHistoryRollCallFlag',
                       'MatterHistoryPassedFlag')

        for action in self.history(matter_id):
            bill_action = {}

            if not action['MatterHistoryActionName']:
                continue

            if action['MatterHistoryId'] == 138469:  # Skip duplicate council approval event
                continue

            bill_action['action_description'] = action['MatterHistoryActionName'].strip()
            bill_action['action_date'] = action['MatterHistoryActionDate']

            responsible_org = action['MatterHistoryActionBodyName']

            if responsible_org == 'City Council':
                responsible_org = 'New York City Council'

            elif responsible_org == 'Administration':
                responsible_org = 'Mayor'

            elif responsible_org == 'Town Hall Meeting':
                continue

            bill_action['responsible_org'] = responsible_org

            if all(bill_action.values()):
                action_date = self.toTime(bill_action['action_date']).date()
                bill_action['action_date'] = action_date

                classification = ACTION_CLASSIFICATION[bill_action['action_description']]
                bill_action['classification'] = classification

                if all(action[k] is not None for k in vote_fields):
                    bool_result = action['MatterHistoryPassedFlag']
                    result = 'pass' if bool_result else 'fail'

                    votes = (result, self.votes(action['MatterHistoryId']))
                else:
                    votes = (None, [])

                yield bill_action, votes


    def _version_rank(self, version):
        '''
        This method overrides `LegistarAPIBillScraper._version_rank`.

        Traditionally, matter versions are numbered in ascending order, e.g.,
        the highest version number denotes the most recent version. By contrast,
        most New York City Council matters have one version labeled with an
        asterisk (*).

        Instead of numbers, NY City Council orders versions by letter, where
        the last letter alphabetically indicates the most recent version.

        A very small number of bills introduced prior to 2000 have a "0"
        version. These are artifacts of reconciling poor formatting and should
        be reported to Council admin for removal.

        `version_map` contains possible versions and their recency ranking,
        where a higher ranking means a more recent version.

        Params

          :version (str) - '*', 'A', 'B', 'C', 'D'

        Returns

          integer value indicating position of given version relative to other
          possible versions, such that the max() of an array of outputs will
          return the most recent version
        '''
        version_map = {'*': 1,
                       'A': 2,
                       'B': 3,
                       'C': 4,
                       'D': 5}

        return version_map[version]


    def sponsorships(self, matter_id):
        for i, sponsor in enumerate(self.sponsors(matter_id)):
            sponsorship = {'entity_type': 'person'}

            if i == 0:
                sponsorship['primary'] = True
                sponsorship['classification'] = 'Primary'
            else:
                sponsorship['primary'] = False
                sponsorship['classification'] = 'Regular'

            sponsor_name = sponsor['MatterSponsorName']

            if sponsor_name.startswith(('(in conjunction with',
                                        '(by request of')):
                continue

            sponsorship['name'] = sponsor_name

            yield sponsorship


    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for matter in self.matters(n_days_ago):
            matter_id = matter['MatterId']

            date = matter['MatterIntroDate']
            title = matter['MatterName']
            identifier = matter['MatterFile']

            if not all((date, title, identifier)):
                continue

            leg_type = BILL_TYPES[matter['MatterTypeName']]

            bill_session = self.sessions(self.toTime(date))

            bill = Bill(identifier=identifier,
                        title=title,
                        classification=leg_type,
                        legislative_session=bill_session,
                        from_organization={"name": "New York City Council"})

            legistar_web = matter['legistar_url']
            legistar_api = self.BASE_URL + '/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            if matter['MatterTitle']:
                bill.add_title(matter['MatterTitle'])

            if matter['MatterEXText5']:
                bill.add_abstract(matter['MatterEXText5'], note='')

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for attachment in self.attachments(matter_id):

                if attachment['MatterAttachmentId'] == 103315:  # Duplicate
                    continue

                if attachment['MatterAttachmentName']:
                    bill.add_document_link(attachment['MatterAttachmentName'],
                                           attachment['MatterAttachmentHyperlink'],
                                           media_type='application/pdf')

            for action, vote in self.actions(matter_id):
                act = bill.add_action(action['action_description'],
                                      action['action_date'],
                                      organization={'name': action['responsible_org']},
                                      classification=action['classification'])

                result, votes = vote

                if result:
                    organization = json.loads(act['organization_id'].lstrip('~'))
                    vote_event = VoteEvent(legislative_session=bill.legislative_session,
                                           motion_text=act['description'],
                                           organization=organization,
                                           classification=None,
                                           start_date=act['date'],
                                           result=result,
                                           bill=bill)

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + '/histories')

                    for vote in votes:
                        raw_option = vote['VoteValueName'].lower()

                        if raw_option == 'suspended':
                            continue

                        clean_option = self.VOTE_OPTIONS.get(raw_option, raw_option)
                        vote_event.vote(clean_option, vote['VotePersonName'].strip())

                    yield vote_event

            for topic in self.topics(matter_id) :
                bill.add_subject(topic['MatterIndexName'].strip())

            for relation in self.relations(matter_id):
                try:
                    related_bill = self.endpoint('/matters/{0}', relation['MatterRelationMatterId'])
                except scrapelib.HTTPError:
                    continue
                else:
                    date = related_bill['MatterIntroDate']
                    related_bill_session = self.session(self.toTime(date))
                    identifier = related_bill['MatterFile']
                    bill.add_related_bill(identifier=identifier,
                                          legislative_session=related_bill_session,
                                          relation_type='companion')

            text = self.text(matter_id)

            if text:
                if text['MatterTextPlain']:
                    bill.extras['plain_text'] = text['MatterTextPlain'].replace(u'\u0000', '')

                if text['MatterTextRtf']:
                    bill.extras['rtf_text'] = text['MatterTextRtf'].replace(u'\u0000', '')

            yield bill


BILL_TYPES = {'Introduction': 'bill',
              'Resolution'  : 'resolution',
              'Land Use Application': None,
              'Oversight': None,
              'Land Use Call-Up': None,
              'Communication': None,
              "Mayor's Message": None,
              'Local Laws 2015': 'bill',
              'Commissioner of Deeds': None,
              'Town Hall Meeting': None,
              'Tour': None,
              'Petition': 'petition',
              'SLR': None,
              'City Agency Report': None,
              'N/A': None}


ACTION_CLASSIFICATION = {
    'Adopted by the Committee': 'committee-passage',
    'Amended by Committee': 'amendment-passage',
    'Amended by Council': 'amendment-passage',
    'Amendment Defeated by Council': 'amendment-failure',
    'Amendment Proposed by Comm': 'amendment-introduction',
    'Amendment Proposed by Council': 'amendment-introduction',
    'Amici Curiae Brief Filed': None,
    'App/Disapp In Part By Committee': None,
    'App/Disapp In Part by Council': None,
    'Appointed to Committee': None,
    'Appointed to Position': None,
    'Approved and Referred to the Department of City Planning': 'referral',
    'Approved by Committee': 'committee-passage',
    'Approved by Committee and Referred to Finance  pursuant to Rule 6.50 of the Council': 'committee-passage',
    'Approved by Committee with Companion Resolution': 'committee-passage',
    'Approved by Committee with Modifications': 'committee-passage',
    'Approved by Committee with Modifications and Referred to CPC': 'committee-passage',
    'Approved by Council': 'passage',
    'Approved by Subcommittee': 'committee-passage',
    'Approved by Subcommittee and Referred to Finance pursuant to Rule 6.50 of the Council': 'committee-passage',
    'Approved by Subcommittee with Modifications': 'committee-passage',
    'Approved by Subcommittee with Modifications and Referred pursuant to Rule 11.20(b) of the Rules of the Council and Section 197(d) of the New York City Charter': 'committee-passage',
    'Approved by Subcommittee with Modifications and Referred to CPC': 'committee-passage',
    'Approved with Modifications and Referred to the City Planning Commission pursuant to Rule 11.70(b) of the Rules of the Council and Section 197-(d) of the New York City Charter.': 'referral',
    'Approved, by Council': 'passage',
    'Approved/Ordered in Part by Council': 'passage',
    'Bill Signing Scheduled by Mayor': None,
    'Called up by Chairperson': None,
    'Charter Approved by Members': None,
    'City Charter Rule Adopted': None,
    'City Charter Rule,File,City Planning Commission': None,
    'Contract Approved by City': None,
    'Defeated by Committee': 'committee-failure',
    'Defeated by Council': 'failure',
    'Deferred': 'deferral',
    'Demonstrated': None,
    'Disapproved by Committee': 'committee-failure',
    'Disapproved by Committee with Companion Resolution': 'committee-failure',
    'Disapproved by Council': 'failure',
    'Disapproved by Mayor': 'executive-veto',
    'Disapproved by Subcommittee': 'committee-failure',
    'Discharged from Committee': None,
    'Elected to Leadership Position': None,
    'Elected to Office': None,
    'Executive Director Appointed': None,
    'Filed by Committee': 'filing',
    'Filed by Committee with Companion Resolution': 'filing',
    'Filed by Council': 'filing',
    'Filed by Subcommittee': 'filing',
    'Filed, by Committee': 'filing',
    'Hearing Held by Committee': None,
    'Hearing Held by Mayor': None,
    'Hearing Scheduled by Committee': None,
    'Hearing Scheduled by Mayor': None,
    'Hearing on P-C Item by Comm': None,
    'Introduced by Council': 'filing',
    'Introduced by Council, IMMEDIATE CONSIDERATION': 'filing',
    'Judicial Case Argued': None,
    'Judicial Case Decided': None,
    'Laid Over Again by Committee': 'deferral',
    'Laid Over Again by Council': 'deferral',
    'Laid Over Again by Subcommittee': 'deferral',
    'Laid Over by Committee': 'deferral',
    'Laid Over by Council': 'deferral',
    'Laid Over by Subcommittee': 'deferral',
    'Motion': None,
    'Organization Founded': None,
    'Other Action Taken': None,
    'Overridden by Council': 'veto-override-passage',
    'P-C Item Approved by Comm': 'committee-passage',
    'P-C Item Approved by Committee and Referred to Finance pursuant to Rule 6.50 of the Council': 'committee-passage',
    'P-C Item Approved by Committee with Companion Resolution': 'committee-passage',
    'P-C Item Approved by Committee with Modifications': 'committee-passage',
    'P-C Item Approved by Committee with Modifications and Referred to CPC': 'committee-passage',
    'P-C Item Approved by Subcommittee and Referred to Finance pursuant to Rule 6.50 of the Council': 'committee-passage',
    'P-C Item Approved by Subcommittee with Companion Resolution': 'committee-passage',
    'P-C Item Approved by Subcommittee with Modifications': 'committee-passage',
    'P-C Item Approved by Subcommittee with Modifications and Referred to CPC': 'committee-passage',
    'P-C Item Disapproved by Committee with Companion Resolution': 'committee-passage',
    'P-C Item Disapproved by Subcommittee with Companion Resolution': 'committee-passage',
    'P-C Item Discharged from Committee': None,
    'P-C Item Filed by Comm': 'filing',
    'P-C Item Filed by Committee with Companion Resolution': 'filing',
    'P-C Item Filed by Subcommittee with Companion Resolution': 'filing',
    'P-C Item Laid Over by Comm': 'deferral',
    'Prec Item Disapproved by Committee': 'committee-failure',
    'Press Conference Filed': None,
    'Press Conference Held': None,
    'Printed Item Laid on Desk': None,
    'Proclamation Granted': None,
    'Proclamation Requested': None,
    'Rcvd, Ord, Prnt, Fld by Council': 'filing',
    'Rcvd,Ord,Prnt,Fld by Comm': 'filing',
    'Re-referred  pursuant to Rule 6.50 of the Council': 'referral-committee',
    'Re-referred to Committee by Council': 'referral-committee',
    'Recalled by Council': None,
    'Received from Mayor': None,
    'Recessed': None,
    'Recommit to Comm by Council': None,
    'Recommit to Council by Mayor': None,
    'Recved from Mayor by Council': 'executive-receipt',
    'Referred to City Agency': 'referral',
    'Referred to Comm by Council': 'referral-committee',
    'Referred to Committee by Committee': 'referral-committee',
    'Referred to Gen Ord Calendar': 'referral',
    'Referred to Landmarks Preservation Commission': 'referral',
    'Reprnt Amnd Item Laid on Desk': None,
    'Sent for Introduction': 'introduction',
    'Sent to Council Member for Approval': None,
    'Sent to Mayor by Council': None,
    'Signed Into Law by Mayor': 'executive-signature',
    'Sine Die (Filed, End of Session)': 'failure',
    'Special Event Filed': None,
    'Special Event Held': None,
    'Sworn In': None,
    'Testified at Comm Hearing': None,
    'Tour Held by Committee': None,
    'Town Hall Meeting Filed': None,
    'Town Hall Meeting Held': None,
    'Unknown': None,
    'Vetoed by Mayor': 'executive-veto',
    'Withdrawn by Mayor': 'withdrawal',
    'Withdrawn by Public Advocate': 'withdrawal',
}
