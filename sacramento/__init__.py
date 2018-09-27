# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .bills import SacramentoBillScraper
from .vote_events import SacramentoVoteEventScraper
from .events import SacramentoEventScraper
from .people import SacramentoPersonScraper


class Sacramento(Jurisdiction):
    division_id = "ocd-division/country:us/state:ca/place:sacramento"
    classification = "legislature"
    name = "Sacramento City Council"
    url = "http://www.cityofsacramento.org/"
    scrapers = {
        # "bills": SacramentoBillScraper,
        # "vote_events": SacramentoVoteEventScraper,
        # "events": SacramentoEventScraper,
        "people": SacramentoPersonScraper,
    }

    def get_organizations(self):

        org = Organization(name="Sacramento City Council", classification="legislature")

        org.add_post(label='Mayor of the City of Sacramento',
                     role='Mayor',
                     division_id='ocd-division/country:us/state:ca/place:sacramento')

        for district in range(1, 9):
            org.add_post(label='Sacramento City Council Member, District {}'.format(district),
                         role='Member',
                         division_id='ocd-division/country:us/state:ca/place:sacramento/council_district:{}'.format(district))

        yield org
