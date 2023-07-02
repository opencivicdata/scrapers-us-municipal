from legistar.bills import LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id
import datetime
import pytz


class AnnarborBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/a2gov'
    BASE_WEB_URL = 'https://a2gov.legistar.com'
    TIMEZONE = "America/Detroit"

    VOTE_OPTIONS = {'non-voting': 'not voting',
                    'yea': 'yes',
                    'nay': 'no',
                    'recused': 'excused',
                    }

    def session(self, action_date):
        localize = pytz.timezone(self.TIMEZONE).localize
        if action_date < localize(datetime.datetime(2007, 11, 15)):
            return "before"
        elif action_date < localize(datetime.datetime(2008, 11, 15)):
            return "2007"
        elif action_date < localize(datetime.datetime(2009, 11, 15)):
            return "2008"
        elif action_date < localize(datetime.datetime(2010, 11, 15)):
            return "2009"
        elif action_date < localize(datetime.datetime(2011, 11, 15)):
            return "2010"
        elif action_date < localize(datetime.datetime(2012, 11, 15)):
            return "2011"
        elif action_date < localize(datetime.datetime(2013, 11, 15)):
            return "2012"
        elif action_date < localize(datetime.datetime(2014, 11, 15)):
            return "2013"
        elif action_date < localize(datetime.datetime(2015, 11, 15)):
            return "2014"
        elif action_date < localize(datetime.datetime(2016, 11, 15)):
            return "2015"
        elif action_date < localize(datetime.datetime(2017, 11, 15)):
            return "2016"
        elif action_date < localize(datetime.datetime(2018, 11, 15)):
            return "2017"
        elif action_date < localize(datetime.datetime(2020, 11, 15)):
            return "2018"
        elif action_date < localize(datetime.datetime(2022, 11, 15)):
            return "2020"
        import pdb
        pdb.set_trace()

    def sponsorships(self, matter_id):
        for i, sponsor in enumerate(self.sponsors(matter_id)):
            sponsorship = {}
            if i == 0:
                sponsorship['primary'] = True
                sponsorship['classification'] = "Primary"
            else:
                sponsorship['primary'] = False
                sponsorship['classification'] = "Regular"

            sponsor_name = sponsor['MatterSponsorName'].strip()

            sponsorship['name'] = sponsor_name
            sponsorship['entity_type'] = 'person'

            yield sponsorship

    def actions(self, matter_id):
        old_action = None
        actions = self.history(matter_id)

        for action in actions:
            action_description = action['MatterHistoryActionName']
            action_date = action['MatterHistoryActionDate']
            action_text = action['MatterHistoryActionText']
            responsible_org = action['MatterHistoryActionBodyName']
            if responsible_org == 'City Council':
                responsible_org = 'Ann Arbor City Council'

            action_date = self.toTime(action_date).date()

            responsible_person = None

            bill_action = {'description': action_description,
                           'date': action_date,
                           'organization': {'name': responsible_org},
                           'classification': None,
                           'responsible person': responsible_person,
                           }
            if action_text:
                bill_action['extras'] = {'text': action_text}

            if bill_action != old_action:
                old_action = bill_action
            else:
                continue

            vote_possible = (action['MatterHistoryEventId'] is not None
                             and action['MatterHistoryRollCallFlag'] is not None
                             and action['MatterHistoryPassedFlag'] is not None)

            if vote_possible:

                bool_result = action['MatterHistoryPassedFlag']
                result = 'pass' if bool_result else 'fail'

                votes = (result, self.votes(action['MatterHistoryId']))
            else:
                votes = (None, [])

            yield bill_action, votes, action['MatterHistoryId']

    def scrape(self, window=3):
        window = float(window)
        if window:
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(window)
        else:
            n_days_ago = None

        for matter in self.matters(n_days_ago):
            matter_id = matter['MatterId']

            date = matter['MatterIntroDate']
            title = matter['MatterTitle']
            identifier = matter['MatterFile']

            # If a bill has a duplicate action item that's causing the entire scrape
            # to fail, add it to the `problem_bills` array to skip it.
            # For the time being...nothing to skip!

            problem_bills = set()

            if identifier in problem_bills:
                continue

            if not all((date, title, identifier)):
                continue

            if date == '5012-05-07T00:00:00':
                continue
            bill_session = self.session(self.toTime(date))
            # bill_type = BILL_TYPES[matter['MatterTypeName']]

            if identifier.startswith('S'):
                alternate_identifiers = [identifier]
                identifier = identifier[1:]
            else:
                alternate_identifiers = []

            bill = Bill(identifier=identifier,
                        legislative_session=bill_session,
                        title=title,
                        # classification=bill_type,
                        from_organization={"name": "Ann Arbor City Council"})

            legistar_web = matter['legistar_url']

            legistar_api = 'http://webapi.legistar.com/v1/a2gov/matters/{0}'.format(matter_id)

            bill.add_source(legistar_web, note='web')
            bill.add_source(legistar_api, note='api')

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for action, vote, history_id in self.actions(matter_id):
                responsible_person = action.pop('responsible person')
                act = bill.add_action(**action)

                if responsible_person:
                    act.add_related_entity(responsible_person,
                                           'person',
                                           entity_id=_make_pseudo_id(name=responsible_person))

                if action['description'] == 'Referred':
                    body_name = matter['MatterBodyName']
                    if body_name != 'City Council':
                        act.add_related_entity(body_name,
                                               'organization',
                                               entity_id=_make_pseudo_id(name=body_name))

                result, votes = vote
                if result:
                    vote_event = VoteEvent(legislative_session=bill.legislative_session,
                                           motion_text=action['description'],
                                           organization=action['organization'],
                                           classification=None,
                                           start_date=action['date'],
                                           result=result,
                                           bill=bill)

                    # this is abusing the identifier, which is
                    # supposed to be something from upstream
                    # like rollcall # 132
                    vote_event.identifier = str(history_id)

                    if 'extras' in action:
                        vote_event.extras['text'] = action['extras']['text']

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + '/histories')

                    for vote in votes:
                        vote_value = vote['VoteValueName']
                        if vote_value is None:
                            continue
                        raw_option = vote_value.lower()
                        clean_option = self.VOTE_OPTIONS.get(raw_option,
                                                             raw_option)
                        vote_event.vote(clean_option,
                                        vote['VotePersonName'].strip())

                    yield vote_event

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for topic in self.topics(matter_id):
                bill.add_subject(topic['MatterIndexName'].strip())

            for attachment in self.attachments(matter_id):
                if attachment['MatterAttachmentName']:
                    bill.add_version_link(attachment['MatterAttachmentName'],
                                          attachment['MatterAttachmentHyperlink'],
                                          media_type="application/pdf")

            bill.extras = {'local_classification': matter['MatterTypeName']}

            text = self.text(matter_id)

            if text:
                if text['MatterTextPlain']:
                    bill.extras['plain_text'] = text['MatterTextPlain']

            yield bill
