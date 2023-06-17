import datetime
from collections import defaultdict

import lxml
import lxml.etree
import pytz
import requests
from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper
from pupa.utils import _make_pseudo_id

from .base import ElmsAPI


class ChicagoEventsScraper(ElmsAPI, Scraper):
    def _events(self, n_days_ago):

        for event in self._paginate(
            self._endpoint("/meeting"),
            {"filter": f"date gt {n_days_ago.isoformat()}", "sort": "date asc"},
        ):
            detailed_event = self.get(self._endpoint(f'/meeting/{event["meetingId"]}'))
            yield detailed_event.json()

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.now().astimezone() - datetime.timedelta(
            float(window)
        )
        for event in self._events(n_days_ago):

            when = datetime.datetime.fromisoformat(event["date"])
            location = event["location"]
            if not location:
                location = None

            e = Event(
                name=event["body"],
                start_date=when,
                location_name=location,
            )

            e.pupa_id = str(event["meetingId"])

            if video_links := event["videoLink"]:
                for link in video_links.split():
                    e.add_media_link(
                        note="Recording",
                        url=link,
                        type="recording",
                        media_type="text/html",
                    )

            for document in event["files"]:
                e.add_document(
                    note=document["attachmentType"],
                    url=document["path"],
                    media_type="application/pdf",
                )

            for item in event["agenda"]:
                if not (matterTitle := item["matterTitle"]):
                    continue

                agenda_item = e.add_agenda_item(matterTitle)
                if bill_identifier := item["recordNumber"]:
                    if bill_identifier.startswith("S"):
                        canonical_identifier = bill_identifier[1:]
                    else:
                        canonical_identifier = bill_identifier
                    agenda_item.add_bill(canonical_identifier)

                    response = self.get(
                        self._endpoint(
                            f'/meeting/{event["meetingId"]}/matter/{item["matterId"]}/votes'
                        )
                    )
                    votes = response.json()
                    if votes:
                        agenda_item["related_entities"].append(
                            {
                                "vote_event_id": _make_pseudo_id(
                                    motion_text=item["actionText"],
                                    start_date=str(when.date()),
                                    organization__name=participant,
                                    bill__identifier=canonical_identifier,
                                ),
                                "entity_type": "vote_event",
                                "note": "consideration",
                            }
                        )

            participant = event["body"]
            e.add_participant(name=participant, type="organization")

            participants = set()
            for attendance in event["attendance"]:
                for call in attendance["votes"]:
                    if call["vote"] == "Present":
                        participants.add(call["voterName"].strip())

            for person in participants:
                e.add_participant(name=person, type="person")

            e.add_source(self._endpoint(f'/matter/{event["meetingId"]}'), note="api")

            yield e
