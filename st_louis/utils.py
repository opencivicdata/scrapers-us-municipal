from pupa.scrape import Scraper
from lxml import html
import requests


class StlScraper(Scraper):

	def lxmlize(self, url, payload=None):
		if payload:
			entry = self.post(url, payload).text
		else:
			entry = self.get(url).text
		page = html.fromstring(entry)
		page.make_links_absolute(url)
		return page 

class Utils(object):

	BASE_URL = "https://www.stlouis-mo.gov/government"
	ALDERMEN_HOME = BASE_URL + "/departments/aldermen"
	BILLS_HOME = BASE_URL + "/city-laws/board-bills/index.cfm"


