import datetime
import itertools

import pytz
import requests
import scrapelib
from legistar.bills import LegistarAPIBillScraper, LegistarBillScraper
from pupa.scrape import Bill, Scraper, VoteEvent
from pupa.utils import _make_pseudo_id


def sort_actions(actions):
    action_time = "MatterHistoryActionDate"
    action_name = "MatterHistoryActionName"
    sorted_actions = sorted(
        actions,
        key=lambda x: (
            x[action_time].split("T")[0],
            ACTION[x[action_name]]["order"],
            x[action_time].split("T")[1],
        ),
    )

    return sorted_actions


class ChicagoBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = "http://webapi.legistar.com/v1/chicago"
    BASE_WEB_URL = "https://chicago.legistar.com"
    TIMEZONE = "US/Central"

    VOTE_OPTIONS = {
        "yea": "yes",
        "rising vote": "yes",
        "nay": "no",
        "recused": "excused",
    }

    def session(self, action_date):
        localize = pytz.timezone(self.TIMEZONE).localize
        if action_date < localize(datetime.datetime(2011, 5, 18)):
            return "2007"
        elif action_date < localize(datetime.datetime(2015, 5, 18)):
            return "2011"
        elif action_date < localize(datetime.datetime(2019, 5, 20)):
            return "2015"
        else:
            return "2019"

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

            if sponsor_name.startswith(("City Clerk",)):
                sponsorship["name"] = "Office of the City Clerk"
                sponsorship["entity_type"] = "organization"
            else:
                sponsorship["name"] = sponsor_name
                sponsorship["entity_type"] = "person"

            if not sponsor_name.startswith(
                ("Misc. Transmittal", "No Sponsor", "Dept./Agency")
            ):
                yield sponsorship

    def actions(self, matter_id):
        old_action = None
        actions = self.history(matter_id)
        actions = sort_actions(actions)

        for action in actions:
            action_date = action["MatterHistoryActionDate"]
            action_description = action["MatterHistoryActionName"]
            motion_text = action["MatterHistoryActionText"]
            responsible_org = action["MatterHistoryActionBodyName"]

            action_date = self.toTime(action_date).date()

            responsible_person = None
            if responsible_org == "City Council":
                responsible_org = "Chicago City Council"
            elif responsible_org == "Office of the Mayor":
                responsible_org = "City of Chicago"
                if action_date < datetime.date(2011, 5, 16):
                    responsible_person = "Daley, Richard M."
                else:
                    responsible_person = "Emanuel, Rahm"

            bill_action = {
                "description": action_description,
                "date": action_date,
                "motion_text": motion_text,
                "organization": {"name": responsible_org},
                "classification": ACTION[action_description]["ocd"],
                "responsible person": responsible_person,
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

                bool_result = action["MatterHistoryPassedFlag"]
                result = "pass" if bool_result else "fail"

                # Votes that are not roll calls, i.e., voice votes, sometimes
                # include "votes" that omit the vote option (yea, nay, etc.).
                # Capture that a vote occurred, but skip recording the
                # null votes, as they break the scraper.

                matter_history_id = action["MatterHistoryId"]
                action_text = action["MatterHistoryActionText"] or ""

                if "voice vote" in action_text.lower():
                    # while there should not be individual votes
                    # for voice votes, sometimes there are.
                    #
                    # http://webapi.legistar.com/v1/chicago/eventitems/163705/votes
                    # http://webapi.legistar.com/v1/chicago/matters/26788/histories

                    self.info(
                        "Skipping votes for history {0} of matter ID {1}".format(
                            matter_history_id, matter_id
                        )
                    )
                    votes = (result, [])
                else:
                    votes = (result, self.votes(matter_history_id))
            else:
                votes = (None, [])

            yield bill_action, votes

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        for matter in self.matters(n_days_ago):
            matter_id = matter["MatterId"]

            date = matter["MatterIntroDate"]
            title = matter["MatterTitle"]
            identifier = matter["MatterFile"]

            # If a bill has a duplicate action item that's causing the entire scrape
            # to fail, add it to the `problem_bills` array to skip it.
            # For the time being...nothing to skip!

            problem_bills = ["Or2011-189"]

            if identifier in problem_bills:
                continue

            if not all((date, title, identifier)):
                continue

            bill_session = self.session(self.toTime(date))
            bill_type = BILL_TYPES[matter["MatterTypeName"]]

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
                from_organization={"name": "Chicago City Council"},
            )

            legistar_web = matter["legistar_url"]

            legistar_api = "http://webapi.legistar.com/v1/chicago/matters/{0}".format(
                matter_id
            )

            bill.add_source(legistar_web, note="web")
            bill.add_source(legistar_api, note="api")

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for current, subsequent in pairwise(self.actions(matter_id)):
                action, vote = current
                responsible_person = action.pop("responsible person")
                motion_text = action.pop("motion_text") or action["description"]
                act = bill.add_action(**action)

                if responsible_person:
                    act.add_related_entity(
                        responsible_person,
                        "person",
                        entity_id=_make_pseudo_id(name=responsible_person),
                    )

                if action["description"] in {"Referred", "Re-Referred"}:
                    if subsequent is None:
                        body_name = matter["MatterBodyName"]
                        if body_name != "City Council":
                            act.add_related_entity(
                                body_name,
                                "organization",
                                entity_id=_make_pseudo_id(name=body_name),
                            )
                    else:
                        next_action, _ = subsequent
                        next_body_name = next_action["organization"]["name"]
                        if next_body_name != "City Council":
                            act.add_related_entity(
                                next_body_name,
                                "organization",
                                entity_id=_make_pseudo_id(name=next_body_name),
                            )

                result, votes = vote
                if result:
                    vote_event = VoteEvent(
                        legislative_session=bill.legislative_session,
                        motion_text=motion_text,
                        organization=action["organization"],
                        classification=action["classification"],
                        start_date=action["date"],
                        result=result,
                        bill_action=action["description"],
                        bill=bill,
                    )

                    vote_event.add_source(legistar_web)
                    vote_event.add_source(legistar_api + "/histories")

                    for vote in votes:
                        vote_value = vote["VoteValueName"]
                        if vote_value is None:
                            continue
                        raw_option = vote_value.lower()
                        clean_option = self.VOTE_OPTIONS.get(raw_option, raw_option)
                        vote_event.vote(clean_option, vote["VotePersonName"].strip())

                    yield vote_event

            for sponsorship in self.sponsorships(matter_id):
                bill.add_sponsorship(**sponsorship)

            for topic in self.topics(matter_id):
                bill.add_subject(topic["MatterIndexName"].strip())

            for attachment in self.attachments(matter_id):
                if attachment["MatterAttachmentName"]:
                    bill.add_version_link(
                        attachment["MatterAttachmentName"],
                        attachment["MatterAttachmentHyperlink"],
                        media_type="application/pdf",
                    )

            relations = self.relations(matter_id)
            identified_relations = []
            for relation in relations:
                relation_matter_id = relation["MatterRelationMatterId"]
                try:
                    relation_matter = self.matter(relation_matter_id)
                except scrapelib.HTTPError:
                    continue
                relation_identifier = relation_matter["MatterFile"]
                try:
                    relation_date = self.toTime(relation_matter["MatterIntroDate"])
                except TypeError:
                    continue
                relation_bill_session = self.session(relation_date)
                identified_relations.append(
                    {
                        "identifier": relation_identifier,
                        "legislative_session": relation_bill_session,
                        "date": relation_date,
                    }
                )

            if identified_relations:
                intro_date = self.toTime(date)
                relation_type = None
                if len(identified_relations) == 1:
                    if identified_relations[0]["date"] >= intro_date:
                        relation_type = "replaced-by"
                elif all(
                    relation["date"] <= intro_date for relation in identified_relations
                ):
                    relation_type = "replaces"

                if relation_type is None:
                    self.warn("Unclear relation for {0}".format(matter_id))

                else:
                    for relation in identified_relations:
                        bill.add_related_bill(
                            relation["identifier"],
                            relation["legislative_session"],
                            relation_type,
                        )

            bill.extras = {"local_classification": matter["MatterTypeName"]}

            text = self.text(matter_id)

            if text:
                if text["MatterTextPlain"]:
                    plain_text = text["MatterTextPlain"]
                    bill.extras["plain_text"] = plain_text

            yield bill


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)


ACTION = {
    "Direct Introduction": {"ocd": "introduction", "order": 0},
    "Introduced (Agreed Calendar)": {"ocd": "introduction", "order": 0},
    "Rules Suspended - Immediate Consideration": {"ocd": "introduction", "order": 0},
    "Referred": {"ocd": "referral-committee", "order": 1},
    "Re-Referred": {"ocd": "referral-committee", "order": 1},
    "Substituted in Committee": {"ocd": "substitution", "order": 1},
    "Amended in Committee": {"ocd": "amendment-passage", "order": 1},
    "Withdrawn": {"ocd": "withdrawal", "order": 1},
    "Remove Co-Sponsor(s)": {"ocd": None, "order": 1},
    "Add Co-Sponsor(s)": {"ocd": None, "order": 1},
    "Recommended for Re-Referral": {"ocd": None, "order": 1},
    "Committee Discharged": {"ocd": "committee-passage", "order": 1},
    "Held in Committee": {"ocd": "committee-failure", "order": 1},
    "Recommended Do Not Pass": {"ocd": "committee-passage-unfavorable", "order": 1},
    "Recommended to Pass": {"ocd": "committee-passage-favorable", "order": 1},
    "Deferred and Published": {"ocd": None, "order": 2},
    "Amended in City Council": {"ocd": "amendment-passage", "order": 2},
    "Failed to Pass": {"ocd": "failure", "order": 2},
    "Passed as Amended": {"ocd": "passage", "order": 2},
    "Adopted": {"ocd": "passage", "order": 2},
    "Approved": {"ocd": "passage", "order": 2},
    "Passed": {"ocd": "passage", "order": 2},
    "Approved as Amended": {"ocd": "passage", "order": 2},
    "Passed as Substitute": {"ocd": "passage", "order": 2},
    "Adopted as Substitute": {"ocd": None, "order": 2},
    "Placed on File": {"ocd": "filing", "order": 2},
    "Tabled": {"ocd": "deferral", "order": 2},
    "Vetoed": {"ocd": "failure", "order": 2},
    "Published in Special Pamphlet": {"ocd": None, "order": 3},
    "Signed by Mayor": {"ocd": "executive-signature", "order": 3},
    "Repealed": {"ocd": None, "order": 4},
}


BILL_TYPES = {
    "Ordinance": "ordinance",
    "Resolution": "resolution",
    "Order": "order",
    "Claim": "claim",
    "Oath of Office": None,
    "Communication": None,
    "Appointment": "appointment",
    "Report": None,
}
