from legistar.events import LegistarAPIEventScraper
from legistar.events import LegistarEventsScraper

import requests
import lxml.html
from datetime import datetime

from pupa.scrape import Scraper
from pupa.scrape import Event

class LametroEventScraper(LegistarAPIEventScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com'
    EVENTSPAGE = "https://metro.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Los_Angeles"

    def scrape(self):
        web_results = self.scrapeWebCalendar()

        for event in self.events():
            # Create a key for lookups in the web_results dict.
            key = ''

            key = event['EventBodyName'].strip() + ' ' + datetime.strptime(event['EventDate'][:10], '%Y-%m-%d').strftime('%-m/%-d/%Y') + ' ' + event['EventTime']

            try:
                # Look for the event in the web_results dict.
                web_event_dict = web_results[key]
            except:
                web_event_dict = {'Name': {'label': '', 'url': ''}, 'Audio': '', 'Meeting Time': '', 'Recap/Minutes': ''}

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

            meeting_detail_web = self.WEB_URL + '/MeetingDetail.aspx?ID={EventId}&GUID={EventGuid}'.format(**event)
            if requests.head(meeting_detail_web).status_code == 200:
                e.add_source(meeting_detail_web, note='web')
            else:
                e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

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

            # Update 'e' with data from https://metro.legistar.com/Calendar.aspx.
            if web_event_dict['Audio'] != 'Not\xa0available' and web_event_dict['Audio'] != '':
                e.add_media_link(note=web_event_dict['Audio']['label'],
                                 url=web_event_dict['Audio']['url'],
                                 media_type='link')

            if web_event_dict['Recap/Minutes'] != 'Not\xa0available' and web_event_dict['Recap/Minutes'] != '':
                e.add_document(note=web_event_dict['Recap/Minutes']['label'],
                               url=web_event_dict['Recap/Minutes']['url'],
                               media_type="application/pdf")

            print("my dict:", web_event_dict)
            print("LOOK!")
            print(e)

            yield e

    def scrapeWebCalendar(self):
        web_scraper = LegistarEventsScraper(None, None)
        web_scraper.EVENTSPAGE = self.EVENTSPAGE
        web_scraper.BASE_URL = self.WEB_URL

        web_info = {}

        for event, _ in web_scraper.events():
            # Make the dict key (name, date, time) and add it.
            key = event['Name']['label'] + ' ' + event['Meeting Date'] + ' ' + event['Meeting Time']
            web_info[key] = event
            print(web_info)

        return web_info
