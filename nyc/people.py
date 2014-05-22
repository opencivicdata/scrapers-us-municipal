from legistar.ext.pupa import PupaGenerator
from pupa.scrape import Scraper


class NewYorkCityPersonScraper(Scraper):
    scrape = PupaGenerator('people')
