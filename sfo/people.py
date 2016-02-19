from pupa.scrape import Person, Organization
from .legistar import LegistarScraper
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PEOPLE_PAGE = 'https://sfgov.legistar.com/People.aspx'


class SFPersonScraper(LegistarScraper):
    base_url = 'https://sfgov.legistar.com/'

    def People(self, follow_links=True) :
        for page in self.pages(PEOPLE_PAGE) :
            table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]

            for person, _, _ in self.parseDataTable(table):
                if follow_links and type(person['Person Name']) == dict:
                    if type(person['Web Site']) == dict:
                        website_url = person['Web Site']['url']
                        website = self.lxmlize(website_url)
                        elem = website.xpath("//*[@class='sup_district']")
                        if elem:
                            person['District'] = elem[0].text.strip()

                        contact_p = website.xpath("//*[@id='sup_right']/h2[contains(.,'Contact Info')]/following::p")
                        if contact_p:
                            # TODO: Split this into phone and address
                            True

                    detail_url = person['Person Name']['url']
                    person_details = self.lxmlize(detail_url)
                    img = person_details.xpath(
                        "//img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        person['Photo'] = img[0].get('src')

                    committee_table = person_details.xpath(
                        "//table[@id='ctl00_ContentPlaceHolder1_gridDepartments_ctl00']")[0]
                    committees = self.parseDataTable(committee_table)

                    yield person, committees

                else :
                    yield person


    def scrape(self):
        committee_d = {}
        non_committees = {
            'Board of Supervisors',
            }

        for person, committees in self.People() :
            if person['District'] == None:
                continue

            district = person['District']
            role = "Supervisor"
            p = Person(
                person['Person Name']['label'],
                district=district,
                primary_org="legislature",
                role=role,
                )

            if person['Photo'] :
                p.image = person['Photo']

            if person["E-mail"]:
                p.add_contact_detail(
                    type="email",
                    value=person['E-mail']['label'],
                    note='E-mail'
                    )


            if person['Web Site']:
                p.add_link(person['Web Site']['url'])
            p.add_source(person['Person Name']['url'], note='web')

            yield p

            for committee, _, _ in committees:
                committee_name = committee['Department Name']
                if committee_name and committee_name not in non_committees:
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        o = Organization(
                            committee_name,
                            classification='committee',
                            parent_id={'name' : 'San Francisco Board of Supervisors'}
                            )
                        o.add_source(PEOPLE_PAGE, note='web')
                        committee_d[committee_name] = o

                    o.add_member(
                        p,
                        role=committee["Title"],
                        start_date=self.toTime(committee['Start Date']).date(),
                        end_date=self.toTime(committee['End Date']).date(),
                        )

        for o in committee_d.values() :
            yield o
