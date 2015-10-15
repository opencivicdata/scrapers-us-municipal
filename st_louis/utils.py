from lxml import html
import requests


class Utils(object):

	@staticmethod
	def lxmlize(url):
		entry = requests.get(url)
		page = html.fromstring(entry.text)
		page.make_links_absolute(url)
		return page
