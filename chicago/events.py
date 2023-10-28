import datetime

from pupa.scrape import Event, Scraper
from pupa.utils import _make_pseudo_id

from .base import ElmsAPI
from .rule_forty_five import RULE_45


class ChicagoEventsScraper(ElmsAPI, Scraper):
    def _events(self, n_days_ago):

        for event in self._paginate(
            self._endpoint("/meeting"),
            {"filter": f"date gt {n_days_ago.isoformat()}", "sort": "date asc"},
        ):
            detailed_event = self.get(self._endpoint(f'/meeting/{event["meetingId"]}'))
            yield detailed_event.json()

    def scrape(self, window=7):
        n_days_ago = datetime.datetime.now().astimezone() - datetime.timedelta(
            float(window)
        )
        for event in self._events(n_days_ago):

            when = datetime.datetime.fromisoformat(event["date"])
            location = event["location"]
            if not location:
                location = None

            if (event["comment"] or "").lower() == "wrong meeting date":
                continue

            status = self.infer_status(event, when)

            e = Event(
                name=event["body"],
                start_date=when,
                location_name=location,
                status=status,
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

            participant = event["body"]
            if participant == "City Council":
                participant = "Chicago City Council"
            e.add_participant(name=participant, type="organization")

            participants = set()
            for attendance in event["attendance"]:
                for call in attendance["votes"]:
                    if call["vote"] == "Present":
                        participants.add(call["voterName"].strip())

            rule_45 = RULE_45.get(participant, {}).get(str(when.date()))

            if rule_45:
                if rule_45["source"]:
                    e.add_document(
                        note="Rule 45 Report",
                        url=rule_45["source"],
                        media_type="application/pdf",
                    )
                if not participants and rule_45["attendance"]:
                    participants.update(rule_45["attendance"])

            for person in participants:
                e.add_participant(name=person, type="person")

            for item in event["agenda"]:
                if not (matterTitle := item["matterTitle"]):
                    continue

                agenda_item = e.add_agenda_item(matterTitle)
                if bill_identifier := item["recordNumber"]:
                    bill_identifier = bill_identifier.strip()

                    agenda_item.add_bill(bill_identifier)

                    response = self.get(
                        self._endpoint(
                            f'/meeting/{event["meetingId"]}/matter/{item["matterId"]}/votes'
                        )
                    )
                    votes = response.json()
                    if votes:
                        if item["actionText"]:
                            agenda_item["related_entities"].append(
                                {
                                    "vote_event_id": _make_pseudo_id(
                                        motion_text=item["actionText"],
                                        start_date=str(when.date()),
                                        organization__name=participant,
                                        bill__other_identifiers__identifier=bill_identifier,
                                    ),
                                    "entity_type": "vote_event",
                                    "note": "consideration",
                                }
                            )
                        else:
                            agenda_item["related_entities"].append(
                                {
                                    "vote_event_id": _make_pseudo_id(
                                        start_date=str(when.date()),
                                        organization__name=participant,
                                        bill__other_identifiers__identifier=bill_identifier,
                                    ),
                                    "entity_type": "vote_event",
                                    "note": "consideration",
                                }
                            )

            e.add_source(
                self._endpoint(f'/matter/{event["meetingId"]}'), note="elms_api"
            )
            e.add_source(
                f"https://chicityclerkelms.chicago.gov/Meeting/?meetingId={event['meetingId']}",
                note="web",
            )

            yield e

    def infer_status(self, event, when):
        raw_status = event["status"]

        if raw_status == "Scheduled":
            if when > datetime.datetime.now().astimezone():
                return "confirmed"
            else:
                return "passed"
        elif raw_status in {"Recessed", "Reconvened", "Rescheduled"}:
            return "passed"
        elif raw_status == "Cancelled":
            return "cancelled"
        elif not raw_status and not event["comment"]:
            return "passed"

        comment = event["comment"]
        if comment is None:
            comment = ""
        else:
            comment = comment.lower()

        if any(
            phrase in comment
            for phrase in (
                "rescheduled to",
                "postponed to",
                "rescheduled to",
                "postponed to",
                "deferred",
                "time change",
                "date change",
                "cancelled",
                "new date and time",
                "rescheduled indefinitely",
                "rescheduled for",
            )
        ):
            return "cancelled"
        elif comment in {"rescheduled", "recessed"}:
            return "cancelled"
        else:
            return "passed"
