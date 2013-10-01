from nose.tools import *
from legistar.scraper import LegistarScraper
from legistar.config import Config, DEFAULT_CONFIG
from BeautifulSoup import BeautifulSoup

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
  config = Config(hostname = 'synecdoche.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  assert_equal(scraper._legislation_uri, 'https://synecdoche.legistar.com/Legislation.aspx')
  assert_equal(scraper._calendar_uri, 'https://synecdoche.legistar.com/Calendar.aspx')

@istest
def supports_advanced_initial_search_form():
  config = Config(hostname = 'chicago.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    #fail('no legislation found')
    assert False

@istest
def supports_simple_initial_search_form():
  config = Config(hostname = 'phila.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  try:
    summaries.next()
  except StopIteration:
    #fail('no legislation found')
    assert False

@istest
def paging_through_legislation():
  config = Config(hostname = 'chicago.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  summaries = list(scraper.searchLegislation('pub'))
  # Making summaries a list forces the scraper to iterate completely through
  # the generator
  for s in summaries:
    print s['Record #']
  assert_greater(len(summaries), 100)


@istest
def parse_detail_keys():
  config = Config(hostname = 'phila.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  summary = {'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1265815&GUID=97CBBF7C-A123-4808-9D50-A1E340BE5BC1'}
  detail = scraper.expandLegislationSummary(summary)
  assert_in(u'Version', detail[0].keys())
  assert_not_in(u'CITY COUNCIL', detail[0].keys())

@istest
def recognize_dates():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False,
           date_format = '%m/%d/%Y',).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  summaries = scraper.searchLegislation('')
  summary = summaries.next()
  import datetime
  assert_is_instance(summary['File Created'], datetime.datetime)

@istest
def attachments_list():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1243262&GUID=01021C5A-3624-4E5D-AA32-9822D1F5DA29&Options=ID|Text|&Search='})
  # Attachments value should be a list
  assert_is_instance(detail[0]['Attachments'], list)

@istest
def attachments_list():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)

  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1243262&GUID=01021C5A-3624-4E5D-AA32-9822D1F5DA29&Options=ID|Text|&Search='})
  # Attachments value should be a list
  assert_not_equal(detail[0]['Attachments'][0]['fulltext'], '')

@istest
def attachments_list():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False, fulltext = False).defaults(DEFAULT_CONFIG)

  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1243262&GUID=01021C5A-3624-4E5D-AA32-9822D1F5DA29&Options=ID|Text|&Search='})
  # Attachments value should be a list
  assert_equal(detail[0]['Attachments'][0]['fulltext'], '')


@istest
def no_attachments_list():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)

  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://phila.legistar.com/LegislationDetail.aspx?ID=1254964&GUID=AF8A4E91-4DF6-41A2-80B4-EFC94A2AFF89&Options=ID|Text|&Search='})
  # Legislation with no attachments should have no attachment key
  assert_not_in('Attachments', detail[0])

@istest
def link_address_is_href():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)

  scraper = LegistarScraper(config)

  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a href="http://www.google.com"></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_equal(address, 'http://www.google.com')

@istest
def link_address_is_onclick():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)

  scraper = LegistarScraper(config)

  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a onclick="radopen(\'http://www.google.com\');"></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_equal(address, 'http://www.google.com')

@istest
def link_address_is_none():
  config = Config(hostname = 'phila.legistar.com',
           sponsor_links = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  from BeautifulSoup import BeautifulSoup
  link = BeautifulSoup('<html><a></a></html>').find('a')
  address = scraper._get_link_address(link)
  assert_is_none(address)

@istest
def history_row_url():
  config = Config(hostname = 'chicago.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  detail = scraper.expandLegislationSummary({'URL':'http://chicago.legistar.com/LegislationDetail.aspx?ID=1255978&GUID=8051C1E6-DED6-433B-AC9A-0FE436051C9F&Options=Advanced&Search='})
  assert_equal(detail[1][0]['Action Details']['url'], 'https://chicago.legistar.com/HistoryDetail.aspx?ID=6534991&GUID=253AA818-B592-4594-8237-0A617AA41766')

@istest
def can_get_history_detail_using_summary_row():
  config = Config(hostname = 'chicago.legistar.com',
            sponsor_links = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  legislation_summary = {'URL':'https://chicago.legistar.com/LegislationDetail.aspx?ID=1450228&GUID=97689689-D0EA-47A2-8474-09B3A71C221B&Options=Advanced&Search='}
  legislation_details = scraper.expandLegislationSummary(legislation_summary)
  print legislation_details

  history_summary = legislation_details[1][0]['Action Details']
  
  print history_summary

  attrs, votes = scraper.expandHistorySummary(history_summary)
  ayes = [vote for vote in votes if vote['Vote'] == 'Yea']
  assert_equal(len(ayes), 49)
  assert_equal(attrs['Result'], 'Pass')


@istest
def parse_sponsors():
  with open('tests/local/LegislationDetail.aspx?ID=1255978&GUID=8051C1E6-DED6-433B-AC9A-0FE436051C9F') as f :
    soup = BeautifulSoup(f)
  config = Config(hostname = 'chicago.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  legislation_details = scraper.parseLegislationDetail(soup)
  assert_equal(legislation_details[0]["Sponsors"][1], u'Moreno, Proco Joe')


@istest
def philly_sponsors():
  config = Config(hostname = 'phila.legistar.com',
            sponsor_links = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  legislation_summary = {'URL': 'http://phila.legistar.com/LegislationDetail.aspx?ID=1233260&GUID=DC103FB6-FF9D-4250-B0CE-111B80E8B80C'}
  legislation_details = scraper.expandLegislationSummary(legislation_summary)
  assert_equal(legislation_details[0]["Sponsors"][0], u'Councilmember DiCicco')

@istest
def chicago_topics():
  """Tests that scraper works for Chicago for legislation with and without topics"""
  config = Config(hostname = 'chicago.legistar.com').defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  legislation_with_topics = {'URL': 'http://chicago.legistar.com/LegislationDetail.aspx?ID=1319481&GUID=40B01792-C9D8-4E8C-BADE-2D27BFC8284D'}
  legislation_details = scraper.expandLegislationSummary(legislation_with_topics)

  print legislation_details[0]
  assert_equal(legislation_details[0]["Topics"], [u'PUBLIC WAY USAGE - Awnings'])

  legislation_no_topics = {'URL': 'http://chicago.legistar.com/LegislationDetail.aspx?ID=1429779&GUID=118DDF75-D698-4526-BA54-B560BB6CCB04'}
  legislation_details = scraper.expandLegislationSummary(legislation_no_topics)
  assert_equal(legislation_details[0]["Topics"], [])

@istest
def philly_topics():
  """Tests that scraper works for Philly legislation with and without topics"""
  config = Config(hostname = 'philly.legistar.com').defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  legislation_with_topics = {'URL': 'http://phila.legistar.com/LegislationDetail.aspx?ID=1433307&GUID=773A9C3F-ABA5-4D6C-B901-A9EEE3B1B8B0'}
  legislation_details = scraper.expandLegislationSummary(legislation_with_topics)
  assert_equal(legislation_details[0]["Topics"], [u'LIQUOR BY THE DRINK TAX', u'SCHOOL TAX AUTHORIZATION'])
  legislation_no_topics = {'URL': 'http://phila.legistar.com/LegislationDetail.aspx?ID=1426307&GUID=E9EC8885-0DDD-4B64-AB2D-EA0503284268'}
  legislation_details = scraper.expandLegislationSummary(legislation_no_topics)
  assert_equal(legislation_details[0]["Topics"], [])


# Members
@istest
def supports_fetching_council_members():
  config = Config(hostname = 'phila.legistar.com',
            fulltext = True).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  members = scraper.councilMembers()
  try:
    members.next()
  except StopIteration:
    fail('no council members found')

# Ann Arbor, MI has a healthy number of people for some reason (4 pages)
@istest
def paging_through_council_members():
  config = Config(hostname = 'a2gov.legistar.com', 
            fulltext = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  members = list(scraper.councilMembers(follow_links=False))
  assert_greater(len(members), 100)

# Calendar
@istest
def supports_fetching_calendar():
  config = Config(hostname = 'phila.legistar.com',
            fulltext = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  events = scraper.councilCalendar('all')
  try:
    events.next()
  except StopIteration:
    fail('no events found')

# testing pagination on Alexandria, VA since they only have ~150 events (2 pages)
@istest
def paging_through_calendar():
  config = Config(hostname = 'alexandria.legistar.com', 
            fulltext = False).defaults(DEFAULT_CONFIG)
  scraper = LegistarScraper(config)
  events = list(scraper.councilCalendar('all'))
  assert_greater(len(events), 100)