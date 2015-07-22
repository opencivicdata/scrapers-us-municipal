from legistar.bills import LegistarBillScraper
from pupa.scrape import Event
import datetime

class NYCBillScraper(LegistarBillScraper):
    LEGISLATION_URL = 'http://legistar.council.nyc.gov/Legislation.aspx'
    BASE_URL = 'http://legistar.council.nyc.gov/'
    TIMEZONE = "US/Eastern"

    def scrape(self):
        for page in self.searchLegislation(created_after=datetime.datetime(2015, 1, 1)) :
            for legislation_summary in self.parseSearchResults(page) :
                print(legislation_summary)

