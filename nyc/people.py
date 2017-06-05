from pupa.scrape import Person, Organization
from legistar.people import LegistarPersonScraper
import datetime

class NYCPersonScraper(LegistarPersonScraper):
    MEMBERLIST = 'http://legistar.council.nyc.gov/DepartmentDetail.aspx?ID=6897&GUID=CDC6E691-8A8C-4F25-97CB-86F31EDAB081'
    TIMEZONE = 'US/Eastern'
    ALL_MEMBERS = "3:2"

    def scrape(self):
        noncommittees = {'Committee of the Whole'}
        committee_d = {}

        people_d = {}

        # Go to memberlist
        extra_args = {'ctl00$ContentPlaceHolder$lstName' : 'City Council'}

        for councilman, committees in self.councilMembers(extra_args=extra_args) :
            
            if 'url' in councilman['Person Name'] :
                councilman_url = councilman['Person Name']['url']

                if councilman_url in people_d :
                    people_d[councilman_url][0].append(councilman) 
                else :
                    people_d[councilman_url] = [councilman], committees

        for person_entries, committees in people_d.values() :

            councilman = person_entries[-1]
            
            p = Person(councilman['Person Name']['label'])
            
            if p.name == 'Letitia James' :
                p.name = 'Letitia Ms. James'
                p.add_name('Letitia James')

            spans = [(self.toTime(entry['Start Date']).date(), 
                      self.toTime(entry['End Date']).date(),
                      entry['District'])
                     for entry in person_entries]

            merged_spans = []
            last_end_date = None
            last_district = None
            for start_date, end_date, district in sorted(spans) :
                if last_end_date is None :
                    span = [start_date, end_date, district]
                elif (start_date - last_end_date) == datetime.timedelta(1) and district == last_district :
                    span[1] = end_date
                else :
                    merged_spans.append(span)
                    span = [start_date, end_date, district]

                last_end_date = end_date
                last_district = district

            merged_spans.append(span)

            for start_date, end_date, district in merged_spans :
                district = councilman['District'].replace(' 0', ' ')
                end_date = end_date.isoformat()
                print(start_date, end_date)
                
                p.add_term('Council Member', 'legislature', 
                           district=district, 
                           start_date=start_date.isoformat(),
                           end_date=end_date)

            party = councilman['Political Party']
            if party == 'Democrat' :
                party = 'Democratic'
            
            if party :
                p.add_party(party)

            if councilman['Photo'] :
                p.image = councilman['Photo']

            if councilman["E-mail"]:
                p.add_contact_detail(type="email",
                                     value=councilman['E-mail']['url'],
                                     note='E-mail')

            if councilman['Web site']:
                p.add_link(councilman['Web site']['url'], note='web site')

            p.extras = {'Notes' : councilman['Notes']}
                 
            p.add_source(councilman['Person Name']['url'], note='web')

            for committee, _, _ in committees:
                committee_name = committee['Department Name']['label']
                if committee_name not in noncommittees and 'committee' in committee_name.lower():
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        parent_id = PARENT_ORGS.get(committee_name,
                                                    'New York City Council')
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : parent_id})
                        o.add_source(committee['Department Name']['url'])
                        committee_d[committee_name] = o

                    membership = o.add_member(p, role=committee["Title"])
                    membership.start_date = self.mdY2Ymd(committee["Start Date"])
            yield p
            

        for o in committee_d.values() :
            if 'Committee' in o.name :
                yield o

        for o in committee_d.values() :
            if 'Subcommittee' in o.name :
                yield o

        o = Organization('Committee on Mental Health, Developmental Disability, Alcoholism, Drug Abuse and Disability Services',
                         classification='committee',
                         parent_id={'name' : 'New York City Council'})
        o.add_source("http://legistar.council.nyc.gov/Departments.aspx")

        yield o

        o = Organization('Subcommittee on Drug Abuse',
                         classification='committee',
                         parent_id={'name' : 'Committee on Mental Health, Developmental Disability, Alcoholism, Drug Abuse and Disability Services'})
        o.add_source("http://legistar.council.nyc.gov/Departments.aspx")

        yield o

            


PARENT_ORGS = {
    'Subcommittee on Landmarks, Public Siting and Maritime Uses' : 'Committee on Land Use',
    'Subcommittee on Libraries' : 'Committee on Cultural Affairs, Libraries and International Intergroup Relations',
    'Subcommittee on Non-Public Schools' : 'Committee on Education',
    'Subcommittee on Planning, Dispositions and Concessions' : 'Committee on Land Use',
    'Subcommittee on Senior Centers' : 'Committee on Aging',
    'Subcommittee on Zoning and Franchises' : 'Committee on Land Use'}
