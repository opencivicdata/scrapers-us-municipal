import datetime

from pupa.scrape import Jurisdiction, Organization, Person

from .bills import ChicagoBillScraper
from .events import ChicagoEventsScraper
from .people import ChicagoPersonScraper


class Chicago(Jurisdiction):
    division_id = "ocd-division/country:us/state:il/place:chicago"
    classification = "government"
    name = "Chicago City Government"
    url = "https://chicago.legistar.com/"
    parties = [{"name": "Democrats"}]

    scrapers = {
        "people": ChicagoPersonScraper,
        "events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }

    legislative_sessions = [
        {
            "identifier": "2019",
            "name": "2019 Regular Session",
            "start_date": "2019-05-20",
            "end_date": "2023-05-19",
        },
        {
            "identifier": "2015",
            "name": "2015 Regular Session",
            "start_date": "2015-05-18",
            "end_date": "2019-05-19",
        },
        {
            "identifier": "2011",
            "name": "2011 Regular Session",
            "start_date": "2011-05-18",
            "end_date": "2015-05-17",
        },
        {
            "identifier": "2007",
            "name": "2007 Regular Session",
            "start_date": "2007-05-18",
            "end_date": "2011-05-17",
        },
    ]

    def get_organizations(self):
        org = Organization(name="Chicago City Council", classification="legislature")
        for x in range(1, 51):
            org.add_post(
                "Ward {}".format(x),
                "Alderman",
                division_id="ocd-division/country:us/state:il/place:chicago/ward:{}".format(
                    x
                ),
            )

        yield org

        city = Organization("City of Chicago", classification="executive")
        city.add_post(
            "Mayor",
            "Mayor",
            division_id="ocd-division/country:us/state:il/place:chicago",
        )
        city.add_post(
            "City Clerk",
            "City Clerk",
            division_id="ocd-division/country:us/state:il/place:chicago",
        )

        yield city

        daley = Person(name="Daley, Richard M.")
        daley.add_term(
            "Mayor",
            "executive",
            start_date=datetime.date(1989, 4, 24),
            end_date=datetime.date(2011, 5, 16),
            appointment=True,
        )
        daley.add_source("https://chicago.legistar.com/People.aspx")
        yield daley

        emanuel = Person(name="Emanuel, Rahm")
        emanuel.add_term(
            "Mayor",
            "executive",
            start_date=datetime.date(2011, 5, 16),
            appointment=True,
        )
        emanuel.add_source("https://chicago.legistar.com/People.aspx")
        yield emanuel

        lightfoot = Person(name="Lightfoot, Lori E.")
        lightfoot.add_term(
            "Mayor",
            "executive",
            start_date=datetime.date(2019, 5, 20),
            appointment=True,
        )
        lightfoot.add_source("https://chicago.legistar.com/People.aspx")
        yield lightfoot

        mendoza = Person(name="Mendoza, Susana A.")
        mendoza.add_term(
            "City Clerk",
            "executive",
            start_date=datetime.date(2011, 5, 16),
            end_date=datetime.date(2016, 12, 4),
            appointment=True,
        )

        mendoza.add_source("https://chicago.legistar.com/People.aspx")
        yield mendoza

        valle = Person(name="Del Valle, Miguel")
        valle.add_term(
            "City Clerk",
            "executive",
            start_date=datetime.date(2006, 12, 1),
            end_date=datetime.date(2011, 5, 16),
            appointment=True,
        )

        valle.add_source("https://chicago.legistar.com/People.aspx")
        yield valle

        valencia = Person(name="Valencia, Anna M.")
        valencia.add_term(
            role="City Clerk",
            org_classification="executive",
            start_date=datetime.date(2017, 1, 25),
            end_date=datetime.date(2019, 5, 20),
            appointment=True,
        )

        valencia.add_source("https://chicago.legistar.com/People.aspx")
        yield valencia
