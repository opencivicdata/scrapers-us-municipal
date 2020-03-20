import pytest
import datetime

from lametro import LametroBillScraper, LametroEventScraper


@pytest.fixture(scope='module')
def bill_scraper():
    scraper = LametroBillScraper(datadir='', jurisdiction='ocd-division/test')
    return scraper

@pytest.fixture(scope='module')
def event_scraper():
    scraper = LametroEventScraper(datadir='', jurisdiction='ocd-division/test')
    return scraper

@pytest.fixture
def api_event():
    '''
    Dictionary with pertinent info for an event.
    '''
    event = {'EventLastModifiedUtc': '2018-10-04T18:45:31.123',
             'status': 'passed',
             'EventVideoStatus': 'Public',
             'EventMinutesFile': None, 
             'EventAgendaLastPublishedUTC': '2019-02-22T23:50:26.483',
             'EventMinutesStatusName': 'Draft',
             'EventAgendaFile': 'http://metro.legistar1.com/metro/meetings/2019/2/1473_A_Board_of_Directors_-_Regular_Board_Meeting_19-02-28_Agenda.pdf',
             'EventBodyId': 138, 
             'audio': [], 
             'EventGuid': '57DC7258-0E6D-42CA-BB9A-717FCC96E436',
             'EventBodyName': 'Board of Directors - Regular Board Meeting',
             'event_details': [], 
             'EventItems': [], 
             'EventRowVersion': 'AAAAAADdAQ0=',
             'EventDate': '2019-02-28T00:00:00',
             'EventId': 1473, 
             'EventLocation': 'One Gateway Plaza, Los Angeles, CA 90012',
             'SAPEventId': 1535, 
             'EventAgendaStatusName': 'Final',
             'SAPEventGuid': '8962CCBC-5E42-4B3B-91DA-6178D507079C',
             'start': datetime.datetime(2019, 2, 28, 9, 30),
             'EventInSiteURL': '', 
             'EventTime': '9:30 AM'}

    return event

@pytest.fixture
def web_event():
    '''
    Dictionary with pertinent info for a web_event.
    Corresponds with the event fixture above.
    '''
    web_event = {'Meeting Details': {'label': 'Meeting\xa0details', 'url': ''}, 
                 'Meeting Time': '9:30 AM', 
                 'eComment': 'Not\xa0available', 
                 'Name': {'label': 'Board of Directors - Regular Board Meeting', 'url': ''}, 
                 'Meeting Date': '2/28/2019', 
                 'Audio': {'label': 'Audio', 'url': ''},
                 'Agenda': {'label': 'Agenda', 'url': ''}, 
                 'iCalendar': {'url': ''}, 
                 'Meeting Location': 'One Gateway Plaza, Los Angeles, CA 90012', 
                 'Recap/Minutes': 'Not\xa0available',
                 'Meeting video': 'Not\xa0available'}
    
    return web_event

@pytest.fixture
def event_agenda_item():
    '''
    Dictionary with pertinent info for an event item. 
    It corresponds with the above api_event.
    '''
    agenda_item = {'EventItemGuid': '57DC7258-0E6D-42CA-BB9A-717FCC96E436',
                   'EventItemEventId': 1473,
                   'EventItemRollCallFlag': 0,
                   'EventItemAgendaSequence': 12,
                   'EventItemMinutesSequence': 12,
                   'EventItemMatterFile': None,
                   'EventItemAgendaNumber': None,
                   'EventItemLastModifiedUtc': '2019-03-04T19:47:09.387',
                   'EventItemTitle': 'Adjournment'}

    return agenda_item

@pytest.fixture
def matter():
    '''
    Dictionary with pertinent info for a bill. Bill is public.
    '''
    matter = {'MatterAgendaDate': '2017-11-16T00:00:00', 
              'MatterName': None, 
              'MatterTypeName': 'Contract',
              'MatterId': 4450, 
              'MatterStatusName': 'Passed', 
              'MatterStatusId': 72, 
              'MatterBodyId': 172,
              'MatterVersion': '1', 
              'legistar_url': 'https://metro.legistar.com/LegislationDetail.aspx?ID=3210569&GUID=B1D413C9-1C1B-4B4A-B398-DBAEFE1885E0', 
              'MatterPassedDate': '2017-11-30T00:00:00', 
              'MatterBodyName': 'System Safety, Security and Operations Committee', 
              'MatterFile': '2017-0643',
              'MatterIntroDate': '2017-09-19T00:00:00',
              'MatterGuid': 'D0750C68-B1D1-4CE4-BC8A-A2EB64A68155',
              'MatterRestrictViewViaWeb': False,
              'MatterTitle': 'AUTHORIZE the Chief Executive Officer'}
    
    return matter

public_private_bill_data = [
    ('MatterRestrictViewViaWeb', False, False),
    ('MatterRestrictViewViaWeb', True, True),
    ('MatterBodyName', 'TO BE REMOVED', True),
    ('MatterStatusName', 'Draft', True),
    ('MatterStatusName', 'Passed', False),
    ('legistar_url', None, True),
]

@pytest.fixture(params=public_private_bill_data)
def public_private_bill_data(request):
    '''
    This parametrized fixture contains arguments for updating the values of a bill, namely:
    'MatterRestrictViewViaWeb', 'MatterStatusName', and 'legistar_url'.
    
    Changing these values also determines whether the bill should be 
    marked as having a 'restricted view,' i.e., private vs. public.
    '''
    return request.param