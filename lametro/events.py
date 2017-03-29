from legistar.events import LegistarAPIEventScraper
from legistar.events import LegistarEventsScraper

import requests

from pupa.scrape import Scraper
from pupa.scrape import Event

class LametroEventScraper(LegistarAPIEventScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com'
    EVENTSPAGE = "https://metro.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Los_Angeles"
    # date_format = '%Y-%m-%dT%H:%M:%S'

    def scrape(self):
        web_results = self.scrapeWebCalendar()

        for event in self.events():
            # Create a key for lookups in the web_results dict.
            key = (event['EventBodyName'].strip(), self.toTime(event['EventDate']).date(), event['EventTime'])

            web_event_dict = web_results.get(key, {'Meeting Details': 'Meeting\xa0details', 'Audio': 'Not\xa0available', 'Recap/Minutes': 'Not\xa0available'})

            body_name = event["EventBodyName"]
            if 'Board of Directors -' in body_name:
                body_name, event_name = [part.strip()
                                         for part
                                         in body_name.split('-')]
            else:
                event_name = body_name

            e = Event(event_name,
                      start_time=event["start"],
                      timezone=self.TIMEZONE,
                      description='',
                      location_name=event["EventLocation"],
                      status=event["status"])

            for item in self.agenda(event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])
                if item["EventItemMatterFile"]:
                    identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(identifier)


            e.add_participant(name=body_name,
                              type="organization")

            e.add_source(self.BASE_URL + '/events/{EventId}'.format(**event),
                         note='api')

            if event['EventAgendaFile']:
                e.add_document(note= 'Agenda',
                               url = event['EventAgendaFile'],
                               media_type="application/pdf")

            if event['EventMinutesFile']:
                e.add_document(note= 'Minutes',
                               url = event['EventMinutesFile'],
                               media_type="application/pdf")

            # Update 'e' with data from https://metro.legistar.com/Calendar.aspx, if that data exists.
            if web_event_dict['Audio'] != 'Not\xa0available':
                e.add_media_link(note=web_event_dict['Audio']['label'],
                                 url=web_event_dict['Audio']['url'],
                                 media_type='text/html')

            if web_event_dict['Recap/Minutes'] != 'Not\xa0available':
                e.add_document(note=web_event_dict['Recap/Minutes']['label'],
                               url=web_event_dict['Recap/Minutes']['url'],
                               media_type="application/pdf")

            if web_event_dict['Meeting Details'] != 'Meeting\xa0details':
                if requests.head(web_event_dict['Meeting Details']['url']).status_code == 200:
                    e.add_source(web_event_dict['Meeting Details']['url'], note='web')
                else:
                    e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

            yield e

    def scrapeWebCalendar(self):
        web_scraper = LegistarEventsScraper(None, None)
        web_scraper.EVENTSPAGE = self.EVENTSPAGE
        web_scraper.BASE_URL = self.WEB_URL
        web_scraper.TIMEZONE = "America/Los_Angeles"
        web_scraper.date_format = '%m/%d/%Y'
        web_info = {}

        for event, _ in web_scraper.events():
            # Make the dict key (name, date-as-datetime, time), and add it.
            key = (event['Name']['label'], web_scraper.toTime(event['Meeting Date']).date(), event['Meeting Time'])
            web_info[key] = event

        return web_info