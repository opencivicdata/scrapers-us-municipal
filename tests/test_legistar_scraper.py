from nose.tools import *
from legistar_scraper import LegistarScraper

@istest
def default_legislation_and_calendar_uris():
  scraper = LegistarScraper('synecdoche.legistar.com')
  assert_equal(scraper._legislation_uri, 'http://synecdoche.legistar.com/Legislation.aspx')
  assert_equal(scraper._calendar_uri, 'http://synecdoche.legistar.com/Calendar.aspx')

@istest
def supports_advanced_initial_search_form():
  scraper = LegistarScraper('chicago.legistar.com')
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')

@istest
def supports_simple_initial_search_form():
  scraper = LegistarScraper('phila.legistar.com')
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')
