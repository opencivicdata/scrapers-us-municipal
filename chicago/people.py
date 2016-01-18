from pupa.scrape import Person, Organization
from .legistar import LegistarScraper
import logging
import datetime


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
        non_committees = {'City Council', 'Office of the Mayor',
                          'Office of the City Clerk'}

        for councilman, committees in self.councilMembers() :
            if councilman['Ward/Office'] == "":
                continue

            ward = councilman['Ward/Office']
            if ward not in {"Mayor", "Clerk"} :

                ward = "Ward {}".format(int(ward))
                role = "Alderman"
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
            p.add_source(councilman['Person Name']['url'], note='web')

            for committee, _, _ in committees:
                committee_name = committee['Legislative Body']['label']
                if committee_name and committee_name not in non_committees:
                    o = committee_d.get(committee_name, None)
                    if o is None:
                        o = Organization(committee_name,
                                         classification='committee',
                                         parent_id={'name' : 'Chicago City Council'})
                        o.add_source(committee['Legislative Body']['url'], 
                                     note='web')
                        committee_d[committee_name] = o

                    o.add_member(p, role=committee["Title"])

            yield p

        for name, term in FORMER_ALDERMEN.items() :
            p =  Person(name=name,
                        primary_org="legislature",
                        start_date=term['term'][0],
                        end_date=term['term'][1],
                        district="Ward {}".format(term['ward']),
                        role='Alderman')
            if name == 'Chandler, Michael D.' :
                p.add_term('Alderman',
                           "legislature",
                           district="Ward {}".format(term['ward']),
                           start_date=datetime.date(2011, 5, 16),
                           end_date=datetime.date(2015, 5, 18))

            p.add_source(term['source'], note='web')
            yield p

        for o in committee_d.values() :
            yield o

        for committee_name in FORMER_COMMITTEES :
            o = Organization(committee_name, 
                             classification='committee',
                             parent_id={'name' : 'Chicago City Council'})
            o.add_source("https://chicago.legistar.com/Departments.aspx", 
                         note='web')
            yield o

        for joint_committee in JOINT_COMMITTEES :

            o = Organization(joint_committee, 
                             classification='committee',
                             parent_id={'name' : 'Chicago City Council'})
            o.add_source("https://chicago.legistar.com/Departments.aspx",
                         note='web')
            yield o

        
FORMER_ALDERMEN = {"Thomas, Latasha R.": {'term': ('2000', 
                                                   datetime.date(2015, 5, 18)),
                                          'ward': 17,
                                          'source': 'https://en.wikipedia.org/wiki/Latasha_Thomas'},
                   "Rugai, Virginia": {'term': ('1990-12', 
                                                datetime.date(2011, 5, 16)),
                                       'ward': 19,
                                       'source': 'https://chicago.legistar.com/LegislationDetail.aspx?ID=888062&GUID=DD19729C-1A71-4742-BC32-67F9991CEA38&FullText=1'},
                   "Rice, John": {'term': (datetime.date(2009, 10, 7),
                                           datetime.date(2011, 5, 16)),
                                  'ward': 36,
                                  'source': 'https://en.wikipedia.org/wiki/John_Rice_%28alderman%29'},
                   "Cullerton, Timothy M.": {'term': (datetime.date(2011, 1, 13), 
                                                      datetime.date(2015, 5, 18)),
                                             'ward': 38,
                                             'source': 'http://www.chicagotribune.com/news/local/politics/chi-northwest-side-ald-cullerton-wont-run-for-reelection-20140716-story.html'},
                   "Smith, Mary Ann": {'term': ('1989', datetime.date(2011, 5, 16)), 
                                       'ward': 48,
                                       'source': 'http://chicagoist.com/2010/08/06/48th_ward_ald_mary_ann_smith_announ.php'},
                   "Thompson, JoAnn": {'term' : (datetime.date(2007, 5, 21), 
                                                 datetime.date(2015, 2, 9)),
                                       'ward': 16,
                                       'source': 'http://www.chicagotribune.com/news/ct-thompson-funeral-met-20150216-story.html'},
                   "Dixon, Sharon": {'term' : (datetime.date(2007, 5, 21), 
                                               datetime.date(2011, 5, 16)),
                                     'ward' : 24,
                                     'source': 'https://en.wikipedia.org/wiki/Sharon_Denise_Dixon'},
                   "Daley, Vi": {'term' : ('1999', datetime.date(2011, 5, 16)),
                                 'ward' : 43,
                                 'source': 'https://en.wikipedia.org/wiki/Vi_Daley'},
                   "Fioretti, Bob": {'term' : (datetime.date(2007, 5, 21), 
                                               datetime.date(2015, 5, 18)),
                                     'ward' : 2,
                                     'source': 'https://en.wikipedia.org/wiki/Robert_Fioretti'},
                   "Balcer, James": {'term' : ('1997', datetime.date(2015, 5, 18)),
                                     'ward' : 11,
                                     'source': 'https://en.wikipedia.org/wiki/Robert_Fioretti'},
                   "Shiller, Helen": {'term' : ('1987', 
                                                datetime.date(2011, 5, 16)),
                                      'ward' : 46,
                                      'source': 'https://en.wikipedia.org/wiki/Helen_Shiller'},
                   "Olivo, Frank": {'term' : ('1994', 
                                              datetime.date(2011, 5, 16)),
                                    'ward' : 13,
                                    'source': 'https://en.wikipedia.org/wiki/Frank_Olivo'},
                   "Holmes, Natashia": {'term' : (datetime.date(2013, 2, 13),
                                                  datetime.date(2015, 5, 18)),
                                        'ward' : 7,
                                       'source': 'https://en.wikipedia.org/wiki/Natashia_Holmes'},
                   "Col\u00f3n, Rey": {'term' : ('2003', 
                                                 datetime.date(2015, 5, 18)),
                                       'ward' : 35,
                                       'source': 'https://en.wikipedia.org/wiki/Rey_Col%C3%B3n'},
                   "Lyle, Freddrenna": {'term' : (datetime.date(1998, 2, 8), 
                                                  datetime.date(2011, 5, 16)),
                                        'ward' : 6,
                                       'source': 'https://en.wikipedia.org/wiki/Freddrenna_Lyle'},
                   "Pope, John": {'term' : ('1999', 
                                            datetime.date(2015, 5, 18)),
                                  'ward' : 10,
                                  'source': 'https://en.wikipedia.org/wiki/John_Pope_%28alderman%29'},
                   'Chandler, Michael D.': {'term' : ('1995', 
                                                      datetime.date(2007, 5, 21)),
                                            'ward' : 24,
                                            'source': 'http://www.nbcchicago.com/blogs/ward-room/Chicago-City-Council-Michael-Chandler-133643633.html'},
                   "Jackson, Sandi": {'term' : (datetime.date(2007, 5, 21),
                                                datetime.date(2013, 1, 15)),
                                      'ward' : 7,
                                       'source': 'https://en.wikipedia.org/wiki/Sandi_Jackson'},
                   "Preckwinkle, Toni": {'term' : ('1991', 
                                                   datetime.date(2010, 12, 6)),
                                         'ward' : 4,
                                       'source': 'https://chicago.legistar.com/LegislationDetail.aspx?ID=1796824&GUID=F8615605-0DEB-4946-9495-7A0511681B64'},
                   "Stone, Bernard": {'term' : ('1973', datetime.date(2011, 5, 16)),
                                      'ward' : 50,
                                      'source': 'https://en.wikipedia.org/wiki/Bernard_Stone'},
                   "Graham, Deborah L.": {'term' : (datetime.date(2010, 3, 15), 
                                                    datetime.date(2015, 5, 18)),
                                          'ward' : 29,
                                          'source': 'http://www.oakpark.com/News/Articles/3-16-2010/Graham-appointed-Chicago-alderman/'},
                   "Smith, Ed": {'term' : ('1983', 
                                           datetime.date(2010, 11, 30)),
                                 'ward' : 28,
                                 'source': 'https://en.wikipedia.org/wiki/Ed_Smith_%28alderman%29'},
                   "O'Connor, Mary": {'term' : (datetime.date(2011, 5, 16), 
                                                datetime.date(2015, 5, 18)),
                                      'ward' : 41,
                                      'source': "https://en.wikipedia.org/wiki/Mary_O'Connor_%28alderman%29"},
                   "Lane, Lona": {'term' : ('2006', 
                                            datetime.date(2015, 5, 18)),
                                  'ward' : 18,
                                  'source': 'http://www.dnainfo.com/chicago/20150407/ashburn/derrick-curtis-wins-18th-ward-election'},
                   "Allen, Thomas": {'term' : ('1993-03', 
                                               datetime.date(2010, 11, 19)),
                                     'ward' : 38,
                                     'source': 'https://chicago.legistar.com/LegislationDetail.aspx?ID=837428&GUID=6A43F1D5-DD83-4A61-AC6A-8A6E152C11FE'},
                   "Newsome, Shirley": {'term' : (datetime.date(2011, 1, 13), 
                                                  datetime.date(2011, 5, 16)),
                                        'ward' : 4,
                                        'source': 'https://en.wikipedia.org/wiki/4th_Ward,_Chicago'},
                   "Suarez, Regner Ray": {'term' : ('1991', 
                                                    datetime.date(2015, 5, 18)),
                                          'ward' : 31,
                                          'source': 'https://en.wikipedia.org/wiki/Ray_Suarez_%28politician%29'},
                   "Doherty, Brian": {'term' : ('1991', 
                                                datetime.date(2011, 5, 16)),
                                      'ward' : 41,
                                      'source': 'https://en.wikipedia.org/wiki/Brian_Doherty_%28politician%29'},
                   "Schulter, Eugene": {'term' : ('1975', 
                                                  datetime.date(2011, 5, 16)),
                                        'ward' : 47,
                                       'source': 'https://en.wikipedia.org/wiki/Eugene_Schulter'},
                   "Mell, Richard F.": {'term' : ('1975',
                                                  datetime.date(2013, 7, 24)),
                                        'ward' : 33,
                                       'source': 'https://en.wikipedia.org/wiki/Richard_Mell'},
                   "Levar, Patrick": {'term' : ('1987', 
                                                datetime.date(2011, 5, 16)),
                                      'ward' : 45,
                                      'source': 'https://en.wikipedia.org/wiki/Patrick_Levar'}}

FORMER_COMMITTEES = ('Committee on Parks and Recreation',
                     'Committee on Zoning',
                     'Committee on Special Events and Cultural Affairs',
                     'Committee on Historical Landmark Preservation',
                     'Committee on Traffic Control and Safety',
                     'Committee on Buildings',
                     'Committee on Energy, Environmental Protection and Public Utilities',
                     'Committee on Health',
                     'Committee on Police and Fire')

JOINT_COMMITTEES = ('Joint Committee: Housing and Real Estate; Zoning, Landmarks and Building Standards',
                    'Joint Committee: Finance; Special Events, Cultural Affairs and Recreation',
                    'Joint Committee: Budget and Government Operations; Health and Environmental Protection',
                    'Joint Committee: Budget and Government Operations; License and Consumer Protection',
                    'Joint Committee: Budget and Government Operations; Housing and Real Estate; Special Events, Cultural Affairs and Recreation',
                    'Joint Committee: License and Consumer Protection; Transportation and Public Way',
                    'Joint Committee: Health and Environmental Protection; Housing and Real Estate',
                    'Joint Committee: Finance; Housing and Real Estate',
                    'Joint Committee: Budget and Government Operations; Zoning, Landmarks and Building Standards',
                    'Joint Committee: Health and Environmental Protection; License and Consumer Protection',
                    'Joint Committee: Housing and Real Estate; Human Relations',
                    'Joint Committee: Pedestrian and Traffic Safety; Transportation and Public Way',
                    'Joint Committee: Finance; Police and Fire',
                    'Joint Committee: Aviation; Finance',
                    'Joint Committee: Finance; Health and Environmental Protection',
                    'Joint Committee: Finance; Transportation and Public Way',
                    'Joint Committee: Economic, Capital and Technology Development; Housing and Real Estate; Zoning, Landmarks and Building Standards',
                    'Joint Committee: Economic, Capital and Technology Development; Energy, Environmental Protections & Public Utilities; Finance',
                    'Joint Committee: Buildings; Housing and Real Estate',
                    'Joint Committee: Finance; Human Relations')
