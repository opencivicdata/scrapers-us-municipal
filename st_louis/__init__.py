# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .people import StLouisPersonScraper
from .bills import StLouisBillScraper


class StLouis(Jurisdiction):
    division_id = "ocd-division/country:us/state:mo/place:st_louis"

    # FIXME
    # Do we need jurisdiction_id? pupa did not auto-generate this field 
    # like division_id, I made it myself.
    # And is this the correct id? or should it be 
    # .../place:st_louis/council ? or .../place:st_louis/government ?
    jurisdiction_id = "ocd-jurisdiction/country:us/state:mo/place:st_louis"
    
    classification = "legislature"
    name = "St. Louis city Board of Aldermen"
    url = "https://www.stlouis-mo.gov/government/departments/aldermen/"
    scrapers = {
        "people": StLouisPersonScraper,
        "bills":  StLouisBillScraper
    }

    WARD_COUNT = 28

    def get_organizations(self):
        yield self.board_of_aldermen()

    def board_of_aldermen(self):
        org = Organization(name="St Louis Board of Aldermen", 
                           classification="legislature")
        # add a post for each Ward
        for ward_num in range(1, self.WARD_COUNT + 1):
            org.add_post(label="Ward {} Alderman".format(ward_num),
                         role="Alderman")
        yield org


    # TODO better way of doing this?
    legislative_sessions = [
        { "identifier": "2015-2016",
          "name": "2015-2016 Regular Session",
          "start_date": "2015-04-20",
          "end-date": "2016-04-17"
        },
        { "identifier": "2014-2015",
          "name": "2014-2015 Regular Session",
          "start_date": "2014-04-14",
          "end-date": "2015-04-20"
        },
        { "identifier": "2013-2014",
          "name": "2013-2014 Regular Session",
          "start_date": "2013-04-15",
          "end-date": "2014-04-07"
        },
        { "identifier": "2012-2013",
          "name": "2012-2013 Regular Session",
          "start_date": "2012-04-16",
          "end-date": "2013-04-08"
        },
        { "identifier": "2011-2012",
          "name": "2011-2012 Regular Session",
          "start_date": "2011-04-18",
          "end-date": "2012-04-09"
        },
        { "identifier": "2010-2011",
          "name": "2010-2011 Regular Session",
          "start_date": "2010-04-19",
          "end-date": "2011-04-11"
        }
    ]


