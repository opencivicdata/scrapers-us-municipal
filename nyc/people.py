from legistar.ext.pupa import PupaGenerator
from pupa.scrape import Scraper


class NewYorkCityPersonScraper(Scraper):
    # This also scrapes orgs.
    scrape = PupaGenerator('people')
