from pupa.scrape import Person
from legistar.people import LegistarPersonScraper
import datetime


class SFPersonScraper(LegistarPersonScraper):
    MEMBERLIST = 'https://sfgov.legistar.com/MainBody.aspx'
    TIMEZONE = 'US/Pacific'
    ALL_MEMBERS = "3:0"

    def scrape(self):
        noncommittees = {'Board of Supervisors'}
        people_d = {}

        for councilman, committees in self.councilMembers() :

            if 'url' in councilman['Web Site'] :
                website_url = councilman['Web Site']['url']
                website = self.lxmlize(website_url)
                elem = website.xpath("//*[@class='sup_district']")
                if elem:
                    councilman['District'] = elem[0].text.strip()

            if 'url' in councilman['Person Name'] :
                councilman_url = councilman['Person Name']['url']

                if councilman_url in people_d :
                    people_d[councilman_url][0].append(councilman)
                else :
                    people_d[councilman_url] = [councilman], committees

        for person_entries, committees in people_d.values() :

            councilman = person_entries[-1]

            p = Person(councilman['Person Name']['label'])

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
                if end_date > datetime.date.today() :
                    end_date = ''
                else :
                    end_date = end_date.isoformat()
                print(start_date, end_date)
                #p.add_term('Council Member', 'legislature',
                #           district=district,
                #           start_date=start_date.isoformat(),
                #           end_date=end_date)

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
                committee_name = committee['Department Name']
                if committee_name not in noncommittees :
                    if committee['Title'] == 'Supervisor' :
                        committee['Title'] = 'Committee Member'
                    p.add_membership(committee_name,
                                     role=committee["Title"],
                                     start_date=self.mdY2Ymd(committee['Start Date']),
                                     end_date=self.mdY2Ymd(committee['End Date'])
                                     )
            yield p
