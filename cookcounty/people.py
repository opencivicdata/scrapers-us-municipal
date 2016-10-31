from legistar.people import LegistarPersonScraper
import datetime
import re

from pupa.scrape import Person, Organization


class CookcountyPersonScraper(LegistarPersonScraper):
    MEMBERLIST = 'https://cook-county.legistar.com/DepartmentDetail.aspx?ID=20924&GUID=B78A790A-5913-4FBF-8FBF-ECEE445B7796'
    TIMEZONE = 'US/Central'
    ALL_MEMBERS = "3:3"

    def scrape(self):
        committee_d = {}

        for councilman, committees in self.councilMembers() :

            p = Person(' '.join((councilman['First name'], councilman['Last name']))) 
            if p.name == 'Toni Preckwinkle' :
                continue
            elif p.name == 'Robert Steele' :
                district = 2
            elif p.name == 'Jerry Butler' :
                district = 3
            elif p.name == 'Sean Morrison' :
                district = 17
            else :
                district = re.findall('\d+', councilman['Person Name']['url'])[0]

            start_date = self.toTime(councilman['Start Date']).date()
            end_date = self.toTime(councilman['End Date']).date()

            if end_date == datetime.date(2018, 12, 2) :
                end_date = ''
            else :
                end_date = end_date.isoformat()

            p.add_term('Commissioner', 'legislature', 
                       district='District {}'.format(district), 
                       start_date=start_date.isoformat(),
                       end_date=end_date)

            if councilman["E-mail"]:
                p.add_contact_detail(type="email",
                                     value=councilman['E-mail']['url'],
                                     note='E-mail')

            if councilman['Web site']:
                p.add_link(councilman['Web site']['url'], note='web site')


            p.add_source(councilman['Person Name']['url'])

            for committee, _, _ in committees:
                committee_name = committee['Department Name']['label']

                if 'committee' in committee_name.lower() :
                    o = committee_d.get(committee_name, 
                                        None)
                    if o is None:
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : 'Cook County Board of Commissioners'})
                        o.add_source(committee['Department Name']['url'])
                        committee_d[committee_name] = o

                    membership = o.add_member(p, role=committee["Title"])
                    membership.start_date = self.mdY2Ymd(committee["Start Date"])
            yield p

        for o in committee_d.values() :
            yield o
