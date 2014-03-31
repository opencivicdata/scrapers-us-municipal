import re

import lxml, lxml.html

from pupa.scrape import Scraper
from pupa.scrape.helpers import Legislator, Organization

class PersonScraper(Scraper):

    COUNTY_BOARD_URL = 'http://www.arlingtonva.us/Departments/CountyBoard/meetings/members/CountyBoardMeetingsMembersMain.aspx'

    def scrape(self):
        board_html = self.urlopen(self.COUNTY_BOARD_URL)
        board_lxml = lxml.html.fromstring(board_html)
        board_lxml.make_links_absolute(base_url=self.COUNTY_BOARD_URL)

        for board_member_lxml in board_lxml.cssselect("div[name=cbo_list] div[name=row]"):
            name = board_member_lxml.cssselect("div[name=info] strong")[0].text.strip()
            image = board_member_lxml.cssselect("div[name=pictures] img")[0].get('src')
            pieces = re.split(r'<br\s*\/?>', lxml.html.tostring(board_member_lxml.cssselect("div[name=info]")[0]).decode(), re.I)
            position = re.sub(r'<[^>]*>', '', pieces[1]).strip()
            links = board_member_lxml.cssselect("div[name=info] a")
            email = bio_link = None
            for link in links:
                if link.text is None:
                    continue
                if 'arlingtonva.us' in link.text.lower():
                    email = re.sub(r'\s*\(at\)\s*','@', link.text).strip()
                elif 'bio' in link.text.lower():
                    bio_link = link

            legislator = Legislator(name=name, post_id=position, image=image)
            legislator.add_contact(type='email', value=email, note='%(name)s email address' % {'name': name} )
            legislator.add_source(self.COUNTY_BOARD_URL)

            bio = None
            if bio_link is not None:
                bio_href = bio_link.attrib.get('href')
                bio_html = self.urlopen(bio_href)
                bio_lxml = lxml.html.fromstring(bio_html)
                bio_text = re.sub(r'<[^>]*>', '', lxml.html.tostring(bio_lxml.cssselect('#textSection #text')[0]).decode(), re.I).strip()
                bio_text = re.sub(r'&#160;', ' ', bio_text)
                legislator.biography = bio_text
                legislator.add_link('bio page', bio_href)

            yield legislator
