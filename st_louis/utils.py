from lxml import html
import requests


class Utils(object):

	BASE_URL = "https://www.stlouis-mo.gov"
	ALDERMEN_HOME = BASE_URL + "/government/departments/aldermen"
	BILLS_HOME = ALDERMEN_HOME + "/city-laws/board-bills.cfm"

	@staticmethod
	def lxmlize(url):
		entry = requests.get(url)
		page = html.fromstring(entry.text)
		page.make_links_absolute(url)
		return page

