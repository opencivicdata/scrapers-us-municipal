# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person

from .events import PittsburghEventScraper
from .people import PittsburghPersonScraper
from .bills import PittsburghBillScraper
from .vote_events import PittsburghVoteEventScraper

import datetime


class Pittsburgh(Jurisdiction):
    division_id = "ocd-division/country:us/state:pa/place:pittsburgh"
    classification = "legislature"
    name = "Pittsburgh City Council"
    url = "https://pittsburgh.legistar.com"
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        "events": PittsburghEventScraper,
        "people": PittsburghPersonScraper,
        "bills": PittsburghBillScraper,
    }

    legislative_sessions = [{"identifier": "2019",
            "name": "2019 Session",
            "start_date": "2019-01-01",
            "end_date": "2019-12-31"},
            {"identifier": "2018",
            "name": "2018 Session",
            "start_date": "2018-01-01",
            "end_date": "2018-12-31"},
            {"identifier": "2017",
            "name": "2017 Session",
            "start_date": "2017-01-01",
            "end_date": "2017-12-31"},
            {"identifier": "2016",
            "name": "2016 Session",
            "start_date": "2016-01-01",
            "end_date": "2016-12-31"},
            {"identifier": "2015",
            "name": "2015 Session",
            "start_date": "2015-01-01",
            "end_date": "2015-12-31"}
            ]

    def get_organizations(self):
        org = Organization(name="Pittsburgh City Council", classification="legislature")
        for x in range(1, 9):
            org.add_post(
                "District {}".format(x),
                "Councilmember",
                division_id='ocd-division/country:us/state:pa/place:pittsburgh/council_district:{}'.format(x))

        yield org

        city = Organization('City of Pittsburgh', classification='executive')
        city.add_post('Mayor', 'Mayor', division_id='ocd-division/country:us/state:pa/place:pittsburgh')
        city.add_post('City Clerk', 'City Clerk', division_id='ocd-division/country:us/state:pa/place:pittsburgh')

        yield city

        peduto = Person(name="Peduto, Bill")
        peduto.add_term('Mayor',
                        'executive',
                        start_date=datetime.date(2014, 1, 6),
                        appointment=True)
        peduto.add_source('http://pittsburghpa.gov/mayor/mayor-profile')

        ravenstahl = Person(name="Ravenstahl, Luke")
        ravenstahl.add_term('Mayor',
                            'executive',
                            start_date=datetime.date(2006, 9, 1),
                            end_date=datetime.date(2014, 1, 5),
                            appointment=True)
        ravenstahl.add_source('')

        pree = Person(name="Pree, Brenda")
        pree.add_term('City Clerk',
                      'executive',
                      start_date=datetime.date(2017, 8, 29),
                      appointment=True)
        pree.add_source('http://pittsburghpa.gov/clerk/clerk-bio')

        doheny = Person(name="Doheny, Mary Beth")
        doheny.add_term('City Clerk',
                        'executive',
                        start_date=datetime.date(2014, 3, 18),
                        end_date=datetime.date(2017, 8, 28),
                        appointment=True)
        doheny.add_source('')
