from pupa.scrape import Jurisdiction

from .events import BostonEventsScraper
from .people import BostonPersonScraper
from .vote import BostonVoteScraper


class Boston(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ma/place:boston/council'

    name = 'Boston City Council'
    url = 'http://www.cityofboston.gov/citycouncil/'
    extras = {
        "social_media": {
            "twitter": "https://twitter.com/BOSCityCouncil",
            "facebook": "https://www.facebook.com/pages/Boston-City-Council/106846899335407",
        }
    }

    scrapers = {
        "people": BostonPersonScraper,
        "events": BostonEventsScraper,
        "votes": BostonVoteScraper,
    }
