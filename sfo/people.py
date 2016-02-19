from pupa.scrape import Person, Organization
from .legistar import LegistarScraper
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMBERLIST = 'https://sfgov.legistar.com/People.aspx'


class SFPersonScraper(LegistarScraper):
    timezone = 'US/Pacific'
    base_url = 'https://sfgov.legistar.com/'

    def councilMembers(self, follow_links=True) :
        for page in self.pages(MEMBERLIST) :
            table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]

            for councilman, _, _ in self.parseDataTable(table):
                if follow_links and type(councilman['Person Name']) == dict:
                    if type(councilman['Web Site']) == dict:
                        website_url = councilman['Web Site']['url']
                        website = self.lxmlize(website_url)
                        elem = website.xpath("//*[@class='sup_district']")
                        if elem:
                            councilman['District'] = elem[0].text.strip()

                        contact_p = website.xpath("//*[@id='sup_right']/h2[contains(.,'Contact Info')]/following::p")
                        if contact_p:
                            # TODO: Split this into phone and address
                            True

                    detail_url = councilman['Person Name']['url']
                    councilman_details = self.lxmlize(detail_url)
                    img = councilman_details.xpath(
                        "//img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        councilman['Photo'] = img[0].get('src')

                    committee_table = councilman_details.xpath(
                        "//table[@id='ctl00_ContentPlaceHolder1_gridDepartments_ctl00']")[0]
                    committees = self.parseDataTable(committee_table)

                    yield councilman, committees

                else :
                    yield councilman


    def scrape(self):
        committee_d = {}
        non_committees = {
            'Board of Supervisors',
            }

        for councilman, committees in self.councilMembers() :
            if councilman['District'] == None:
                continue

            district = councilman['District']
            role = "Supervisor"
            p = Person(
                councilman['Person Name']['label'],
                district=district,
                primary_org="legislature",
                role=role,
                )

            if councilman['Photo'] :
                p.image = councilman['Photo']

            def split_newlines(node):
                lines = []
                for elem in node.xpath("./*[following-sibling::*[name()='br']]"):
                    lines.append(elem.tail.strip())
                return lines

            if councilman["E-mail"]:
                p.add_contact_detail(
                    type="email",
                    value=councilman['E-mail']['label'],
                    note='E-mail'
                    )


            if councilman['Web Site']:
                p.add_link(councilman['Web Site']['url'])
            p.add_source(councilman['Person Name']['url'], note='web')

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
                        o.add_source(MEMBERLIST, note='web')
                        committee_d[committee_name] = o

                    o.add_member(
                        p,
                        role=committee["Title"],
                        start_date=self.toTime(committee['Start Date']).date(),
                        end_date=self.toTime(committee['End Date']).date(),
                        )

        for o in committee_d.values() :
            yield o
