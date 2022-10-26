import datetime
from collections import defaultdict

import lxml
import lxml.etree
import pytz
import requests
from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper
from pupa.utils import _make_pseudo_id


class ChicagoEventsScraper(LegistarAPIEventScraper, Scraper):
    BASE_URL = "http://webapi.legistar.com/v1/chicago"
    WEB_URL = "https://chicago.legistar.com/"
    EVENTSPAGE = "https://chicago.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Chicago"

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for api_event, web_event in self.events(n_days_ago):

            when = api_event["start"]
            location = api_event["EventLocation"]

            extracts = self._parse_comment(api_event["EventComment"])
            description, room, status, invalid_event = extracts

            if invalid_event:
                continue

            if room:
                location = room + ", " + location

            if not status:
                status = api_event["status"]

            if description:
                e = Event(
                    name=api_event["EventBodyName"],
                    start_date=when,
                    description=description,
                    location_name=location,
                    status=status,
                )
            else:
                e = Event(
                    name=api_event["EventBodyName"],
                    start_date=when,
                    location_name=location,
                    status=status,
                )

            e.pupa_id = str(api_event["EventId"])

            if web_event["Meeting video"] != "Not\xa0available":
                e.add_media_link(
                    note="Recording",
                    url=web_event["Meeting video"]["url"],
                    type="recording",
                    media_type="text/html",
                )
            self.addDocs(e, web_event, "Published agenda")
            self.addDocs(e, web_event, "Meeting Extra1")
            self.addDocs(e, web_event, "Published summary")
            if "Captions" in web_event:
                self.addDocs(e, web_event, "Captions")

            participant = api_event["EventBodyName"]
            if participant == "City Council":
                participant = "Chicago City Council"
            elif (
                participant
                == "Committee on Energy, Environmental Protection and Public Utilities (inactive)"
            ):
                participant = (
                    "Committee on Energy, Environmental Protection and Public Utilities"
                )

            e.add_participant(name=participant, type="organization")

            for item in self.agenda(api_event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])
                bill_identifier = None
                if item["EventItemMatterFile"]:
                    bill_identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(bill_identifier)
                    if (
                        item["EventItemRollCallFlag"] is not None
                        and item["EventItemPassedFlag"] is not None
                        and item["EventItemActionText"] is not None
                    ):

                        agenda_item["related_entities"].append(
                            {
                                "vote_event_id": _make_pseudo_id(
                                    motion_text=item["EventItemActionText"],
                                    start_date=str(when.date()),
                                    organization__name=participant,
                                    bill__identifier=bill_identifier,
                                ),
                                "entity_type": "vote_event",
                                "note": "consideration",
                            }
                        )

            participants = set()
            for call in self.rollcalls(api_event):
                if call["RollCallValueName"] == "Present":
                    participants.add(call["RollCallPersonName"])

            for person in participants:
                e.add_participant(name=person, type="person")

            e.add_source(
                self.BASE_URL + "/events/{EventId}".format(**api_event), note="api"
            )

            e.add_source(web_event["Meeting Name"]["url"], note="web")

            yield e

    def _parse_comment(self, comment):
        description = None
        room = None
        status = None
        invalid_event = False

        comment = comment if comment else ""
        comment = comment.lower().replace("--em--", "").strip()

        if any(
            phrase in comment
            for phrase in (
                "rescheduled to",
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
                "rescheduled for",
            )
        ):
            status = "cancelled"
        elif comment in ("rescheduled", "recessed"):
            status = "cancelled"
        elif comment in (
            "meeting reconvened",
            "reconvened meeting",
            "recessed meeting",
            "reconvene meeting",
            "rescheduled hearing",
            "rescheduled meeting",
            "amended notice of meeting",
            "room change",
            "amended notice",
            "change of location",
            "revised - meeting date and time",
        ):
            pass
        elif "room" in comment:
            room = comment
        elif comment in ("wrong meeting date",):
            invalid_event = True
        else:
            self.info(comment)
            description = comment

        return description, room, status, invalid_event
