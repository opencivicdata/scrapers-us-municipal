from pupa.scrape import Scraper
from pupa.scrape import Person
from .utils import Utils, StlScraper

class StLouisPersonScraper(StlScraper):

	def scrape(self):
		# FIXME maybe should be `yield from`?
		yield self.scrape_people()

	def scrape_people(self):
		for ward_num in range(1, self.jurisdiction.WARD_COUNT + 1):
			# FIXME maybe should be `yield from`?
			yield self.scrape_alderman(ward_num)

	def scrape_alderman(self, ward_num):
		ward_url = "{}/ward-{}".format(Utils.ALDERMEN_HOME, ward_num)
		alderman_url = self.alderman_url(ward_url)
		alderman_page = self.lxmlize(alderman_url)

		# person's name is the only <h1> tag on the page
		name = alderman_page.xpath("//h1/text()")[0]

		# initialize person object with appropriate data so that pupa can 
		# automatically create a membership object linking this person to
		# a post in the jurisdiction's "Board of Aldermen" organization
		district = "Ward {} Alderman".format(ward_num)
		person = Person(name=name, district=district, role="Alderman", 
										primary_org="legislature")

		# set additional fields
		person.image = alderman_page.xpath("//div/img/@src")[0]
		phone_number = alderman_page.xpath("//strong[text()='Phone:']/../text()")[1].strip()
		person.add_contact_detail(type="voice", value=phone_number)

		# add sources
		person.add_source(alderman_url, note="profile")
		person.add_source(ward_url, note="ward")

		return person

	def alderman_url(self, ward_url):
		ward_page = self.lxmlize(ward_url)
		# each ward page contains a link to the current alderman's profile.
		# the text of the link says "Email <Jane Doe>" where Jane Doe is the
		# name of the alderman.
		# find that link by selecting for <a> tags whose text contains 'Email'
		return ward_page.xpath("//a[contains(text(), 'Email')]//@href")[0]
