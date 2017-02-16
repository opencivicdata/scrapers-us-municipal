from legistar.events import LegistarAPIEventScraper

import requests

from pupa.scrape import Scraper
from pupa.scrape import Event

class LametroEventScraper(LegistarAPIEventScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com'
    TIMEZONE = "America/Los_Angeles"

    def scrape(self):
        for event in self.events():
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

            e.add_source('foo')

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


            yield e
