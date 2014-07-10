from pupa.scrape import Jurisdiction

from granicus.pupa.events import make_event_scraper


class StateCollege(Jurisdiction):
    division_id = 'ocd-division/country:us/state:pa/place:state_college'
    name = 'State College'
    url =  'http://www.statecollegepa.us/'
    classification = "government"

    scrapers = {
        # XXX: The server is giving us 500 errors...
        # "events": make_event_scraper("statecollegepa"),
    }
