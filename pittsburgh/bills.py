from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id
import datetime
import itertools
import pytz
import requests


class PittsburghBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/pittsburgh'
    BASE_WEB_URL = 'https://pittsburgh.legistar.com'
    TIMEZONE = "US/Eastern"

    VOTE_OPTIONS = {'aye' : 'yes',
                    'no' : 'no',
                    'abstain' : 'abstain',
                    'absent': 'absent',
                    'out of room': 'absent'}

    def session(self, action_date) :
        return str(action_date.year)

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
        actions = self.history(matter_id)

        for action in actions :
            action_date = action['MatterHistoryActionDate']
            action_description = action['MatterHistoryActionName']
            responsible_org = action['MatterHistoryActionBodyName']

            action_date =  self.toTime(action_date).date()

            responsible_person = None
            if responsible_org == 'City Council' :
                responsible_org = 'Pittsburgh City Council'
            elif responsible_org == 'Office of the Mayor':
                responsible_org = 'City of Pittsburgh'
                if action_date < datetime.date(2014, 1, 3):
                    responsible_person = 'William Peduto'
                else:
                    responsible_person = 'Luke Ravensthal'

            if action_description in ACTION:
                ocd_classification = ACTION[action_description]['ocd']
            else:
                ocd_classification = None

            bill_action = {'description' : action_description,
                           'date' : action_date,
                           'organization' : {'name' : responsible_org},
                           'classification': ocd_classification,
                           # 'classification' : ACTION[action_description]['ocd'],
                           'responsible person' : responsible_person}
            if bill_action != old_action:
                old_action = bill_action
            else:
                continue

            if (action['MatterHistoryEventId'] is not None
                and action['MatterHistoryRollCallFlag'] is not None
                and action['MatterHistoryPassedFlag'] is not None) :

                bool_result = action['MatterHistoryPassedFlag']
                result = 'pass' if bool_result else 'fail'

                votes = (result, self.votes(action['MatterHistoryId']))
            else :
                votes = (None, [])

            yield bill_action, votes

    def scrape(self, window=3) :
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for matter in self.matters(n_days_ago) :
            matter_id = matter['MatterId']

            date = matter['MatterIntroDate']
            title = matter['MatterTitle']
            identifier = matter['MatterFile']

            # If a bill has a duplicate action item that's causing the entire scrape
            # to fail, add it to the `problem_bills` array to skip it.
            # For the time being...nothing to skip!

            problem_bills = []

            if identifier in problem_bills:
                continue

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
                        from_organization={"name":"Pittsburgh City Council"})

            legistar_web = matter['legistar_url']

            legistar_api = 'http://webapi.legistar.com/v1/pittsburgh/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for action, vote in self.actions(matter_id) :
                responsible_person = action.pop('responsible person')
                act = bill.add_action(**action)

                if responsible_person:
                     act.add_related_entity(responsible_person,
                                            'person',
                                            entity_id = _make_pseudo_id(name=responsible_person))

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

ACTION = {'Committee Report':
              {'ocd' : None, 'order' : 0},
          'Interview Held':
              {'ocd': None, 'order': 0},
          'Meeting Held':
              {'ocd': None, 'order': 0},
          'On File':
              {'ocd': 'filing', 'order': 0},
          'Read, Received And Filed':
              {'ocd': 'filing', 'order': 0},
          'Read and referred':
              {'ocd': 'filing', 'order': 0},
          'Recorded':
              {'ocd': 'receipt', 'order': 0},
          'Reported from Standing Committee':
              {'ocd': None, 'order': 0},
          'Scheduled':
              {'ocd': None, 'order': 0},
          'Not introduced':
              {'ocd': 'failure', 'order': 0},
          'Post Agenda Held':
              {'ocd': None, 'order': 0},
          'Held for Post Agenda':
              {'ocd': None, 'order': 0},
          'Withdrawn':
              {'ocd': 'withdrawal', 'order': 1},
          'Held in Standing Committee':
              {'ocd': 'committee-failure', 'order': 1},
          'Held in Council':
              {'ocd': 'committee-failure', 'order': 1},
          'In Standing Committee':
              {'ocd': 'referral-committee', 'order': 1},
          'Read and referred':
              {'ocd': 'referral', 'order': 1},
          'Defeated':
              {'ocd': 'failure', 'order': 2},
          'Died due to expiration of legislative council session':
              {'ocd': 'failure', 'order': 2},
          'Passed Finally':
              {'ocd': 'passage', 'order': 2},
          'Postponed':
              {'ocd': 'deferral', 'order': 2},
          'Re-Scheduled':
              {'ocd': 'deferral', 'order': 2},
          'Not Introduced':
              {'ocd': 'deferral', 'order': 2},
          'Adopted':
              {'ocd': 'passage', 'order': 2},
          'Approved':
              {'ocd': 'passage', 'order': 2},
          'TABLED':
              {'ocd': 'deferral', 'order': 2},
          'Vetoed':
              {'ocd': 'failure', 'order': 2},
          'Cancelled':
              {'ocd': 'withdrawal', 'order': 2},
          'Mayor\'s Office for Signature':
              {'ocd': 'executive-receipt', 'order': 3},
          'Veto was Overridden':
              {'ocd': 'veto-override-passage', 'order': 3},
          'Veto was Sustained':
              {'ocd': 'veto-override-failure', 'order': 3},
          'Signed by the Mayor':
              {'ocd': 'executive-signature', 'order': 4}
        }



BILL_TYPES = {'Ordinance' : 'ordinance',
              'Resolution' : 'resolution',
              'Order' : 'order',
              'Executive Order' : 'bill',
              'Claim' : 'claim',
              'Petition' : 'petition',
              'Proclamation' : 'proclamation',
              'Will of Council': 'proclamation',
              'Oath of Office' : None,
              'Communication' : None,
              'Appointment-Informing' : 'appointment',
              'Appointment-Requiring Vote' : 'appointment',
              'Post Agenda' : None,
              'Invoices' : None,
              'Remarks' : None,
              'Sister City Inventory' : None,
              'Small Games of Chance' : None,
              'Ceritificate of Election' : None,
              'Transcripts - PH' : None,
              'Transcripts - Regular Meeting' : None,
              'Transcripts - SCM' : None,
              'Veto Message' : None,
              'Public Hearing' : None,
              'Report' : None}
