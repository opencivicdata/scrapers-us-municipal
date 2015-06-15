import re

from pupa.scrape import Person, Organization
from legistar.people import LegistarPersonScraper



class NYCPersonScraper(LegistarPersonScraper):
    MEMBERLIST = 'http://legistar.council.nyc.gov/People.aspx'

    def scrape(self):
        non_committees = {'City Council'}
        committee_d = {}

        for councilman, committees in self.councilMembers() :
            district = re.search('.*(District \d+).*?',
                                 councilman['Notes']).group(1)
            if ('Democrat' in councilman['Notes'] 
                or 'Democratic' in councilman['Notes']) :
                party = 'Democratic'
            elif 'Republican' in councilman ['Notes'] :
                party = 'Republican'
            else :
                party = None
            
            

            p = Person(councilman['Person Name']['label'],
                       district=district,
                       primary_org="legislature",
                       role='Council Member')

            if councilman['Photo'] :
                p.image = councilman['Photo']

            if councilman["E-mail"]:
                p.add_contact_detail(type="email",
                                     value=councilman['E-mail'],
                                     note='E-mail')

            if councilman['Website']:
                p.add_link(councilman['Website']['url'])
                
            p.add_source(councilman['Person Name']['url'])

            for committee, _, _ in committees:
                committee_name = committee['Department Name']['label']
                if committee_name and committee_name not in non_committees:
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : 'New York City Council'})
                        o.add_source("http://legistar.council.nyc.gov/Departments.aspx")
                        committee_d[committee_name] = o

                    membership = o.add_member(p, role=committee["Title"])
                    membership.start_date = self.mdY2Ymd(committee["Start Date"])
            yield p

        for o in committee_d.values() :
            yield o
