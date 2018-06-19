from collections import defaultdict
import datetime

import lxml
import lxml.etree
import pytz
import requests
from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper

class ChicagoEventsScraper(LegistarAPIEventScraper, Scraper) :
    BASE_URL = 'http://webapi.legistar.com/v1/chicago'
    WEB_URL = "https://chicago.legistar.com/"
    EVENTSPAGE = "https://chicago.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Chicago"

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for api_event, event in self.events(n_days_ago):

            description = None

            when = api_event['start']
            location_string = event[u'Meeting Location']

            location_list = location_string.split('--', 2)
            location = ', '.join(location_list[0:2])
            if not location :
                continue

            status_string = location_list[-1].split('Chicago, Illinois')
            if len(status_string) > 1 and status_string[1] :
                status_text = status_string[1].lower()
                if any(phrase in status_text
                       for phrase in ('rescheduled to',
                                      'postponed to',
                                      'reconvened to',
                                      'rescheduled to',
                                      'meeting recessed',
                                      'recessed meeting',
                                      'postponed to',
                                      'recessed until',
                                      'deferred',
                                      'time change',
                                      'date change',
                                      'recessed meeting - reconvene',
                                      'cancelled',
                                      'new date and time',
                                      'rescheduled indefinitely',
                                      'rescheduled for',)) :
                    status = 'cancelled'
                elif status_text in ('rescheduled', 'recessed') :
                    status = 'cancelled'
                elif status_text in ('meeting reconvened',
                                     'reconvened meeting',
                                     'recessed meeting',
                                     'reconvene meeting',
                                     'rescheduled hearing',
                                     'rescheduled meeting',) :
                    status = api_event['status']
                elif status_text in ('amended notice of meeting',
                                     'room change',
                                     'amended notice',
                                     'change of location',
                                     'revised - meeting date and time') :
                    status = api_event['status']
                elif 'room' in status_text :
                    location = status_string[1] + ', ' + location
                elif status_text in ('wrong meeting date',) :
                    continue
                else :
                    print(status_text)
                    description = status_string[1].replace('--em--', '').strip()
                    status = api_event['status']
            else :
                status = api_event['status']


            if description :
                e = Event(name=event["Name"]["label"],
                          start_date=when,
                          description=description,
                          location_name=location,
                          status=status)
            else :
                e = Event(name=event["Name"]["label"],
                          start_date=when,
                          location_name=location,
                          status=status)

            e.pupa_id = str(api_event['EventId'])

            if event['Video'] != 'Not\xa0available' :
                e.add_media_link(note='Recording',
                                 url = event['Video']['url'],
                                 type="recording",
                                 media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Notice')
            self.addDocs(e, event, 'Captions')
            self.addDocs(e, event, 'Summary')

            participant = event["Name"]["label"]
            if participant == 'City Council' :
                participant = 'Chicago City Council'
            elif participant == 'Committee on Energy, Environmental Protection and Public Utilities (inactive)' :
                participant = 'Committee on Energy, Environmental Protection and Public Utilities'

            e.add_participant(name=participant,
                              type="organization")

            for item in self.agenda(api_event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])
                if item["EventItemMatterFile"]:
                    identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(identifier)

            participants = set()
            for call in self.rollcalls(api_event):
                if call['RollCallValueName'] == 'Present':
                    participants.add(call['RollCallPersonName'])

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
