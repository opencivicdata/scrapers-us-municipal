# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person

from .events import PittsburghEventsScraper
from .people import PittsburghPersonScraper
from .bills import PittsburghBillScraper

import datetime


class Pittsburgh(Jurisdiction):
    division_id = "ocd-division/country:us/state:pa/place:pittsburgh"
    classification = "government"
    name = "Pittsburgh City Government"
    timezone = "America/New_York"
    url = "https://pittsburgh.legistar.com"

    scrapers = {
        "events": PittsburghEventsScraper,
        "people": PittsburghPersonScraper,
        "bills": PittsburghBillScraper,
    }

    # legislative_sessions = []

    # def get_legislative_sessions(self):
    #     for year in range(2001, 2030):
    #         legislative_sessions.append({"identifier": str(year),
    #                 "name": str(year) + ' Session',
    #                 "start_date": str(year) + '-01-01',
    #                 "end_date": str(year) + '-12-31'})


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
            "end_date": "2015-12-31"},
            {"identifier": "2014",
            "name": "2015 Session",
            "start_date": "2014-01-01",
            "end_date": "2014-12-31"},
            {"identifier": "2013",
            "name": "2013 Session",
            "start_date": "2013-01-01",
            "end_date": "2013-12-31"},
            {"identifier": "2012",
            "name": "2012 Session",
            "start_date": "2012-01-01",
            "end_date": "2012-12-31"},
            {"identifier": "2011",
            "name": "2011 Session",
            "start_date": "2011-01-01",
            "end_date": "2011-12-31"},
            {"identifier": "2015",
            "name": "2010 Session",
            "start_date": "2010-01-01",
            "end_date": "2010-12-31"},
            {"identifier": "2009",
            "name": "2009 Session",
            "start_date": "2009-01-01",
            "end_date": "2009-12-31"},
            {"identifier": "2008",
            "name": "2008 Session",
            "start_date": "2008-01-01",
            "end_date": "2008-12-31"},
            {"identifier": "2007",
            "name": "2007 Session",
            "start_date": "2007-01-01",
            "end_date": "2007-12-31"},
            {"identifier": "2008",
            "name": "2006 Session",
            "start_date": "2006-01-01",
            "end_date": "2006-12-31"},
            {"identifier": "2005",
            "name": "2005 Session",
            "start_date": "2005-01-01",
            "end_date": "2005-12-31"},
            {"identifier": "2004",
            "name": "2004 Session",
            "start_date": "2004-01-01",
            "end_date": "2004-12-31"},
            {"identifier": "2003",
            "name": "2003 Session",
            "start_date": "2003-01-01",
            "end_date": "2003-12-31"},
            {"identifier": "2008",
            "name": "2002 Session",
            "start_date": "2002-01-01",
            "end_date": "2002-12-31"},
            {"identifier": "2008",
            "name": "2001 Session",
            "start_date": "2001-01-01",
            "end_date": "2001-12-31"},
            ]

    def get_organizations(self):
        org = Organization(name="Pittsburgh City Council", classification="legislature")
        for x in range(1, 10):
            org.add_post(
                "District {}".format(x),
                "Councilmember",
                division_id='ocd-division/country:us/state:pa/place:pittsburgh/council_district:{}'.format(x))

        yield org

        standing_committee = Organization(name='Standing Committee', classification='committee')

        standing_committee.add_source('http://pittsburghpa.gov/council/standing-committees', note='web')

        yield standing_committee


        mayor = Organization(name='Mayor', classification='executive')

        mayor.add_source('http://pittsburghpa.gov/mayor/index.html', note='web')

        yield mayor

        city_clerk = Organization(name='City Clerk', classification='department')
        city_clerk.add_post('City Clerk', 'City Clerk', division_id='ocd-division/country:us/state:pa/place:pittsburgh')
        city_clerk.add_source('http://pittsburghpa.gov/clerk/', note='web')

        yield city_clerk

        pree = Person(name="Brenda Pree")
        pree.add_term('City Clerk',
                      'department',
                      start_date=datetime.date(2017, 8, 29),
                      appointment=True)
        pree.add_source('http://pittsburghpa.gov/clerk/clerk-bio')

        yield pree

        doheny = Person(name="Mary Beth Doheny")
        doheny.add_term('City Clerk',
                        'department',
                        start_date=datetime.date(2014, 3, 18),
                        end_date=datetime.date(2017, 8, 28),
                        appointment=True)
        doheny.add_source('http://pittsburghpa.gov')

        yield doheny

        all_members = Person(name="All Members")
        all_members.add_term('City Council',
                              'legislature',
                              start_date=datetime.date(1816, 3, 18))
        all_members.add_source('http://pittsburghpa.gov/council/index.html')

        yield all_members


