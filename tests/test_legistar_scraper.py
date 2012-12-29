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

@istest
def can_get_legislation_detail_using_summary_row():
  scraper = LegistarScraper('phila.legistar.com')
  summaries = scraper.searchLegislation('')
  first_summary = summaries.next()
  first_detail = scraper.expandLegislationSummary(first_summary)
  assert_equal(first_detail[0]['Title'], first_summary['Title'])

  scraper = LegistarScraper('chicago.legistar.com')
  summaries = scraper.searchLegislation('')
  first_summary = summaries.next()
  first_detail = scraper.expandLegislationSummary(first_summary)
  assert_equal(first_detail[0]['Title'], first_summary['Title'])

@istest
def parse_detail_keys():
  scraper = LegistarScraper('phila.legistar.com')
  summary = {'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1265815&GUID=97CBBF7C-A123-4808-9D50-A1E340BE5BC1'}
  detail = scraper.expandLegislationSummary(summary)
  assert_in(u'Version', detail[0].keys())
  assert_not_in(u'CITY COUNCIL', detail[0].keys())

@istest
def recognize_dates():
  scraper = LegistarScraper('phila.legistar.com')
  summaries = scraper.searchLegislation('')
  summary = summaries.next()
  import datetime
  assert_is_instance(summary['File Created'], datetime.datetime)
