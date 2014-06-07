from pupa.scrape import Scraper, Legislator, Committee, Person, Membership
from pupa.utils import make_psuedo_id
import lxml.html

CITY_CLERK = "http://www.holyoke.org/departments/city-clerk/"
CITY_TREASURER = "http://www.holyoke.org/departments/treasurer/"
CITY_COUNCIL = "http://www.holyoke.org/councilors/"


class HolyokePersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape_clerk(self):
        page = self.lxmlize(CITY_CLERK)
        bar, = page.xpath("//div[@class='right-bar']")
        head, office, contact, _ = bar.xpath(".//div[@class='module']")
        name, = head.xpath(".//h4")
        title, social = head.xpath(".//p")

        clerk = Person(name=name.text_content())
        clerk.add_source(CITY_CLERK)

        membership = Membership(
            role='clerk',
            label=title.text_content(),
            person_id=clerk._id,
            organization_id=make_psuedo_id(
                classification="legislature",
                name=self.jurisdiction.name))

        emails = social.xpath(".//a[contains(@href, 'mailto:')]")
        for email in emails:
            clerk.add_contact_detail(type='email',
                                     value=email.attrib['href'],
                                     note='Office Email')

        offices = office.xpath(".//p")
        for office in offices:
            clerk.add_contact_detail(type='address',
                                     value=office.text_content(),
                                     note='Office Address')

        contacts = contact.xpath(".//span")
        for contact in contacts:
            class_ = contact.attrib['class']
            type_ = {"icon-phone": "voice",
                     "icon-email": "email"}[class_]

            value = contact.tail
            if value is None:
                value = contact.getnext()
                value = value.text_content() if value is not None else None

            if value is None:
                continue

            clerk.add_contact_detail(type=type_,
                                     value=value,
                                     note="Office Contact Detail")
        yield clerk

        staff, = page.xpath("//div[@id='staff']")
        for member in staff.xpath(
            "//div[@class='table-item clearfix remove-clickable']"
        ):
            name, = member.xpath(".//span[@class='title1']")
            staffer = Person(name=name.text)
            staffer.add_source(CITY_CLERK)
            details = member.xpath(".//p/span")

            for detail in details:
                type_ = {
                    "icon-phone marker": "voice",
                    "icon-email marker": "email",
                }[detail.attrib['class']]
                value = detail.tail
                if value is None:
                    value = detail.getnext()
                    value = value.text_content() if value is not None else None

                if value is None:
                    continue

                staffer.add_contact_detail(type=type_,
                                           value=value,
                                           note="Office")

            yield staffer

    def scrape(self):
        yield from self.scrape_clerk()
