from pupa.scrape import Scraper
from pupa.scrape import Bill
from pupa.scrape import BaseBillScraper
from .utils import Utils

# we subclass pupa.scrape.BaseBillScraper -- special helper for bill scrapers
# see https://github.com/opencivicdata/pupa/blob/master/ARCHITECTURE.md#pupascrape
class StLouisBillScraper(Scraper):

	def scrape(self):
		for session in self.jurisdiction.legislative_sessions:
			session_id = session["identifier"]
			session_url = self.bill_session_url(session_id)
			page = Utils.lxmlize(session_url)

			# bills are in a <table class="data"> 
			bill_rows = page.xpath("//table[@class='data']/tr")
			# first row is headers, so ignore it
			bill_rows.pop(0)
			
			for row in bill_rows:
				id_link    = row.xpath("td[1]/a")[0]
				title_link = row.xpath("td[3]/a")[0]

				bill_id    = id_link.xpath("text()")[0]
				bill_url   = id_link.xpath("@href")[0]
				bill_title = title_link.xpath("text()")[0]

				bill = Bill(identifier=bill_id,
					        legislative_session=session_id,
					        title=bill_title)
				bill.add_source(bill_url)
				yield bill

	def bill_session_url(self, session_id):
		return Utils.BILLS_HOME + "?sessionBB=" + session_id

