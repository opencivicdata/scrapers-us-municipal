from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
import itertools
import pytz
import requests

class ChicagoBillScraper(LegistarAPIBillScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/chicago'
    BASE_WEB_URL = 'https://chicago.legistar.com'
    TIMEZONE = "US/Central"

    VOTE_OPTIONS = {'yea' : 'yes',
                    'rising vote' : 'yes',
                    'nay' : 'no',
                    'recused' : 'excused'}

    def session(self, action_date) :
        localize = pytz.timezone(self.TIMEZONE).localize
        # 2011 Kill Bill https://chicago.legistar.com/LegislationDetail.aspx?ID=907351&GUID=6118274B-A598-4584-AA5B-ABDFA5F79506
        if action_date <  localize(datetime.datetime(2011, 5, 4)) :
            return "2007"
        # 2015 Kill Bill https://chicago.legistar.com/LegislationDetail.aspx?ID=2321351&GUID=FBA81B7C-8A33-4D6F-92A7-242B537069B3
        elif action_date < localize(datetime.datetime(2015, 5, 6)) :
            return "2011"
        else :
            return "2015"

    def sponsorships(self, matter_id) :
        for i, sponsor in enumerate(self.sponsors(matter_id)) :
            sponsorship = {}
            if i == 0 :
                sponsorship['primary'] = True
                sponsorship['classification'] = "Primary"
            else :
                sponsorship['primary'] = False
                sponsorship['classification'] = "Regular"

            sponsor_name = sponsor['MatterSponsorName'].strip()
            
            if sponsor_name.startswith(('City Clerk',)) : 
                sponsorship['name'] = 'Office of the City Clerk'
                sponsorship['entity_type'] = 'organization'
            else :
                sponsorship['name'] = sponsor_name
                sponsorship['entity_type'] = 'person'

            if not sponsor_name.startswith(('Misc. Transmittal',
                                            'No Sponsor',
                                            'Dept./Agency')) :
                yield sponsorship

    def actions(self, matter_id) :
        old_action = None
        for action in self.history(matter_id) :
            action_date = action['MatterHistoryActionDate']
            action_description = action['MatterHistoryActionName'].strip()
            responsible_org = action['MatterHistoryActionBodyName']

            if all((action_date, action_description, responsible_org)) :
                action_date =  self.toTime(action_date).date()

                if responsible_org == 'City Council' :
                    responsible_org = 'Chicago City Council'

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

            if not all((date, title)) :
                continue

            bill_session = self.session(self.toTime(date))
            bill_type = BILL_TYPES[matter['MatterTypeName']]

            bill = Bill(identifier=matter['MatterFile'],
                        legislative_session=bill_session,
                        title=title,
                        classification=bill_type,
                        from_organization={"name":"Chicago City Council"})

            legistar_web = self.legislation_detail_url(matter_id)
            legistar_api = 'http://webapi.legistar.com/v1/chicago/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            for action, vote in self.actions(matter_id) :
                act = bill.add_action(**action)

                if action['description'] == 'Referred' :
                    body_name = matter['MatterBodyName']
                    if body_name != 'City Council' :
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
                         'Amended in City Council' : 'amendment-passage',
                         'Placed on File' : 'filing',
                         'Withdrawn' : 'withdrawal',
                         'Signed by Mayor' : 'executive-signature',
                         'Vetoed' : 'executive-veto',
                         'Appointment' : 'appointment',
                         'Introduced (Agreed Calendar)' : 'introduction',
                         'Direct Introduction' : 'introduction',
                         'Remove Co-Sponsor(s)' : None,
                         'Add Co-Sponsor(s)' : None,
                         'Tabled' : 'deferred',
                         'Rules Suspended - Immediate Consideration' : None,
                         'Committee Discharged' : None,
                         'Held in Committee' : 'committee-failure',
                         'Recommended for Re-Referral' : None,
                         'Published in Special Pamphlet' : None,
                         'Adopted as Substitute' : None,
                         'Deferred and Published' : None,
                         'Approved as Amended' : 'passage',
}


BILL_TYPES = {'Ordinance' : 'ordinance',
              'Resolution' : 'resolution',
              'Order' : 'order',
              'Claim' : 'claim',
              'Oath of Office' : None,
              'Communication' : None,
              'Appointment' : 'appointment',
              'Report' : None}

