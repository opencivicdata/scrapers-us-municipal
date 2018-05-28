import lxml.html
from pupa.scrape import Scraper

class NashvilleScraper(Scraper):
    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def strip_string_array(self, string_array):
        stripped = [string.strip() for string in string_array]
        return ' '.join(stripped)
