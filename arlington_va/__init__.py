from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import EventScraper


class Arlington(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:va/place:arlington/council'
    name = 'Arlington County Board'
    url = 'http://www.arlingtonva.us/Departments/CountyBoard/CountyBoardMain.aspx'

    scrapers = {'people': PersonScraper, 'events': EventScraper}
