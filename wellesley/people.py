from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html
import re

MEMBER_LIST = "http://www.wellesleyma.gov/Pages/WellesleyMA_Clerk/elected"


def clean_address(where):
    baddies = [
        "-",
        "(",
    ]

    for thing in baddies:
        where = where.strip().rstrip(thing)

    where = where.strip()

    return where


class WellesleyPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        page = self.lxmlize(MEMBER_LIST)
        for row in page.xpath("//table[@frame='void']/tbody/tr")[1:]:
            role, whos, expire = row.xpath("./*")
            people = zip([x.text_content() for x in whos.xpath(".//font")],
                         [x.text_content() for x in expire.xpath(".//font")])
            thing = role.text_content()

            comm = Committee(name=thing)
            url = role.xpath(".//a")[0].attrib['href']
            comm.add_link(url=url, note='homepage')

            for person, expire in people:
                if "TBA" in person:
                    continue
                info = {}

                try:
                   info = re.match("(?P<name>.*), (?P<addr>\d+\w* .*)",
                                   person).groupdict()
                except AttributeError:
                    info = re.match("(?P<name>.*) (?P<addr>\d+\w* .*)",
                                    person).groupdict()

                addr = info['addr']

                roles = {"Vice Chair": "Vice Chair",
                         "Chair": "Chair",
                         "CHAIR": "Chair",
                         "Appt": "member",}

                position = "member"

                if "Resigned" in addr:
                    continue

                for role in roles:
                    if role in addr:
                        addr, chair = [x.strip() for x in addr.rsplit(role, 1)]
                        position = roles[role]

                addr = clean_address(addr)
                leg = Legislator(name=info['name'], district=position)
                leg.add_contact_detail(type="address",
                                       value=addr,
                                       note="Address")
                leg.add_source(MEMBER_LIST)
                yield leg

                leg.add_membership(comm)
            comm.add_source(MEMBER_LIST)
            yield comm
