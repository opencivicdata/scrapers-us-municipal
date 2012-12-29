from nose.tools import *
from legistar_scraper import LegistarScraper

@istest
def default_legislation_and_calendar_uris():
  config = {'hostname': 'synecdoche.legistar.com'}
  scraper = LegistarScraper(config)
  assert_equal(scraper._legislation_uri, 'http://synecdoche.legistar.com/Legislation.aspx')
  assert_equal(scraper._calendar_uri, 'http://synecdoche.legistar.com/Calendar.aspx')

@istest
def supports_advanced_initial_search_form():
  config = {'hostname': 'chicago.legistar.com'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')

@istest
def supports_simple_initial_search_form():
  config = {'hostname': 'phila.legistar.com'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')

@istest
def can_get_legislation_detail_using_summary_row():
  config = {'hostname': 'phila.legistar.com'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  first_summary = summaries.next()
  first_detail = scraper.expandLegislationSummary(first_summary)
  assert_equal(first_detail[0]['Title'], first_summary['Title'])

  config = {'hostname': 'chicago.legistar.com'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  first_summary = summaries.next()
  first_detail = scraper.expandLegislationSummary(first_summary)
  assert_equal(first_detail[0]['Title'], first_summary['Title'])

@istest
def parse_detail_keys():
  config = {'hostname': 'phila.legistar.com'}
  scraper = LegistarScraper(config)
  summary = {'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1265815&GUID=97CBBF7C-A123-4808-9D50-A1E340BE5BC1'}
  detail = scraper.expandLegislationSummary(summary)
  assert_in(u'Version', detail[0].keys())
  assert_not_in(u'CITY COUNCIL', detail[0].keys())

@istest
def recognize_dates():
  config = {'hostname': 'phila.legistar.com', 'date_format': '%m/%d/%Y'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  summary = summaries.next()
  import datetime
  assert_is_instance(summary['File Created'], datetime.datetime)

@istest
def ignore_dates_when_no_date_format():
  config = {'hostname': 'phila.legistar.com'}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  summary = summaries.next()
  import datetime
  assert_not_is_instance(summary['File Created'], datetime.datetime)
