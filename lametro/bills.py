import datetime
import itertools
import pytz
import requests
import scrapelib

from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id

from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper

class LametroBillScraper(LegistarAPIBillScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    BASE_WEB_URL = 'https://metro.legistar.com'
    TIMEZONE = "America/Los_Angeles"

    VOTE_OPTIONS = {'aye' : 'yes',
                    'nay' : 'no',
                    'recused' : 'abstain',
                    'present' : 'abstain'}

    def session(self, action_date) :
        localize = pytz.timezone(self.TIMEZONE).localize
        if action_date <  localize(datetime.datetime(2015, 7, 1)) :
            return "2014"
        if action_date <  localize(datetime.datetime(2016, 7, 1)) :
            return "2015"
        if action_date <  localize(datetime.datetime(2017, 7, 1)) :
            return "2016"
        if action_date <  localize(datetime.datetime(2018, 7, 1)) :
            return "2017"                 
        else:
            raise ValueError("Invalid action date: {}".format(action_date))

    def sponsorships(self, matter_id) :
        for i, sponsor in enumerate(self.sponsors(matter_id)) :
            sponsorship = {}
            if i == 0 :
                sponsorship['primary'] = True
                sponsorship['classification'] = "Primary"
            else :
                sponsorship['primary'] = False
                sponsorship['classification'] = "Regular"

            sponsorship['name'] = sponsor['MatterSponsorName'].strip()
            sponsorship['entity_type'] = 'organization'
            
            yield sponsorship

    def actions(self, matter_id) :
        old_action = None
        for action in self.history(matter_id) :
            action_date = action['MatterHistoryActionDate']
            action_description = action['MatterHistoryActionName'].strip()
            responsible_org = action['MatterHistoryActionBodyName'].strip()
            if responsible_org == "Board of Directors - Regular Board Meeting":
                responsible_org = "Board of Directors"

            if all((action_date, action_description, responsible_org)) :
                action_date =  self.toTime(action_date).date()

                bill_action = {'description' : action_description,
                               'date' : action_date,
                               'organization' : {'name' : responsible_org},
                               'classification' : ACTION_CLASSIFICATION[action_description]}
                if bill_action != old_action:
                    old_action = bill_action
                else:
                    continue

                if (action['MatterHistoryEventId'] is not None
                    and action['MatterHistoryRollCallFlag'] is not None
                    and action['MatterHistoryPassedFlag'] is not None) :
                    
                    # Do we want to capture vote events for voice votes?
                    # Right now we are not? 
                    bool_result = action['MatterHistoryPassedFlag']
                    result = 'pass' if bool_result else 'fail'

                    votes = (result, self.votes(action['MatterHistoryId'])) 
                else :
                    votes = (None, [])

                yield bill_action, votes

    def scrape(self, window=28) :
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for matter in self.matters(n_days_ago) :
            matter_id = matter['MatterId']

            date = matter['MatterIntroDate']
            title = matter['MatterTitle']
            identifier = matter['MatterFile']

            if not all((date, title, identifier)) :
                continue

            bill_session = self.session(self.toTime(date))
            bill_type = BILL_TYPES[matter['MatterTypeName']]

            if identifier.startswith('S'):
                alternate_identifiers = [identifier]
                identifier = identifier[1:]
            else:
                alternate_identifiers = []

            bill = Bill(identifier=identifier,
                        legislative_session=bill_session,
                        title=title,
                        classification=bill_type,
                        from_organization={"name":"Board of Directors"})
            
            legistar_web = matter['legistar_url']
            
            legistar_api = self.BASE_URL + '/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for action, vote in self.actions(matter_id) :
                act = bill.add_action(**action)

                if action['description'] == 'Referred' :
                    body_name = matter['MatterBodyName']
                    act.add_related_entity(body_name,
                                           'organization',
                                           entity_id = _make_pseudo_id(name=body_name))

                result, votes = vote
                if result :
                    vote_event = VoteEvent(legislative_session=bill.legislative_session, 
                                           motion_text=action['description'],
                                           organization=action['organization'],
                                           classification=None,
                                           start_date=action['date'],
                                           result=result,
                                           bill=bill)

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + '/histories')

                    for vote in votes :
                        raw_option = vote['VoteValueName'].lower()
                        clean_option = self.VOTE_OPTIONS.get(raw_option,
                                                             raw_option)
                        vote_event.vote(clean_option, 
                                        vote['VotePersonName'].strip())

                    yield vote_event


            for sponsorship in self.sponsorships(matter_id) :
                bill.add_sponsorship(**sponsorship)

            for topic in self.topics(matter_id) :
                bill.add_subject(topic['MatterIndexName'].strip())

            for relation in self.relations(matter_id):
                try:
                    # Get data (i.e., json) for the related bill. 
                    # Then, we can find the 'MatterFile' (i.e., identifier) and the 'MatterIntroDate' (i.e., to determine its legislative session).
                    # Sometimes, the related bill does not yet exist: in this case, throw an error, and continue.
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
                    # Currently, the relation type for bills can be one of a few possibilites: https://github.com/opencivicdata/python-opencivicdata/blob/master/opencivicdata/common.py#L104
                    # Metro simply understands these as related files, suggesting that they receive a relation of 'companion'.

            bill.add_version_link('Board Report',
                                  'https://metro.legistar.com/ViewReport.ashx?M=R&N=TextL5&GID=557&ID={}&GUID=LATEST&Title=Board+Report'.format(matter_id),
                                   media_type="application/pdf")

            for attachment in self.attachments(matter_id) :
                if attachment['MatterAttachmentName'] :
                    bill.add_document_link(attachment['MatterAttachmentName'],
                                           attachment['MatterAttachmentHyperlink'],
                                           media_type="application/pdf")

            bill.extras = {'local_classification' : matter['MatterTypeName']}

            text = self.text(matter_id)

            if text :
                if text['MatterTextPlain'] :
                    bill.extras['plain_text'] = text['MatterTextPlain']

                if text['MatterTextRtf'] :
                    bill.extras['rtf_text'] = text['MatterTextRtf'].replace(u'\u0000', '')

            yield bill

ACTION_CLASSIFICATION = {'WITHDRAWN' : 'withdrawal',
                         'APPROVED' : 'passage',
                         'RECOMMENDED FOR APPROVAL' : 'committee-passage-favorable',
                         'RECEIVED AND FILED' : 'filing',
                         'RECOMMENDED FOR APPROVAL AS AMENDED' : 'committee-passage-favorable',
                         'APPROVED AS AMENDED' : 'passage',
                         'APPROVED THE CONSENT CALENDAR' : 'passage',
                         'DISCUSSED' : None,
                         'ADOPTED' : 'passage',
                         'ADOPTED AS AMENDED': 'passage',
                         'FORWARDED WITHOUT RECOMMENDATION' : 'committee-passage',
                         'CARRIED OVER' : 'deferral',
                         'RECEIVED' : 'receipt',
                         'REFERRED' : 'referral-committee',
                         'FORWARDED DUE TO ABSENCES AND CONFLICTS' : 'committee-passage'}

BILL_TYPES = {'Contract' : None,
              'Budget' : None,
              'Program' : None,
              'Motion / Motion Response' : None,
              'Policy' : None,
              'Informational Report' : None,
              'Fare / Tariff / Service Change' : None,
              'Agreement' : None,
              'Oral Report / Presentation' : None,
              'Resolution' : None,
              'Project' : None,
              'Formula Allocation / Local Return' : None,
              'Federal Legislation / State Legislation (Position)': None,
              'Plan': None,
              'Minutes': None,
              'Ordinance': None,
              'Appointment': None,
              'Public Hearing': None,
              'Application': None}

