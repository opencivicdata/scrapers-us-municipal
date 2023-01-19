import datetime
import itertools
import pytz
import requests
import scrapelib

from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id

from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper

from .events import LametroEventScraper

try:
    from .secrets import TOKEN
except ModuleNotFoundError:
    import os

    TOKEN = os.environ["TOKEN"]


class LametroBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = "https://webapi.legistar.com/v1/metro"
    BASE_WEB_URL = "https://metro.legistar.com"
    TIMEZONE = "America/Los_Angeles"

    VOTE_OPTIONS = {
        "aye": "yes",
        "nay": "no",
        "recused": "abstain",
        "present": "abstain",
        "conflict": "abstain",
        None: "abstain",
    }

    START_DATE_PRIVATE_SCRAPE = "2016-07-01"

    def __init__(self, *args, **kwargs):
        """
        Metro scrapes private (or restricted) bills.

        The following properties enable scraping private bills:

        :params - URL params that include the secret Metro API Token

        :scrape_restricted - a boolean used in `python-legistar-scraper`: it
        indicates that the scrape should continue, even if the bill does not exist in
        the Legistar web interface

        START_DATE_PRIVATE_SCRAPE (class attr) - a timestamp that indicates when to start scraping
        private bills. The scraper can safely skip bills from early legislative sessions,
        because those bills will remain private.
        """
        super().__init__(*args, **kwargs)

        self.params = {"Token": TOKEN}
        self.scrape_restricted = True

    def _is_restricted(self, matter):
        is_board_correspondence = matter["MatterTypeName"] in {
            "Board Box",
            "Board Correspondence",
        }
        is_not_sent = matter["MatterStatusName"] != "Sent"

        if (
            matter["MatterRestrictViewViaWeb"]
            or matter["MatterStatusName"] == "Draft"
            or matter["MatterBodyName"] == "TO BE REMOVED"
            or (is_board_correspondence and is_not_sent)
            or not matter.get("legistar_url")
        ):
            return True
        else:
            return False

    def _show_attachment(self, attachment):
        return attachment["MatterAttachmentShowOnInternetPage"]

    def session(self, action_date):
        from . import Lametro

        localize = pytz.timezone(self.TIMEZONE).localize
        fmt = "%Y-%m-%d"

        for session in Lametro.legislative_sessions:
            start_datetime = datetime.datetime.strptime(session["start_date"], fmt)
            end_datetime = datetime.datetime.strptime(session["end_date"], fmt)

            if localize(start_datetime) <= action_date <= localize(end_datetime):
                return session["identifier"]

        raise ValueError("Invalid action date: {}".format(action_date))

    def sponsorships(self, matter_id):
        for i, sponsor in enumerate(self.sponsors(matter_id)):
            sponsorship = {}
            if i == 0:
                sponsorship["primary"] = True
                sponsorship["classification"] = "Primary"
            else:
                sponsorship["primary"] = False
                sponsorship["classification"] = "Regular"

            sponsor_name = sponsor["MatterSponsorName"].strip()

            if sponsor_name == "Board of Directors - Regular Board Meeting":
                sponsor_name = "Board of Directors"

            sponsorship["name"] = sponsor_name
            sponsorship["entity_type"] = "organization"

            yield sponsorship

    def actions(self, matter_id):
        old_action = None
        for action in self.history(matter_id):
            # Metro admin added an action with a classifcation of 'DISCUSSED (do not use).'
            # They requested that we do not pull in this data.
            action_description = action["MatterHistoryActionName"].strip()
            if "do not use" in action_description:
                continue
            action_date = action["MatterHistoryActionDate"]
            responsible_org = action["MatterHistoryActionBodyName"].strip()
            if responsible_org == "Board of Directors - Regular Board Meeting":
                responsible_org = "Board of Directors"

            if all((action_date, action_description, responsible_org)):
                action_date = self.toTime(action_date).date()

                bill_action = {
                    "description": action_description,
                    "date": action_date,
                    "organization": {"name": responsible_org},
                    "classification": ACTION_CLASSIFICATION[action_description],
                }
                if bill_action != old_action:
                    old_action = bill_action
                else:
                    continue

                if (
                    action["MatterHistoryEventId"] is not None
                    and action["MatterHistoryRollCallFlag"] is not None
                    and action["MatterHistoryPassedFlag"] is not None
                ):

                    # Do we want to capture vote events for voice votes?
                    # Right now we are not?
                    bool_result = action["MatterHistoryPassedFlag"]
                    result = "pass" if bool_result else "fail"

                    votes = (result, self.votes(action["MatterHistoryId"]))
                else:
                    votes = (None, [])

                yield bill_action, votes

    def matters(self, since_datetime=None):
        """
        If a since_datetime is provided, scrape matters updated within the
        window, as well as matters on agendas of events updated within the
        window or scheduled to happen in the future, as they are likely to
        change.
        """
        if since_datetime:
            seen = set()

            for matter in super().matters(since_datetime=since_datetime):
                seen.add(matter["MatterId"])
                yield matter

            event_scraper = LametroEventScraper(self.jurisdiction, self.datadir)
            event_scraper.requests_per_minute = self.requests_per_minute
            event_scraper.cache_write_only = self.cache_write_only

            for api_event, _ in event_scraper.events(since_datetime=since_datetime):
                for agenda_item in event_scraper.agenda(api_event):
                    matter_id = agenda_item["EventItemMatterId"]  # Can be null

                    if matter_id and matter_id not in seen:
                        yield self.matter(matter_id)
                        seen.add(matter_id)

        else:
            yield from super().matters()

    def scrape(self, window=28, matter_ids=None):
        """By default, scrape board reports updated in the last 28 days.
        Optionally specify a larger or smaller window of time from which to
        scrape updates, or specific matters to scrape.
        Note that passing a value for :matter_ids supercedes the value of
        :window, such that the given matters will be scraped regardless of
        when they were updated.

        Optional parameters
        :window (numeric) - Amount of time for which to scrape updates, e.g.
        a window of 7 will scrape legislation updated in the last week. Pass
        a window of 0 to scrape all legislation.
        :matter_ids (str) - Comma-separated list of matter IDs to scrape
        """

        if matter_ids:
            matters = [self.matter(matter_id) for matter_id in matter_ids.split(",")]
            matters = filter(None, matters)  # Skip matters that are not yet in Legistar
        elif float(window):  # Support for partial days, i.e., window=0.15
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
            matters = self.matters(n_days_ago)
        else:
            # Scrape all matters, including those without a last-modified date
            matters = self.matters()

        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for matter in matters:
            # Skip this bill, until Metro cleans up duplicate in Legistar API
            if matter["MatterFile"] == "2017-0447":
                continue

            matter_id = matter["MatterId"]
            date = matter["MatterIntroDate"]
            title = matter["MatterTitle"]
            identifier = matter["MatterFile"]

            if not all((date, title, identifier)):
                continue

            bill_is_temporary = identifier.lower().startswith("tmp")
            if bill_is_temporary:
                continue

            # Do not scrape private bills introduced before this timestamp.
            if self._is_restricted(matter) and (date < self.START_DATE_PRIVATE_SCRAPE):
                continue

            bill_session = self.session(self.toTime(date))
            # Metro uses different classifications than OCD's controlled
            # vocabulary. We store that under extras -> local_classification.
            bill_type = None

            if identifier.startswith("S"):
                alternate_identifiers = [identifier]
                identifier = identifier[1:]
            else:
                alternate_identifiers = []

            bill = Bill(
                identifier=identifier,
                legislative_session=bill_session,
                title=title,
                classification=bill_type,
                from_organization={"name": "Board of Directors"},
            )

            # The Metro scraper scrapes private bills.
            # However, we do not want to capture significant data about private bills,
            # other than the value of the helper function `_is_restricted` and a last modified timestamp.
            # We yield private bills early, wipe data from previously imported once-public bills,
            # and include only data *required* by the pupa schema.
            # https://github.com/opencivicdata/pupa/blob/master/pupa/scrape/schemas/bill.py
            bill.extras = {"restrict_view": self._is_restricted(matter)}

            # Add API source early.
            # Private bills should have this url for debugging.
            legistar_api = self.BASE_URL + "/matters/{0}".format(matter_id)
            bill.add_source(legistar_api, note="api")

            if self._is_restricted(matter):
                # required fields
                bill.title = "Restricted View"

                # wipe old data
                bill.extras["plain_text"] = ""
                bill.extras["rtf_text"] = ""
                bill.sponsorships = []
                bill.related_bills = []
                bill.versions = []
                bill.documents = []
                bill.actions = []

                yield bill
                continue

            legistar_web = matter["legistar_url"]
            bill.add_source(legistar_web, note="web")

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for action, vote in self.actions(matter_id):
                act = bill.add_action(**action)

                if action["description"] == "Referred":
                    body_name = matter["MatterBodyName"]
                    act.add_related_entity(
                        body_name,
                        "organization",
                        entity_id=_make_pseudo_id(name=body_name),
                    )

                result, votes = vote
                if result:
                    vote_event = VoteEvent(
                        legislative_session=bill.legislative_session,
                        motion_text=action["description"],
                        organization=action["organization"],
                        classification=None,
                        start_date=action["date"],
                        result=result,
                        bill=bill,
                    )

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + "/histories")

                    for vote in votes:
                        try:
                            raw_option = vote["VoteValueName"].lower()
                        except AttributeError:
                            raw_option = None
                        clean_option = self.VOTE_OPTIONS.get(raw_option, raw_option)
                        vote_event.vote(clean_option, vote["VotePersonName"].strip())

                    yield vote_event

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for topic in self.topics(matter_id):
                bill.add_subject(topic["MatterIndexName"].strip())

            for relation in self.relations(matter_id):
                try:
                    # Get data (i.e., json) for the related bill.
                    # Then, we can find the 'MatterFile' (i.e., identifier) and the 'MatterIntroDate' (i.e., to determine its legislative session).
                    # Sometimes, the related bill does not yet exist: in this case, throw an error, and continue.
                    related_bill = self.endpoint(
                        "/matters/{0}", relation["MatterRelationMatterId"]
                    )
                except scrapelib.HTTPError:
                    continue
                else:
                    date = related_bill["MatterIntroDate"]
                    related_bill_session = self.session(self.toTime(date))
                    identifier = related_bill["MatterFile"]
                    bill.add_related_bill(
                        identifier=identifier,
                        legislative_session=related_bill_session,
                        relation_type="companion",
                    )
                    # Currently, the relation type for bills can be one of a few possibilites: https://github.com/opencivicdata/python-opencivicdata/blob/master/opencivicdata/common.py#L104
                    # Metro simply understands these as related files, suggesting that they receive a relation of 'companion'.

            bill.add_version_link(
                "Board Report",
                "https://metro.legistar.com/ViewReport.ashx?M=R&N=TextL5&GID=557&ID={}&GUID=LATEST&Title=Board+Report".format(
                    matter_id
                ),
                media_type="application/pdf",
            )

            for attachment in self.attachments(matter_id):
                if attachment["MatterAttachmentName"] and self._show_attachment(
                    attachment
                ):
                    bill.add_document_link(
                        attachment["MatterAttachmentName"],
                        attachment["MatterAttachmentHyperlink"].strip(),
                        media_type="application/pdf",
                    )

            bill.extras["local_classification"] = matter["MatterTypeName"]

            matter_version_value = matter["MatterVersion"]
            text = self.text(matter_id, matter_version_value)

            if text:
                if text["MatterTextPlain"]:
                    bill.extras["plain_text"] = text["MatterTextPlain"]

                if text["MatterTextRtf"]:
                    bill.extras["rtf_text"] = text["MatterTextRtf"].replace(
                        "\u0000", ""
                    )

            yield bill


# Defined according to OCD standard here:
# https://github.com/opencivicdata/python-opencivicdata/blob/master/opencivicdata/common.py#L113
ACTION_CLASSIFICATION = {
    "WITHDRAWN": "withdrawal",
    "APPROVED": "passage",
    "RECOMMENDED FOR APPROVAL": "committee-passage-favorable",
    "RECEIVED AND FILED": "filing",
    "RECOMMENDED FOR APPROVAL AS AMENDED": "committee-passage-favorable",
    "APPROVED AS AMENDED": "passage",
    "APPROVED THE CONSENT CALENDAR": "passage",
    "APPROVED ON CONSENT CALENDAR": "passage",
    "DISCUSSED": None,
    "ADOPTED": "passage",
    "ADOPTED AS AMENDED": "passage",
    "FORWARDED WITHOUT RECOMMENDATION": "committee-passage",
    "CARRIED OVER": "deferral",
    "RECEIVED": "receipt",
    "REFERRED": "referral-committee",
    "FORWARDED DUE TO ABSENCES AND CONFLICTS": "committee-passage",
    "NO ACTION TAKEN": "filing",
    "FAILED": "failure",
    "APPROVED UNDER RECONSIDERATION": "passage",
    "NOT DISCUSSED": "deferral",
}
