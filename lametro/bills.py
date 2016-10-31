from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
import itertools
import pytz
import requests

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
            responsible_org = action['MatterHistoryActionBodyName']

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

    def scrape(self) :
        three_days_ago = datetime.datetime.now() - datetime.timedelta(3)
        for matter in self.matters(three_days_ago) :
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

            legistar_web = self.legislation_detail_url(matter_id)
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

            for attachment in self.attachments(matter_id) :
                if attachment['MatterAttachmentName'] :
                    bill.add_version_link(attachment['MatterAttachmentName'],
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

ACTION_CLASSIFICATION = {'WITHDRAWN' : None,
                         'APPROVED' : None,
                         'RECOMMENDED FOR APPROVAL' : None,
                         'RECEIVED AND FILED' : None,
                         'RECOMMENDED FOR APPROVAL AS AMENDED' : None,
                         'APPROVED AS AMENDED' : None,
                         'APPROVED THE CONSENT CALENDAR' : None,
                         'DISCUSSED' : None,
                         'ADOPTED' : None,
                         'FORWARDED WITHOUT RECOMMENDATION' : None,
                         'CARRIED OVER' : None,
                         'RECEIVED' : None,
                         'REFERRED' : None,
                         'FORWARDED DUE TO ABSENCES AND CONFLICTS' : None}

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

