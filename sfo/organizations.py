from pupa.scrape import Organization
from legistar.base import LegistarScraper


class LegistarOrganizationScraper(LegistarScraper):
    DEPARTMENTLIST = None
    ALL_DEPARTMENTS = None

    def organizations(self) :
        if self.ALL_DEPARTMENTS :
            page = self.lxmlize(self.DEPARTMENTLIST)
            payload = self.sessionSecrets(page)
            payload['__EVENTTARGET'] = "ctl00$ContentPlaceHolder1$menuMain"
            payload['__EVENTARGUMENT'] = self.ALL_DEPARTMENTS

        for page in self.pages(self.DEPARTMENTLIST, payload) :
            table = page.xpath(
                "//table[@id='ctl00_ContentPlaceHolder1_gridMain_ctl00']")[0]

            for organization, _, _ in self.parseDataTable(table) :
                yield organization

class SFOrganizationScraper(LegistarOrganizationScraper) :
    DEPARTMENTLIST = 'https://sfgov.legistar.com/Departments.aspx'
    ALL_DEPARTMENTS = '3:2'

    ORG_CLASSIFICATION = {
            'Committee': 'committee',
            'Board or Commission': 'commission',
            }

    def scrape(self):
        for org in self.organizations() :
            committee_name = org['Department Name']
            org_type = org['Type']
            if org_type in ['Committee', 'Board or Commission'] :

                if org_type == 'Board or Commission' and 'Commission' not in committee_name :
                    continue

                o = Organization(committee_name,
                                 classification=self.ORG_CLASSIFICATION.get(org_type),
                                 parent_id={'name' : self.jurisdiction.council_name})
                o.add_source(self.DEPARTMENTLIST)

                yield o

