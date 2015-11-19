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

class Urls(object):

	BASE_URL = "https://www.stlouis-mo.gov/government"
	ALDERMEN_HOME = BASE_URL + "/departments/aldermen"
	BILLS_HOME = BASE_URL + "/city-laws/board-bills/index.cfm"
	COMMITTEES_HOME = ALDERMEN_HOME + "/committee.cfm" 


class HumanName(object):
	""" 
	custom hack to avoid dependency on https://pypi.python.org/pypi/nameparser 
	"""
	
	@staticmethod
	def name_firstandlast(raw_name):
		""" 
		given a string (presumed to be a person's name), try to return
		just the person's first and last name without cruft
		e.g. 'Megan E. Green'     => 'Megan Green' 
				 'Freeman Bosley Sr.' => 'Freeman Bosley'
		"""
		# FIXME various corner cases fail
		# e.g. 'Bill de la Garza'   => 'Bill Garza'
		#      'Freeman Bosley III' => 'Freeman III'

		words = raw_name.split(" ")
		firstname, *rest = words
		# last name is the farthest-back word that does not contain "."
		clean_rest = [ w for w in rest if "." not in w ]
		try: 
			lastname = " " + clean_rest[-1]
		except IndexError:
			lastname = ""
		return firstname + lastname

