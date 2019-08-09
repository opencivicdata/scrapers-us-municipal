from collections import defaultdict
import datetime

import lxml
import lxml.etree
import pytz
import requests
from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper


class PittsburghEventsScraper(LegistarAPIEventScraper, Scraper) :
    BASE_URL = "http://webapi.legistar.com/v1/pittsburgh"
    WEB_URL = "https://pittsburgh.legistar.com/"
    EVENTSPAGE = "https://pittsburgh.legistar.com/Calendar.aspx"
    TIMEZONE = "America/New_York"

    def _event_key(self, event, web_scraper):

        # Overrides method from LegistarAPIEventScraper.
        # The package looks for event["Name"]["label"],
        # however in Pittsburgh"s case there"s no "label".

        response = web_scraper.get(event["iCalendar"]["url"], verify=False)
        event_time = web_scraper.ical(response.text).subcomponents[0]["DTSTART"].dt
        event_time = pytz.timezone(self.TIMEZONE).localize(event_time)

        key = (event["Name"],
               event_time)

        return key

    def clean_agenda_item_title(self, item_title):
      if "PUBLIC COMMENTS" in item_title:
        item_title = "PUBLIC COMMENTS"

      if item_title.endswith(':'):
        item_title = item_title[:-1]

      return item_title

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for api_event, event in self.events(n_days_ago):

            description = api_event["EventComment"]
            when = api_event["start"]
            location = api_event["EventLocation"]

            if location == "Council Chambers":
                location = "Council Chambers, 5th Floor, City-County Building, " \
                            "414 Grant Street, Pittsburgh, PA 15219"

            if not location :
                continue

            status_string = api_event["status"]

            if len(status_string) > 1 and status_string[1] :
                status_text = status_string[1].lower()
                if any(phrase in status_text
                       for phrase in ("rescheduled to",
                                      "postponed to",
                                      "reconvened to",
                                      "rescheduled to",
                                      "meeting recessed",
                                      "recessed meeting",
                                      "postponed to",
                                      "recessed until",
                                      "deferred",
                                      "time change",
                                      "date change",
                                      "recessed meeting - reconvene",
                                      "cancelled",
                                      "new date and time",
                                      "rescheduled indefinitely",
                                      "rescheduled for",)) :
                    status = "cancelled"
                elif status_text in ("rescheduled", "recessed") :
                    status = "cancelled"
                elif status_text in ("meeting reconvened",
                                     "reconvened meeting",
                                     "recessed meeting",
                                     "reconvene meeting",
                                     "rescheduled hearing",
                                     "rescheduled meeting",) :
                    status = api_event["status"]
                elif status_text in ("amended notice of meeting",
                                     "room change",
                                     "amended notice",
                                     "change of location",
                                     "revised - meeting date and time") :
                    status = api_event["status"]
                elif "room" in status_text :
                    location = status_string[1] + ", " + location
                elif status_text in ("wrong meeting date",) :
                    continue
                else :
                    print(status_text)
                    status = api_event["status"]
            else :
                status = api_event["status"]

            if event["Name"] == "Post Agenda":
                event_name = "Agenda Announcement"
            else:
                event_name = event["Name"]

            if description :
                e = Event(name=event_name,
                          start_date=when,
                          description=description,
                          location_name=location,
                          status=status)
            else :
                e = Event(name=event_name,
                          start_date=when,
                          location_name=location,
                          status=status)

            e.pupa_id = str(api_event["EventId"])

            if event["Video"] != "Not\xa0available":
                e.add_media_link(note="Recording",
                                 url = event["Video"]["url"],
                                 type="recording",
                                 media_type = "text/html")

            self.addDocs(e, event, "Agenda")
            self.addDocs(e, event, "Minutes")

            participant = event["Name"]

            if participant == "City Council" or participant == "Post Agenda":
                participant = "Pittsburgh City Council"

            e.add_participant(name=participant,
                              type="organization")

            for item in self.agenda(api_event):
                clean_title = self.clean_agenda_item_title(item["EventItemTitle"])
                agenda_item = e.add_agenda_item(clean_title)
                if item["EventItemMatterFile"]:
                    identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(identifier)

            participants = set()

            for call in self.rollcalls(api_event):
                if call["RollCallValueName"] == "Present":
                    participants.add(call["RollCallPersonName"])

            for person in participants:
                e.add_participant(name=person,
                                  type="person")

            e.add_source(self.BASE_URL + "/events/{EventId}".format(**api_event),
                         note="api")

            try:
                detail_url = event["Meeting Details"]["url"]
            except TypeError:
                e.add_source(self.EVENTSPAGE, note="web")
            else:
                if requests.head(detail_url).status_code == 200:
                    e.add_source(detail_url, note="web")

            yield e
