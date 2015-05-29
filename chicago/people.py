from pupa.scrape import Person, Organization
from .legistar import LegistarScraper
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMBERLIST = 'https://chicago.legistar.com/People.aspx'


class ChicagoPersonScraper(LegistarScraper):
    base_url = 'https://chicago.legistar.com/'

    def councilMembers(self, follow_links=True) :
        for page in self.pages(MEMBERLIST) :
            table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]

            for councilman, headers, row in self.parseDataTable(table):
                if follow_links and type(councilman['Person Name']) == dict:
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
        non_committees = ('City Council', 'Office of the Mayor')

        for councilman, committees in self.councilMembers() :
            if councilman['Ward/Office'] == "":
                continue

            ward = councilman['Ward/Office']
            if ward not in [
                "Mayor",
                "Clerk",
            ]:
                ward = "Ward {}".format(int(ward))
                role = "Alderman"
            else:
                role = ward
            p = Person(councilman['Person Name']['label'],
                       district=ward,
                       primary_org="legislature",
                       role=role)

            if councilman['Photo'] :
                p.image = councilman['Photo']

            contact_types = {
                "City Hall Office": ("address", "City Hall Office"),
                "City Hall Phone": ("voice", "City Hall Phone"),
                "Ward Office Phone": ("voice", "Ward Office Phone"),
                "Ward Office Address": ("address", "Ward Office Address"),
                "Fax": ("fax", "Fax")
            }

            for contact_type, (type_, _note) in contact_types.items():
                if councilman[contact_type]:
                    p.add_contact_detail(type=type_,
                                         value= councilman[contact_type],
                                         note=_note)

            if councilman["E-mail"]:
                p.add_contact_detail(type="email",
                                     value=councilman['E-mail']['label'],
                                     note='E-mail')


            if councilman['Website']:
                p.add_link(councilman['Website']['url'])
            p.add_source(MEMBERLIST)

            for committee, _, _ in committees:
                committee_name = committee['Legislative Body']['label']
                if committee_name and committee_name not in non_committees:
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : 'Chicago City Council'})
                        o.add_source("https://chicago.legistar.com/Departments.aspx")
                        committee_d[committee_name] = o

                    o.add_member(p, role=committee["Title"])
            yield p

        for o in committee_d.values() :
            yield o
