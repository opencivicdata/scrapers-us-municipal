from pupa.scrape import Scraper
from pupa.scrape import Bill
from pupa.scrape import BaseBillScraper
from .utils import Utils
import time

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
				id_link = row.xpath("td[1]/a")[0]
				bill_id = id_link.xpath("text()")[0]
				bill_url = id_link.xpath("@href")[0]
				yield self.scrape_bill(bill_url, bill_id, session_id)


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

		# sponsor
		sponsor_name = data_table.xpath(self.bill_table_query("Sponsor"))[0]
		bill.add_sponsorship(name=sponsor_name,
				classification="Primary",
				entity_type="person",
				primary=True
				)

		# abstract
		summary = data_table.xpath(self.bill_table_query("Summary"))[0]
		bill.add_abstract(abstract=summary, note="summary")
		# TODO clean up weird \t formatting at beginning of summary

		# actions
		actions = data_table.xpath(self.bill_table_query("Actions"))
		for act in actions:
			try:
				date, action_type = self.parse_action(act)
				bill.add_action(date=date,
					description=action_type,	
					classification=action_type)
			except ValueError:
				print("failed to parse action: {}".format(act.strip()))


		# co-sponsors
		co_sponsors = data_table.xpath(self.bill_table_query("Co-Sponsors"))
		co_sponsors = [name.strip() for name in co_sponsors if name.strip()]
		for name in co_sponsors:
			bill.add_sponsorship(name=name,
						classification="co-sponsor",
						entity_type="person",
						primary=False)
		return bill


	def bill_table_query(self, key):
		return "//th[text()='{}:']/../td/text()".format(key)

	def bill_session_url(self, session_id):
		return Utils.BILLS_HOME + "?sessionBB=" + session_id

	def parse_action(self, action_str):
		"""
		action_str will be something like:
		'\n05/15/2015 Second Reading '

		return something like:
		('2015-05-15', 'reading-2')
		"""

		words = action_str.strip().split(" ")

		# date is first word, rest of words describe the bill action
		date_str, *tail = words

		# convert date format from eg "05/12/2015" to "2015-05-12"
		date = time.strptime(date_str, "%m/%d/%Y")
		date_str = time.strftime("%Y-%m-%d", date)

		# try to convert classification from eg
		# "First Reading" to "reading-1"
		classification_str = " ".join(tail)
		try:
			classification = self.action_classifications[classification_str]
		except KeyError:
			raise ValueError("invalid bill action classification: {}"
				.format(classification_str))
			# TODO this exception is triggered in cases of multiple actions
			# on one date, i.e.
			# "05/15/2015 Second Reading,Perfection"
			# Let's catch that and parse it into two separate actions

		return date_str, classification

	action_classifications = {
		"First Reading": "reading-1",
		"Second Reading": "reading-2",
		"Third Reading": "reading-3"
		# TODO other cases. 
		# See http://docs.opencivicdata.org/en/latest/scrape/bills.html
		# what does "Perfection" map to?
	}
		

