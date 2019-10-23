import datetime
import re

import pytz
import requests
from legistar.events import LegistarAPIEventScraperZip
from pupa.scrape import Event, Scraper

from .secrets import TOKEN

class NYCEventsScraper(LegistarAPIEventScraperZip, Scraper):
    BASE_URL = 'https://webapi.legistar.com/v1/nyc'
    WEB_URL = "https://legistar.council.nyc.gov/"
    EVENTSPAGE = "https://legistar.council.nyc.gov/Calendar.aspx/"
    TIMEZONE = "America/New_York"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This adds default param values to all requests made by
        # this session
        self.params = {'Token': TOKEN}

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))

        for api_event, event in self.events(n_days_ago):

            when = api_event['start']
            location = self._clean_location(api_event['EventLocation'])

            description = event['Meeting\xa0Topic']

            if any(each in description
                   for each
                   in ('Multiple meeting items',
                       'AGENDA TO BE ANNOUNCED')) :
                description = None

            if description:
                e = Event(name=api_event["EventBodyName"],
                          start_date=when,
                          description=description,
                          location_name=location,
                          status=api_event['status'])
            else:
                e = Event(name=api_event["EventBodyName"],
                          start_date=when,
                          location_name=location,
                          status=api_event['status'])

            e.pupa_id = str(api_event['EventId'])

            if event['Multimedia'] != 'Not\xa0available' :
                e.add_media_link(note='Recording',
                                 url = event['Multimedia']['url'],
                                 type="recording",
                                 media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Minutes')

            location_string = event[u'Meeting Location']
            location_notes, other_orgs = self._parse_location(location_string)

            if location_notes:
                e.extras = {'location note': ' '.join(location_notes)}

            if e.name == 'City Council Stated Meeting' :
                participating_orgs = ['New York City Council']
            elif 'committee' in e.name.lower() :
                participating_orgs = [e.name]
            else :
                participating_orgs = []

            if other_orgs :
                other_orgs = re.sub('Jointl*y with the ', '', other_orgs)
                participating_orgs += re.split(' and the |, the ', other_orgs)

            for org in participating_orgs :
                e.add_committee(name=org)

            for item in self.agenda(api_event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])
                if item["EventItemMatterFile"]:
                    identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(identifier)

            participants = set()

            for call in self.rollcalls(api_event):
                if call['RollCallValueName'] == 'Present':
                    participants.add(call['RollCallPersonName'].strip())

            for person in participants:
                e.add_participant(name=person,
                                  type="person")

            e.add_source(self.BASE_URL + '/events/{EventId}'.format(**api_event),
                         note='api')

            try:
                detail_url = event['Meeting Details']['url']
            except TypeError:
                e.add_source(self.EVENTSPAGE, note='web')
            else:
                if requests.head(detail_url).status_code == 200:
                    e.add_source(detail_url, note='web')

            yield e

    def _clean_location(self, location_string):
        return re.sub(r'\s{2,}', ' ', location_string)

    def _parse_location(self, location_string):
        other_orgs = None
        location_notes = []

        if '--em--' in location_string:
            location_string, note = location_string.split('--em--')[:2]
            for each in note.split(' - ') :
                if each.startswith('Join') :
                    other_orgs = each
                else :
                    location_notes.append(each)

        return location_notes, other_orgs

    def _event_key(self, event, web_scraper):
        response = web_scraper.get(event['iCalendar']['url'], verify=False)
        event_time = web_scraper.ical(response.text).subcomponents[0]['DTSTART'].dt
        event_time = pytz.timezone(self.TIMEZONE).localize(event_time)

        if event['Name'] == 'City Council Stated Meeting':
            name = 'City Council'
        else:
            name = event['Name']

        key = (name, event_time)

        return key

    def _event_status(self, event):
        if all(event[k] == 'Deferred' for k in ('EventMinutesStatusName',
                                                'EventAgendaStatusName')):
            status = 'cancelled'

        elif datetime.datetime.utcnow().replace(tzinfo = pytz.utc) > event['start']:
            status = 'passed'

        else:
            status = 'confirmed'

        return status

    def _not_in_web_interface(self, event):
        return event['EventAgendaStatusId'] == 1  # agenda not yet final
