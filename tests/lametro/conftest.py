import pytest

from lametro import LametroBillScraper


@pytest.fixture(scope='module')
def scraper():
    scraper = LametroBillScraper(datadir='', jurisdiction='ocd-division/test')
    return scraper

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