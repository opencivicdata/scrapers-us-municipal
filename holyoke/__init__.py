# Copyright (c) Sunlight Foundation, 2014, under the terms of the BSD-3
# license, a copy of which is in the root level LICENSE file.
#
# This scraper was done at Hack for Western Mass, a huge shoutout
# to all the civic hackers and the Hack for Western Mass folks.

from pupa.scrape import Jurisdiction
from .people import HolyokePersonScraper


class Holyoke(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ma/place:holyoke'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ma/place:holyoke/government'
    name = 'Holyoke City'
    url = 'http://www.holyoke.org/elected-officials/'

    scrapers = {
        "people": HolyokePersonScraper
    }
