# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person
from .events import MiamidadeEventScraper
from .bills import MiamidadeBillScraper
from .people import MiamidadePersonScraper

import datetime


class Miamidade(Jurisdiction):
    division_id = "ocd-division/country:us/state:fl/county:miami-dade"
    classification = "legislature"
    name = "Miami-Dade County Government"
    url = "http://miamidade.gov/wps/portal/Main/government"
    parties = []

    scrapers = {
        "events": MiamidadeEventScraper,
        "bills": MiamidadeBillScraper,
        "people": MiamidadePersonScraper,
    }

    legislative_sessions = [{"identifier":"2014",
            "name":"2014 Regular Session",
            "start_date": "2014-11-20",
            "end_date": "2016-11-20"},
            ]


    def get_organizations(self):
        org = Organization(name="Miami-Dade County Commission",
            classification="legislature")
        
        for x in range(1,14):
            org.add_post(label="District {dist} Commissioner".format(dist=x),
                role="Commissioner",
                division_id=self.division_id)
        
        yield org

        mayor = Organization('Office of the Mayor', classification='executive')
        yield mayor

        mayorPers = Person(name="Carlos A. Giménez",
                       primary_org='executive',
                       role='Mayor',
                       primary_org_name='Office of the Mayor',
                       start_date=datetime.date(2011, 6, 28))

        mayorPers.add_source('Ernie')

        yield mayorPers


        clerk = Organization('Clerk of Courts', classification='executive')
        yield clerk

        clerkPers = Person(name="Harvey Ruvin",
                       primary_org='executive',
                       role='Clerk',
                       primary_org_name='Clerk of Courts')

        clerkPers.add_source('Ernie')
        
        yield clerkPers


        pa = Organization('Office of the Property Appraiser', classification='executive')
        yield pa

        paPers = Person(name="Pedro J. Garcia",
                       primary_org='executive',
                       role='Property Appraiser',
                       primary_org_name='Office of the Property Appraiser')

        paPers.add_source('Ernie')
        
        yield paPers
