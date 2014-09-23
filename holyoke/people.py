from pupa.scrape import Scraper, Person, Membership
from pupa.utils import make_psuedo_id
import lxml.html

CITY_CLERK = "http://www.holyoke.org/departments/city-clerk/"
CITY_TREASURER = "http://www.holyoke.org/departments/treasurer/"
CITY_COUNCIL = "http://www.holyoke.org/departments/city-council/"
CITY_MAYOR = "http://www.holyoke.org/departments/mayors-office"


class HolyokePersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape_council(self):
        page = self.lxmlize(CITY_COUNCIL)
        seen = set()
        for member in page.xpath(
            "//a[contains(@href, 'holyoke.org/city-council/')]"
        ):
            url = member.attrib['href']
            if url in seen:
                continue
            seen.add(url)
            yield from self.scrape_counciler(member.attrib['href'])

    def scrape_counciler(self, url):
        page = self.lxmlize(url)
        who, = page.xpath("//h3[@class='subtitle']/text()")
        district, = page.xpath("//div[@class='right-bar']//h2/text()")
        image, = page.xpath(
            "//div[@class='left-bar']//a[@class='image lightbox']//img"
        )

        member = Person(
            primary_org='legislature',
            name=who, district=district,
            image=image.attrib['src']
        )
        member.add_source(url)

        details = page.xpath("//table[@align='center']//td")
        for detail in details:
            detail = detail.text_content().strip()
            if detail is None or detail == "":
                continue

            type_, value = detail.split(":", 1)
            cdtype = {
                "Home Phone": "voice",
                "Address": "address",
                "Email": "email",
                "Cell Phone": "voice",
            }[type_]
            member.add_contact_detail(type=cdtype,
                                      note=type_,
                                      value=value)

        yield member

    def scrape_clerk(self):
        yield from self.scrape_staff(CITY_CLERK, 'clerk')

    def scrape_treasurer(self):
        yield from self.scrape_staff(CITY_CLERK, 'treasurer')

    def scrape_mayor(self):
        yield from self.scrape_staff(CITY_MAYOR, 'mayor')

    def scrape_staff(self, url, role):
        page = self.lxmlize(url)
        bar, = page.xpath("//div[@class='right-bar']")
        head, office, contact, _ = bar.xpath(".//div[@class='module']")
        name, = head.xpath(".//h4")
        title, social = head.xpath(".//p")

        head = Person(name=name.text_content())
        head.add_source(url)

        membership = Membership(
            post_id=make_psuedo_id(role=role,),
            role=role,
            label=title.text_content(),
            person_id=head._id,
            organization_id=make_psuedo_id(
                classification="legislature"))
        yield membership

        emails = social.xpath(".//a[contains(@href, 'mailto:')]")
        for email in emails:
            head.add_contact_detail(type='email',
                                     value=email.attrib['href'],
                                     note='Office Email')

        offices = office.xpath(".//p")
        for office in offices:
            head.add_contact_detail(type='address',
                                     value=office.text_content(),
                                     note='Office Address')

        contacts = contact.xpath(".//span")
        for contact in contacts:
            class_ = contact.attrib['class']
            type_ = {"icon-phone": "voice",
                     "icon-fax": "fax",
                     "icon-email": "email"}[class_]

            value = contact.tail
            if value is None:
                value = contact.getnext()
                value = value.text_content() if value is not None else None

            if value is None:
                continue

            head.add_contact_detail(type=type_,
                                    value=value,
                                    note="Office Contact Detail")
        yield head

        staff, = page.xpath("//div[@id='staff']")
        for member in staff.xpath(
            "//div[@class='table-item clearfix remove-clickable']"
        ):
            name, = member.xpath(".//span[@class='title1']")
            name = name.text
            name, staff_role = name.rsplit("-", 1)
            name = name.strip()
            staff_role = staff_role.strip()

            staffer = Person(name=name)
            staffer.add_source(url)
            details = member.xpath(".//p/span")

            membership = Membership(
                role=staff_role,
                label="%s-staff" % (role),
                person_id=staffer._id,
                organization_id=make_psuedo_id(
                    classification="legislature",))
            yield membership

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
        yield from self.scrape_treasurer()
        yield from self.scrape_mayor()
        yield from self.scrape_council()
