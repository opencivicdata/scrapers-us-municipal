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
            e = Event(name=event["EventBodyName"],
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


            e.add_participant(name=event["EventBodyName"],
                              type="organization")

            e.add_source('foo')

            meeting_detail_web = self.WEB_URL + '/MeetingDetail.aspx?ID={EventId}&GUID={EventGuid}'.format(**event)
            if requests.head(meeting_detail_web).status_code == 200:
                e.add_source(meeting_detail_web, note='web')
            else:
                e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

            e.add_source(self.BASE_URL + '/events/{EventId}'.format(**event),
                         note='api')

            yield e
