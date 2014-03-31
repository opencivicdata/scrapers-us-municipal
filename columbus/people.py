from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html

HOMEPAGE = "http://council.columbus.gov/"

class ColumbusPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape_homepage(self, folk):
        url = folk.attrib['href']
        page = self.lxmlize(url)
        image = page.xpath(
            "//img[contains(@src, 'uploadedImages/City_Council/Members/')]"
        )[0].attrib['src']

        name = page.xpath("//div[@id='ctl00_ctl00_Body_body_cntCommon']/h3")
        name, = name

        bio = "\n\n".join([x.text_content() for x in page.xpath(
            "//div[@id='ctl00_ctl00_Body_body_cntCommon']/p"
        )])

        leg = Legislator(name=name.text,
                         post_id='member',
                         biography=bio,
                         image=image)
        leg.add_source(url)
        return leg

    def scrape(self):
        page = self.lxmlize(HOMEPAGE)
        folks = page.xpath("//div[@class='col-left']/div[2]//"
                           "div[@class='gutter_text'][1]//"
                           "ul[@class='gutterlist']/li//a")
        for folk in folks:
            yield self.scrape_homepage(folk)
