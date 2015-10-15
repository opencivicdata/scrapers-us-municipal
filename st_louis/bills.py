from pupa.scrape import Scraper
from pupa.scrape import Bill
from pupa.scrape import BaseBillScraper
from .utils import Utils

# we subclass pupa.scrape.BaseBillScraper -- special helper for bill scrapers
# see https://github.com/opencivicdata/pupa/blob/master/ARCHITECTURE.md#pupascrape
class StLouisBillScraper(BaseBillScraper):

	def get_bill_ids(self):
		# TODO
		return None

	def get_bill(self, bill_id):
		# TODO
		raise self.ContinueScraping()