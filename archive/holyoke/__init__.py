# Copyright (c) Sunlight Foundation, 2014, under the terms of the BSD-3
# license, a copy of which is in the root level LICENSE file.
#
# This scraper was done at Hack for Western Mass, a huge shoutout
# to all the civic hackers and the Hack for Western Mass folks.

from pupa.scrape import Jurisdiction, Post, Organization
from .people import HolyokePersonScraper

NAME = "Holyoke City"


class Holyoke(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ma/place:holyoke'
    classification = 'government'
    name = NAME
    url = 'http://www.holyoke.org/elected-officials/'

    scrapers = {
        "people": HolyokePersonScraper
    }

    def get_organizations(self):
        # XXX: Add divison IDs
        org = Organization(name='Holyoke City Council',
                          classification='legislature')

        for x in [
            {"label": "Mayor", "role": "mayor",},
            {"label": "City Clerk", "role": "clerk",},
            {"label": "City Treasurer", "role": "treasurer",},
            {"label": "At Large", "role": "councilmember",},

            {"label": "Ward 1", "role": "councilmember"},
            {"label": "Ward 2", "role": "councilmember"},
            {"label": "Ward 3", "role": "councilmember"},
            {"label": "Ward 4", "role": "councilmember"},
            {"label": "Ward 5", "role": "councilmember"},
            {"label": "Ward 6", "role": "councilmember"},
            {"label": "Ward 7", "role": "councilmember"},
        ]:
            org.add_post(**x)

        yield org
