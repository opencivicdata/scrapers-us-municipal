from pupa.scrape.helpers import Legislator, Membership, Organization
from .legistar import LegistarScraper
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MEMBERLIST = 'https://chicago.legistar.com/People.aspx'


class ChicagoPersonScraper(LegistarScraper):
    base_url = 'https://chicago.legistar.com/'

    def councilMembers(self, follow_links=True) :
        for page in self.pages(MEMBERLIST) :
            table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]

            for councilman, headers, row in self.parseDataTable(table):
                if follow_links and type(councilman['Person Name']) == dict :
                    detail_url = councilman['Person Name']['url']
                    councilman_details = self.lxmlize(detail_url)
                    img = councilman_details.xpath("//img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        councilman['Photo'] = img[0].get('src')

                    committee_table = councilman_details.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridDepartments_ctl00']")[0]

                    committees = self.parseDataTable(committee_table)

                    yield councilman, committees

                else :
                    yield councilman


    def scrape(self):
        for councilman, committees in self.councilMembers() :
            contact_types = {
                "City Hall Office": ("address", "City Hall Office"),
                "City Hall Phone": ("phone", "City Hall Phone"),
                "Ward Office Phone": ("phone", "Ward Office Phone"),
                "Ward Office Address": ("address", "Ward Office Address"),
                "Fax": ("fax", "Fax")
            }

            contacts = []
            for contact_type, (_type, note) in contact_types.items () :
                if councilman[contact_type] :
                    contacts.append({"type": _type,
                                     "value": councilman[contact_type],
                                     "note": note})

            if councilman["E-mail"] :
                contacts.append({"type" : "email",
                                 "value" : councilman['E-mail']['label'],
                                 'note' : 'E-mail'})


            p = Legislator(councilman['Person Name']['label'],
                           district="Ward %s" % (councilman['Ward/Office']),
                           image=councilman['Photo'],
                           contact_details = contacts)


            if councilman['Website'] :
                p.add_link('homepage', councilman['Website']['url'])
            p.add_source(MEMBERLIST)

            for committee, _, _ in committees :
                if committee['Legislative Body']['label'] :
                    print(committee)
                    if committee['Legislative Body']['label'] not in ('City Council', 'Office of the Mayor') :
                        p.add_committee_membership(committee['Legislative Body']['label'],
                                                   role= committee["Title"])



            yield p



