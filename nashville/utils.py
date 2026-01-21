import lxml.html
from pupa.scrape import Scraper
from pupa.utils import convert_pdf

class NashvilleScraper(Scraper):
    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def strip_string_array(self, string_array):
        stripped = [string.strip() for string in string_array]
        return ' '.join(stripped)

    def get_dnn_name(self, doc):
        (dnn_name, *rest) = doc.xpath('//div[@id="dnn_ContentPane"]/div/a/@name')
        return dnn_name
    
    def pdf_to_lxml(self, url):
        (filename, resp) = self.urlretrieve(url)
        text = convert_pdf(filename, 'html')
        return lxml.html.fromstring(text)

