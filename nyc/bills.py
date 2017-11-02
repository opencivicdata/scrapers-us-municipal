from legistar.bills import LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
from collections import defaultdict
import pytz

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
                    'medical': 'excused'}

    # TO-DO: cq legislative session including 1996
    SESSION_STARTS = (2014, 2010, 2006, 2004, 2002, 1998, 1996)

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
        for action in self.history(matter_id):
            bill_action = {}

            if not action['MatterHistoryActionName']:
                continue

            bill_action['action_description'] = action['MatterHistoryActionName']
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

                if all(action.get(k, None) for k in ['MatterHistoryEventId',
                                                     'MatterHistoryRollCallFlag',
                                                     'MatterHistoryPassedFlag']):

                    bool_result = action['MatterHistoryPassedFlag']
                    result = 'pass' if bool_result else 'fail'

                    votes = (result, self.votes(action['MatterHistoryId']))
                else:
                    votes = (None, [])

                yield bill_action, votes


    def _version_rank(self, version):
        '''
        - If there is only one version, *, it is the max version.
        - If there is an asterisk version and one other version, the other
          version is the max version.
        - If there is an asterisk version and two other non-numeric versions,
          the max version is the first other version in alphabetical order.
        - Otherwise, function as normal.
        '''
        version_map = {'*': -1,
                       'B': 1,
                       'A': 2}

        return int(version_map.get(version, version))


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

#            if sponsor_name == 'Letitia James':
#                sponsor_name = 'Letitia Ms. James'

            sponsorship['name'] = sponsor_name

            yield sponsorship


    def scrape(self):
        for matter in self.matters():

            matter_id = matter['MatterId']

            leg_type = BILL_TYPES[matter['MatterTypeName']]

            intro_date = self.toTime(matter['MatterIntroDate'])
            bill_session = self.sessions(intro_date)

            bill = Bill(identifier=matter['MatterFile'],
                        title=matter['MatterName'],
                        classification=leg_type,
                        legislative_session=bill_session,
                        from_organization={"name": "New York City Council"})

            legistar_web = matter['legistar_url']
            legistar_api = self.BASE_URL + '/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            if matter['MatterTitle']:
                bill.add_title(matter['MatterTitle'])

            # if matter['MATTERSUMMARY']: bill.add_abstract(blah)

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for attachment in self.attachments(matter_id):
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
                    vote_event = VoteEvent(legislative_session=bill.legislative_session,
                                           motion_text=act['description'],
                                           organization=act['organization'],
                                           classification=None,
                                           start_date=act['date'],
                                           result=result,
                                           bill=bill)

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + '/histories')

                    for vote in votes:
                        raw_option = vote['VoteValueName'].lower()
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
                    bill.extras['plain_text'] = text['MatterTextPlain']

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
              'City Agency Report': None}


ACTION_CLASSIFICATION = {
    'Recalled by Council': None,
    'Tour Held by Committee': None,
    'Hearing on P-C Item by Comm': None,
    'Approved by Committee with Modifications and Referred to CPC': 'committee-passage',
    'Approved by Committee with Modifications': 'committee-passage',
    'Approved by Subcommittee with Modifications': 'committee-passage',
    'Hearing Scheduled by Mayor': None,
    'P-C Item Approved by Comm': 'committee-passage',
    'P-C Item Approved by Subcommittee with Companion Resolution': 'committee-passage',
    'Recessed': None,
    'Amendment Proposed by Comm': 'amendment-introduction',
    'P-C Item Laid Over by Comm': 'deferral',
    'Approved by Subcommittee with Modifications and Referred to CPC': 'committee-passage',
    'Re-referred to Committee by Council': 'referral-committee',
    'Approved by Subcommittee': 'committee-passage',
    'Amended by Committee': 'amendment-passage',
    'Referred to Comm by Council': 'referral-committee',
    'Sent to Mayor by Council': None,
    'P-C Item Approved by Committee with Companion Resolution': 'committee-passage',
    'P-C Item Filed by Subcommittee with Companion Resolution': 'filing',
    'Approved by Council': 'passage',
    'Hearing Held by Mayor': None,
    'Approved, by Council': 'passage',
    'Introduced by Council': 'introduction',
    'Approved by Committee with Companion Resolution': 'committee-passage',
    'Rcvd, Ord, Prnt, Fld by Council': 'filing',
    'Disapproved by Committee with Companion Resolution': 'committee-failure',
    'Disapproved by Committee': 'committee-failure',
    'Disapproved by Subcommittee': 'committee-failure',
    'P-C Item Disapproved by Subcommittee with Companion Resolution': 'committee-failure',
    'Laid Over by Subcommittee': 'deferral',
    'Laid Over by Committee': 'deferral',
    'Town Hall Meeting Filed': None,
    'Filed by Council': 'filing',
    'Town Hall Meeting Held': None,
    'Filed by Subcommittee': 'filing',
    'Filed by Committee with Companion Resolution': 'filing',
    'Hearing Held by Committee': None,
    'Approved by Committee': 'committee-passage',
    'P-C Item Approved by Subcommittee with Modifications and Referred to CPC': ' committee-passage',
    'Approved with Modifications and Referred to the City Planning Commission pursuant to Rule 11.70(b) of the Rules of the Council and Section 197-(d) of the New York City Charter.': None,
    'Approved by Subcommittee with Modifications and Referred pursuant to Rule 11.20(b) of the Rules of the Council and Section 197(d) of the New York City Charter': 'committee-passage',
    'Filed, by Committee': 'filing',
    'Recved from Mayor by Council': 'executive-receipt',
    'Signed Into Law by Mayor': 'executive-signature',
    'Filed by Committee': 'filing',
    'City Charter Rule Adopted': None,
    'Withdrawn by Mayor': None,
    'Laid Over by Council': 'deferral',
    'Disapproved by Council': 'failure',
    'Bill Signing Scheduled by Mayor': None,
    'Sine Die (Filed, End of Session)': 'failure',
    'Recommit to Comm by Council': 'referral-committee',
    'P-C Item Approved by Committee with Modifications': 'committee-passage',
    'P-C Item Approved by Subcommittee with Modifications': 'committee-passage',
    'Printed Item Laid on Desk': None,
    'Introduced by Council, IMMEDIATE CONSIDERATION': 'introduction',
    'Deferred': 'deferral',
    'Approved by Committee and Referred to Finance  pursuant to Rule 6.50 of the Council': 'referral-committee',
    'Re-referred  pursuant to Rule 6.50 of the Council': 'referral-committee',
    'Reprnt Amnd Item Laid on Desk': None,
    'Vetoed by Mayor': 'executive-veto',
    'Overridden by Council': 'veto-override-passage',
    'Laid Over Again by Council': 'deferral',
    'Approved by Subcommittee and Referred to Finance pursuant to Rule 6.50 of the Council': 'referral-committee',
    'P-C Item Filed by Committee with Companion Resolution': 'filing',
    'P-C Item Approved by Committee and Referred to Finance pursuant to Rule 6.50 of the Council': 'referral-committee',
    'P-C Item Approved by Subcommittee and Referred to Finance pursuant to Rule 6.50 of the Council': 'referral-committee',
    'Laid Over Again by Committee': 'deferral',
    'P-C Item Approved by Committee with Modifications and Referred to CPC': 'referral-committee',
}

# LAST ERROR
# 16:55:31 INFO scrapelib: HEAD - http://legistar.council.nyc.gov/gateway.aspx?m=l&id=24575
# 16:55:31 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/sponsors
# 16:55:31 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/attachments
# 16:55:31 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/histories
# 16:55:31 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/indexes
# 16:55:32 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/relations
# 16:55:32 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/versions
# 16:55:32 INFO scrapelib: GET - https://webapi.legistar.com/v1/nyc/matters/24575/texts/27933
# 16:55:32 INFO pupa: save bill LU 0005-2002 in 2002 as bill_8b9339ec-c018-11e7-b09a-9801a7a22767.json
# 16:55:32 WARNING pupa: validation of Bill 8b9339ec-c018-11e7-b09a-9801a7a22767 failed: 1 validation errors:
# Value ' committee-passage' for field '<obj>.actions[0].classification[0]' is not in the enumeration: ['filing', 'introduction', 'reading-1', 'reading-2', 'reading-3', 'passage', 'failure', 'withdrawal', 'substitution', 'amendment-introduction', 'amendment-passage', 'amendment-withdrawal', 'amendment-failure', 'amendment-amendment', 'amendment-deferral', 'committee-passage', 'committee-passage-favorable', 'committee-passage-unfavorable', 'committee-failure', 'executive-receipt', 'executive-signature', 'executive-veto', 'executive-veto-line-item', 'veto-override-passage', 'veto-override-failure', 'deferral', 'receipt', 'referral', 'referral-committee']
