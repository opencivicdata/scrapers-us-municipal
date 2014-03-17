# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper, Legislator, Committee
from pupa.models import Organization, Person, Event

from collections import defaultdict
import lxml.html


MEMBER_LIST = "http://www.cityofboston.gov/citycouncil/"
COMMITTEE_LIST = "http://www.cityofboston.gov/citycouncil/committees/"


PREFIXES = [
    "Councillors",
    "Councillor",
]


def clean_name(name):
    for thing in PREFIXES:
        name = name.replace(thing, "")
    name = name.encode('latin1').strip()
    name = name.replace("\xc2\xa0", "")
    return name


class BostonPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.bos_scrape_committees()
        yield self.bos_scrape_people()

    def get_one(self, page, expr):
        ret = page.xpath(expr)
        if len(ret) != 1:
            print(page.text_content())
            raise Exception("Bad xpath")
        return ret[0]

    def scrape_homepage(self, href):
        page = self.lxmlize(href)
        ret = {}
        ret['bio'] = page.xpath(
            "//div[@class='content_main_sub']")[0].text_content().strip()
        ret['image'] = page.xpath(
            "//div[@class='sub_main_hd']//img")[0].attrib['src']
        return ret

    def bos_scrape_people(self):
        page = self.lxmlize(MEMBER_LIST)
        people = page.xpath(
            "//table[@width='100%']//td[@style='TEXT-ALIGN: center']")

        for person in people:
            image, name = [self.get_one(person, x) for x in [
                ".//img",
                ".//a[contains(@href, 'councillors') and (text()!='')]"
            ]]
            role = person.xpath(".//br")[0].tail.strip()
            image = image.attrib['src']  # Fallback if we don't get one from the
            # homepage.
            homepage = name.attrib['href']
            name = clean_name(name.text)
            info = self.scrape_homepage(homepage)
            if info.get('image', None):
                image = info['image']

            p = Legislator(name=name,
                           post_id=role,
                           image=image,
                           biography=info['bio'])
            p.add_link(homepage, 'homepage')
            p.add_source(homepage)
            p.add_source(MEMBER_LIST)
            yield p

    def scrape_committee_page(self, href):
        page = self.lxmlize(href)
        main = self.get_one(page, "//div[@class='content_main_sub']")
        things = main.xpath("./*")
        cur = None

        split = {
            "chair": None,
            "email": None,
            "liaison": ",",
            "members": ",",
            "vice-chair": None,
            "description": None,
        }

        flags = {
            "Committee Chair:": "chair",
            "Committee E-mail:": "email",
            "Committee Members:": "members",
            "Committee Liaison:": "liaison",
            "Committee Liaison(s):": "liaison",
            "Committee Vice Chair": "vice-chair",
            "Committee Vice Chair:": "vice-chair",
            "Committee Description:": "description",
        }

        def strip(entry):
            entry = entry.replace(u"\xc2", " ").strip()
            return entry

        ret = defaultdict(list)
        for entry in things:
            if entry.tag == "h4":
                cur = flags[strip(entry.text)]
                continue

            e = entry.text_content()
            if e == "":
                continue

            if split[cur]:
                e = [x.strip() for x in e.split(split[cur])]
            else:
                e = [e]

            ret[cur] += e

        return ret

    def bos_scrape_committees(self):
        page = self.lxmlize(COMMITTEE_LIST)
        committees = page.xpath(
            "//a[contains(@href, 'committee') and contains(@href, 'asp')]")
        for c in committees:
            if c.text is None:
                continue
            name = clean_name(c.text)
            homepage = c.attrib['href']

            info = self.scrape_committee_page(homepage)
            committee = Committee(name, classification='committee')
            committee.add_source(COMMITTEE_LIST)
            committee.add_source(homepage)

            for member in info['members']:
                member = clean_name(member)
                committee.add_member(member, role='member')

            chair = info.get('chair', None)
            if chair:
                chair = chair[0]
                chair = clean_name(chair)
                committee.add_member(chair, role='chair')

            vchair = info.get('vice-chair', None)
            if vchair:
                vchair = vchair[0]
                vchair = clean_name(vchair)
                committee.add_member(vchair, role='vice-chair')

            email = info.get('email', None)
            if email:
                email = email[0]
                committee.add_contact_detail(type='email',
                                             value=email,
                                             note='committee email')
            yield committee
