from nose.tools import *
from legistar.scraper import LegistarScraper

try:
  from nose.tools import assert_in, assert_not_in
except ImportError:
  def assert_in(a, b):
    assert a in b, '%r was not in %r' % (a, b)
  def assert_not_in(a, b):
    assert a not in b, '%r was in %r' % (a, b)
  def assert_is_none(a):
    assert a is None, '%r was not None' % (a,)
  def assert_is_instance(a, b):
    assert isinstance(a, b), '%r was not an instance of %r' % (a,b)
  def assert_greater(a, b):
    assert a > b, '%r was not greater than %r' % (a,b)


@istest
def default_legislation_and_calendar_uris():
  config = {'hostname': 'synecdoche.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  assert_equal(scraper._legislation_uri, 'http://synecdoche.legistar.com/Legislation.aspx')
  assert_equal(scraper._calendar_uri, 'http://synecdoche.legistar.com/Calendar.aspx')

@istest
def supports_advanced_initial_search_form():
  config = {'hostname': 'chicago.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')

@istest
def supports_simple_initial_search_form():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    fail('no legislation found')

@istest
def paging_through_results():
  config = {'hostname': 'chicago.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  summaries = list(scraper.searchLegislation('pub'))
  # Making summaries a list forces the scraper to iterate completely through
  # the generator
  for s in summaries:
    print s['Record #']
  assert_greater(len(summaries), 100)


@istest
def parse_detail_keys():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  summary = {'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1265815&GUID=97CBBF7C-A123-4808-9D50-A1E340BE5BC1'}
  detail = scraper.expandLegislationSummary(summary)
  assert_in(u'Version', detail[0].keys())
  assert_not_in(u'CITY COUNCIL', detail[0].keys())

@istest
def recognize_dates():
  config = {'hostname': 'phila.legistar.com',
            'date_format': '%m/%d/%Y',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  summary = summaries.next()
  import datetime
  assert_is_instance(summary['File Created'], datetime.datetime)

@istest
def attachments_list():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1243262&GUID=01021C5A-3624-4E5D-AA32-9822D1F5DA29&Options=ID|Text|&Search='})
  # Attachments value should be a list
  assert_is_instance(detail[0]['Attachments'], list)

@istest
def no_attachments_list():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1254964&GUID=AF8A4E91-4DF6-41A2-80B4-EFC94A2AFF89&Options=ID|Text|&Search='})
  # Legislation with no attachments should have no attachment key
  assert_not_in('Attachments', detail[0])

@istest
def link_address_is_href():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)

  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a href="http://www.google.com"></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_equal(address, 'http://www.google.com')

@istest
def link_address_is_onclick():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)

  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a onclick="radopen(\'http://www.google.com\');"></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_equal(address, 'http://www.google.com')

@istest
def link_address_is_none():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)

  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_is_none(address)

@istest
def history_row_url():
  config = {'hostname': 'chicago.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://chicago.legistar.com/LegislationDetail.aspx?ID=1255978&GUID=8051C1E6-DED6-433B-AC9A-0FE436051C9F&Options=Advanced&Search='})
  assert_equal(detail[1][0]['URL'], 'http://chicago.legistar.com/HistoryDetail.aspx?ID=6534991&GUID=253AA818-B592-4594-8237-0A617AA41766')

@istest
def can_get_history_detail_using_summary_row():
  config = {'hostname': 'phila.legistar.com',
            'fulltext' : True}
  scraper = LegistarScraper(config)
  legislation_summary = {'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1236768&GUID=EB92A4C2-469A-4D73-97C0-A620BBDDD5BE&Options=ID|Text|&Search='}
  legislation_details = scraper.expandLegislationSummary(legislation_summary)
  history_summary = legislation_details[1][2]

  attrs, votes = scraper.expandHistorySummary(history_summary)
  ayes = [vote for vote in votes if vote['Vote'] == 'Ayes']
  assert_equal(len(ayes), 14)
  assert_equal(attrs['Result'], 'Pass')

