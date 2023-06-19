import datetime
import itertools

import pytz
from pupa.scrape import Bill, Scraper, VoteEvent
from pupa.utils import _make_pseudo_id
import scrapelib

from .base import ElmsAPI


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


class ChicagoBillScraper(ElmsAPI, Scraper):
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
        elif action_date < localize(datetime.datetime(2023, 5, 15)):
            return "2019"
        else:
            return "2023"

    def sponsorships(self, matter_id, intro_date_str):
        intro_date = self.toTime(intro_date_str)
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
                sponsorship["entity_type"] = "person"
                if intro_date < datetime.date(2011, 5, 16):
                    sponsorship["name"] = "Del Valle, Miguel"
                elif intro_date < datetime.date(2017, 1, 25):
                    sponsorship["name"] = "Mendoza, Susana A."
                else:
                    sponsorship["name"] = "Valencia, Anna M."
            else:
                sponsorship["name"] = sponsor_name
                sponsorship["entity_type"] = "person"

            # maybe handle departments differently?
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
                elif action_date < datetime.date(2019, 5, 20):
                    responsible_person = "Emanuel, Rahm"
                else:
                    responsible_person = "Lightfoot, Lori E."

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

    def _matters(self, n_days_ago):

        for matter in self._paginate(
            self._endpoint("/matter"),
            {
                "filter": f"finalActionDate gt {n_days_ago.isoformat()}",
                "sort": "finalActionDate asc",
            },
        ):
            detailed_matter = self.get(self._endpoint(f'/matter/{matter["matterId"]}'))
            yield detailed_matter.json()

    def scrape(self, window=3):
        n_days_ago = datetime.datetime.now().astimezone() - datetime.timedelta(
            float(window)
        )
        for matter in self._matters(n_days_ago):
            matter_id = matter["matterId"]

            if not (intro_date_str := matter["introductionDate"]):
                continue

            intro_date = datetime.datetime.fromisoformat(intro_date_str)
            title = matter["title"]
            identifier = matter["recordNumber"]

            if not all((title, identifier)):
                raise

            bill_session = self.session(intro_date)
            bill_type = BILL_TYPES[matter["type"]]

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

            bill_detail_url = self._endpoint(f"/matter/{matter_id}")
            bill.add_source(bill_detail_url, note="api")

            for identifier in alternate_identifiers:
                bill.add_identifier(identifier)

            for current, subsequent in pairwise(matter["actions"]):
                if not (action_name_raw := current["actionName"]):
                    continue

                action_name = action_name_raw.strip()

                if action_name in {"Create", "Submit", "Accept", "Post to Public"}:
                    continue

                if not (action_date := current["actionDate"]):
                    continue

                action = bill.add_action(
                    action_name,
                    datetime.datetime.fromisoformat(action_date),
                    classification=ACTION[action_name]["ocd"],
                    organization={"name": current["actionByName"]},
                )

                if action["classification"] == ["referral-committee"] and subsequent:
                    next_body_name = subsequent["actionByName"]
                    if next_body_name and next_body_name != "City Council":
                        action.add_related_entity(
                            next_body_name,
                            "organization",
                            entity_id=_make_pseudo_id(name=next_body_name),
                        )

                if votes := current["votes"]:

                    # result is not always pass, like i say it is here.
                    # let's address that later
                    vote_event = VoteEvent(
                        legislative_session=bill.legislative_session,
                        motion_text=current["actionText"],
                        organization=current["actionByName"],
                        classification=action["classification"],
                        start_date=action["date"],
                        result="pass",
                        bill_action=action["description"],
                        bill=bill,
                    )

                    vote_event.add_source(bill_detail_url)

                    for vote in votes:
                        vote_value = vote["vote"].lower()
                        clean_option = self.VOTE_OPTIONS.get(vote_value, vote_value)
                        vote_event.vote(clean_option, vote["voterName"].strip())

                    yield vote_event

            for sponsor in matter["sponsors"]:
                if sponsor_name := sponsor["sponsorName"]:
                    bill.add_sponsorship(
                        sponsor_name.strip(),
                        sponsor["sponsorType"],
                        "person",
                        sponsor["sponsorType"] == "Filing Sponsor",
                    )

            if subject := matter["matterCategory"]:
                bill.add_subject(subject)

            for attachment in matter["attachments"]:
                bill.add_version_link(
                    attachment["fileName"],
                    attachment["path"],
                    media_type="application/pdf",
                )

            relations = [
                record_number
                for record_number in matter["relations"]
                if record_number != "CL2012-149"
            ]
            identified_relations = []
            for record_number in relations:
                try:
                    relation_matter = self.get(
                        self._endpoint(f"/matter/recordNumber/{record_number}")
                    ).json()
                except scrapelib.HTTPError:
                    continue

                relation_date = datetime.datetime.fromisoformat(
                    relation_matter["introductionDate"]
                )
                relation_bill_session = self.session(relation_date)
                identified_relations.append(
                    {
                        "identifier": record_number,
                        "legislative_session": relation_bill_session,
                        "date": relation_date,
                    }
                )

            if identified_relations:
                relation_type = None
                if len(identified_relations) == 1:
                    if identified_relations[0]["date"] >= intro_date:
                        relation_type = "replaced-by"
                elif all(
                    relation["date"] <= intro_date for relation in identified_relations
                ):
                    relation_type = "replaces"

                if relation_type is None:
                    self.warning("Unclear relation for {0}".format(identifier))

                else:
                    for relation in identified_relations:
                        bill.add_related_bill(
                            relation["identifier"],
                            relation["legislative_session"],
                            relation_type,
                        )

            bill.extras = {
                "local_classification": matter["type"],
                "key_legislation": matter["keyLegislation"] == "YES",
            }

            yield bill


def pairwise(iterable):
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)


ACTION = {
    "Introduce": {"ocd": "introduction", "order": 0},
    "Direct Introduction": {"ocd": "introduction", "order": 0},
    "Introduced (Agreed Calendar)": {"ocd": "introduction", "order": 0},
    "Rules Suspended - Immediate Consideration": {"ocd": "introduction", "order": 0},
    "Refer": {"ocd": "referral-committee", "order": 1},
    "Referred": {"ocd": "referral-committee", "order": 1},
    "Re-Referred": {"ocd": "referral-committee", "order": 1},
    "Substituted in Committee": {"ocd": "substitution", "order": 1},
    "Single Substitute": {"ocd": "substitution", "order": 1},
    "Amended in Committee": {"ocd": "amendment-passage", "order": 1},
    "Amended": {"ocd": "amendment-passage", "order": 1},
    "Withdrawn": {"ocd": "withdrawal", "order": 1},
    "Remove Co-Sponsor(s)": {"ocd": None, "order": 1},
    "Add Co-Sponsor(s)": {"ocd": None, "order": 1},
    "Recommended for Re-Referral": {"ocd": None, "order": 1},
    "Committee Discharged": {"ocd": "committee-passage", "order": 1},
    "Held in Committee": {"ocd": "committee-failure", "order": 1},
    "Recommend Do Not Pass": {"ocd": "committee-passage-unfavorable", "order": 1},
    "Recommended Do Not Pass": {"ocd": "committee-passage-unfavorable", "order": 1},
    "Recommend to Pass": {"ocd": "committee-passage-favorable", "order": 1},
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
