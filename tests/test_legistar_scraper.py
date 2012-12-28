from nose.tools import *
from legistar_scraper import LegistarScraper

@istest
def default_legislation_and_calendar_uris():
    scraper = LegistarScraper('synecdoche.legistar.com')
    assert_equal(scraper._legislation_uri, 'http://synecdoche.legistar.com/Legislation.aspx')
    assert_equal(scraper._calendar_uri, 'http://synecdoche.legistar.com/Calendar.aspx')
