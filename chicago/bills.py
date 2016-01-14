from legistar.bills import LegistarBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
import itertools
import pytz
import requests

class ChicagoBillScraper(LegistarBillScraper):
    BASE_URL = 'https://chicago.legistar.com/'
    LEGISLATION_URL = 'https://chicago.legistar.com/Legislation.aspx'
    TIMEZONE = "US/Central"
    date_format = '%Y-%m-%dT%H:%M:%S'
    #requests_per_minute = 360

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

            #http://webapi.legistar.com/v1/chicago/matters?$filter=MatterLastModifiedUtc+ gt+datetime'2016-01-01'


    def matters(self, since_date) :
        since_date_str = datetime.datetime.strftime(since_date, '%Y-%m-%d')

        base_url = 'http://webapi.legistar.com/v1/chicago/matters'
        params = {'$filter' : "MatterLastModifiedUtc gt datetime'2016-01-10'"}
        # the oldest thing on ocd is 2015-09-24
        

        response = self.get(base_url, params=params)

        yield from response.json()
        
        page_num = 1
        while len(response.json()) == 1000 :
            params['$skip'] = page_num * 1000
            response = self.get(base_url, params=params)
            yield from response.json()

            page_num += 1

    def history(self, matter_id) :
        history_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/histories'
        history_url = history_url.format(matter_id=matter_id)
        response = self.get(history_url)
        actions = response.json()
        return sorted(actions, key = lambda action : action['MatterHistoryActionId'])

    def sponsors(self, matter_id) :
        sponsor_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/sponsors'
        sponsor_url = sponsor_url.format(matter_id=matter_id)
        response = self.get(sponsor_url)
        return response.json()

    def votes(self, history_id) :
        votes_url = 'http://webapi.legistar.com/v1/chicago/eventitems/{history_id}/votes'
        votes_url = votes_url.format(history_id=history_id)
        response = self.get(votes_url)
        return response.json()

    def topics(self, matter_id) :
        topics_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/indexes'
        topics_url = topics_url.format(matter_id=matter_id)
        response = self.get(topics_url)
        return response.json()

    def attachments(self, matter_id) :
        attachments_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/attachments'
        attachments_url = attachments_url.format(matter_id=matter_id)
        response = self.get(attachments_url)
        return response.json()

    def code_sections(self, matter_id) :
        codesections_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/codesections'
        codesections_url = codesections_url.format(matter_id=matter_id)
        response = self.get(codesections_url)
        return response.json()

    def texts(self, matter_id) :
        versions_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/versions'
        text_url = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}/texts/{text_id}'

        versions_url = versions_url.format(matter_id = matter_id)
        for version in self.get(versions_url).json() :
            yield self.get(text_url.format(matter_id = matter_id, 
                                           text_id = version["Key"])).json()

        
        
    def scrape(self) :
        for matter in self.matters(datetime.date(2016, 1, 12)) :
            bill_type = BILL_TYPES[matter['MatterTypeName']]
            bill_session = self.session(self.toTime(matter['MatterIntroDate']))

            bill = Bill(identifier=matter['MatterFile'],
                        legislative_session=bill_session,
                        title=matter['MatterTitle'],
                        classification=bill_type,
                        from_organization={"name":"Chicago City Council"})

            gateway_url = 'https://chicago.legistar.com/gateway.aspx?m=l&id=/matter.aspx?key={id}'
            legistar_web = self.BASE_URL + requests.head(gateway_url.format(id = matter['MatterId'])).headers['Location']

            legistar_api = 'http://webapi.legistar.com/v1/chicago/matters/{matter_id}'.format(matter_id = matter['MatterId'])

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            old_action_id = None
            for action in self.history(matter['MatterId']) :
                action_id = action['MatterHistoryActionId']
                if action_id == old_action_id :
                    print(previous_action)
                    print(action)
                old_action_id = action_id
                previous_action = action

                action_description = action['MatterHistoryActionName'].strip()
                try :
                    action_date =  self.toTime(action['MatterHistoryActionDate']).date().isoformat()
                except (AttributeError, ValueError) : # https://chicago.legistar.com/LegislationDetail.aspx?ID=1424866&GUID=CEC53337-B991-4268-AE8A-D4D174F8D492
                    continue

                if action_description :
                    responsible_org = action['MatterHistoryActionBodyName']
                    # sometimes the responsible org is missing
                    # https://chicago.legistar.com/LegislationDetail.aspx?ID=2483496&GUID=EC5C27CE-906E-431B-AE09-5C9ECFA8E863
                    if not responsible_org :
                        continue
                    if responsible_org == 'City Council' :
                        responsible_org = 'Chicago City Council'

                    act = bill.add_action(action_description,
                                          action_date,
                                          organization={'name': responsible_org},
                                          classification=ACTION_CLASSIFICATION[action_description])

                    if action_description == 'Referred' : 
                        body_name = matter['MatterBodyName']
                        if body_name != 'City Council' :
                            act.add_related_entity(body_name,
                                                   'organization',
                                                   entity_id = _make_pseudo_id(name=body_name))


                    action_text = action['MatterHistoryActionText']
                    if action_text is None :
                        action_text = ''

                    if action['MatterHistoryEventId'] is not None and 'voice vote' not in action_text.lower() :
                        result = action['MatterHistoryPassedFlag']
                        if result is None :
                            break
                        if result == 1 :
                            result = 'pass'
                        elif result == 0 :
                            result = 'fail'

                        action_vote = VoteEvent(legislative_session=bill.legislative_session, 
                                               motion_text=action_description,
                                               organization={'name': responsible_org},
                                               classification=None,
                                               start_date=action_date,
                                               result=result,
                                               bill=bill)

                        action_vote.add_source(legistar_web)
                        action_vote.add_source(legistar_api + '/histories')

                        for vote in self.votes(action['MatterHistoryId']) : 
                            action_vote.vote(self.VOTE_OPTIONS.get(vote['VoteValueName'].lower(), vote['VoteValueName'].lower()), 
                                             vote['VotePersonName'])

                        yield action_vote


            
            for i, sponsor in enumerate(self.sponsors(matter['MatterId'])) :
                if i == 0 :
                    primary = True
                    sponsorship_type = "Primary"
                else :
                    primary = False
                    sponsorship_type = "Regular"

                sponsor_name = sponsor['MatterSponsorName'].strip()

                entity_type = 'person'
                if sponsor_name.startswith(('City Clerk',)) : 
                    sponsor_name = 'Office of the City Clerk'
                    entity_type = 'organization'
                if not sponsor_name.startswith(('Misc. Transmittal',
                                                'No Sponsor',
                                                'Dept./Agency')) :
                    bill.add_sponsorship(sponsor_name, 
                                         sponsorship_type,
                                         entity_type,
                                         primary)

            for topic in self.topics(matter['MatterId']) :
                bill.add_subject(topic['MatterIndexName'].strip())

            for attachment in self.attachments(matter['MatterId']) :
                bill.add_version_link(attachment['MatterAttachmentName'],
                                      attachment['MatterAttachmentHyperlink'],
                                      media_type="application/pdf")

            bill.extras = {'local_classification' : matter['MatterTypeName']}

            for i, text in enumerate(self.texts(matter['MatterId'])) :
                if text['MatterTextPlain'] :
                    bill.extras['plain_text'] = text['MatterTextPlain']

                if text['MatterTextRtf'] :
                    bill.extras['rtf_text'] = text['MatterTextRtf']

                assert i == 0

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

