from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import TemeculaEventScraper


class Temecula(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:temecula/council'

    name = 'Temecula City Council'
    url = 'http://www.cityoftemecula.org/Temecula/Government/CouncilCommissions/CityCouncil/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    scrapers = {'people': PersonScraper, 'events': TemeculaEventScraper}
