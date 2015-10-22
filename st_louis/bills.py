from pupa.scrape import Scraper
from pupa.scrape import Bill
from pupa.scrape import BaseBillScraper
from .utils import Utils

# we subclass pupa.scrape.BaseBillScraper -- special helper for bill scrapers
# see https://github.com/opencivicdata/pupa/blob/master/ARCHITECTURE.md#pupascrape
class StLouisBillScraper(Scraper):

	def scrape_bill(self, bill_url, bill_id, session_id):
		page = Utils.lxmlize(bill_url)

		# create bill
		title = page.xpath("//em/text()")[0]
		bill = Bill(identifier=bill_id,
			        legislative_session=session_id,
			        title=title)
		bill.add_source(bill_url, note="detail")

		# add additional fields
		data_table = page.xpath("//table[@class='data vertical_table']")[0]

		# abstract
		summary = data_table.xpath(self.bill_table_query("Summary"))[0]
		bill.add_abstract(abstract=summary, note="summary")
		# TODO clean up weird \t formatting at beginning of summary

		# sponsor
		sponsor_name = data_table.xpath(self.bill_table_query("Sponsor"))[0]
		bill.add_sponsorship(name=sponsor_name,
				classification="Primary",
				entity_type="person",
				primary=True
				)

		# actions
		actions = data_table.xpath(self.bill_table_query("Actions"))
		for act in actions:
			date, action_type = self.parse_action(act)
			bill.add_action(description=action_type,	
				date=date, 
				classification=action_type)

		return bill

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
				bill_id    = id_link.xpath("text()")[0]
				bill_url   = id_link.xpath("@href")[0]
				yield self.scrape_bill(bill_url, bill_id, session_id)


	def bill_table_query(self, key):
		return "//th[text()='{}:']/../td/text()".format(key)

	def bill_session_url(self, session_id):
		return Utils.BILLS_HOME + "?sessionBB=" + session_id

	def parse_action(self, action_str):
		words = action_str.strip().split(" ")
		head, *tail = words
		date = head.replace("/", "-")
		classification_str = " ".join(tail)
		classification = self.action_classifications[classification_str]
		print(classification)
		return date, classification

	action_classifications = {
		"First Reading": "reading-1",
		"Second Reading": "reading-2",
		"Third Reading": "reading-3"
	}
		

