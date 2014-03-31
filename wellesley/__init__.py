from pupa.scrape import Jurisdiction

from .people import WellesleyPersonScraper


class Wellesley(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ma/place:wellesley/council'
    name = 'Wellesley Board of Selectmen'
    url = 'http://www.wellesleyma.gov/Pages/WellesleyMA_Selectmen/index'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    scrapers = {
        "people": WellesleyPersonScraper,
    }
