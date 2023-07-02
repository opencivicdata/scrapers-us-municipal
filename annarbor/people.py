from pupa.scrape import Organization, Scraper
from legistar.people import LegistarAPIPersonScraper


class AnnarborPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/a2gov'
    WEB_URL = 'https://a2gov.legistar.com'
    TIMEZONE = "America/Detroit"

    def scrape(self):

        for body in self.bodies():
            body_type = body['BodyTypeName'].lower()
            body_name = body['BodyName']

            is_commission = ('commission' in body_type
                             or body_name in {'Airport Advisory Committee',
                                              'Election Commission',
                                              'Building Board of Appeals',
                                              'Taxicab Board',
                                              "Employees' Retirement System Board of Trustees"})

            if body_type == 'council committee':
                o = Organization(body_name,
                                 classification='committee',
                                 parent_id={'name': 'Ann Arbor City Council'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

            elif is_commission:
                o = Organization(body_name,
                                 classification='commission')

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

            elif 'component unit' in body_type or 'community services area' in body_type:
                o = Organization(body_name,
                                 classification='corporation')

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

            else:
                print(body)
                continue

            yield o
