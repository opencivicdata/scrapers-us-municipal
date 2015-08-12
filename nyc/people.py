import re

from pupa.scrape import Person, Organization
from legistar.people import LegistarPersonScraper



class NYCPersonScraper(LegistarPersonScraper):
    MEMBERLIST = 'http://legistar.council.nyc.gov/People.aspx'

    def scrape(self):
        noncommittees = {'Committee of the Whole'}
        committee_types = {'Committee', 'Subcommittee', 'Land Use'}
        committee_d = {}

        p = Person('Mark S. Weprin',
                   district = 'District 23',
                   primary_org = 'legislature',
                   role='Council Member',
                   end_date='2015-06-14')
        p.add_source('https://en.wikipedia.org/wiki/Mark_Weprin')

        yield p

        p = Person('Letitia Ms. James',
                   district = 'District 35',
                   primary_org = 'legislature',
                   role='Council Member',
                   end_date='2013-12-31')
        p.add_source('https://en.wikipedia.org/wiki/Letitia_James')

        yield p

        p = Person('Vincent Ignizio',
                   district = 'District 51',
                   primary_org = 'legislature',
                   role='Council Member',
                   end_date='2015-05-31')
        p.add_source('https://en.wikipedia.org/wiki/Vincent_M._Ignizio')

        yield p

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
                org_type = committee['Type']
                if committee_name not in noncommittees and org_type in committee_types :
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        parent_id = PARENT_ORGS.get(committee_name,
                                                    'New York City Council')
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : parent_id})
                        o.add_source("http://legistar.council.nyc.gov/Departments.aspx")
                        committee_d[committee_name] = o

                    membership = o.add_member(p, role=committee["Title"])
                    membership.start_date = self.mdY2Ymd(committee["Start Date"])
            yield p

        for o in committee_d.values() :
            yield o


PARENT_ORGS = {
    'Subcommittee on Landmarks, Public Siting and Maritime Uses' : 'Committee on Land Use',
    'Subcommittee on Libraries' : 'Committee on Cultural Affairs, Libraries and International Intergroup Relations',
    'Subcommittee on Non-Public Schools' : 'Committee on Education',
    'Subcommittee on Planning, Dispositions and Concessions' : 'Committee on Land Use',
    'Subcommittee on Senior Centers' : 'Committee on Aging',
    'Subcommittee on Zoning and Franchises' : 'Committee on Land Use'}
