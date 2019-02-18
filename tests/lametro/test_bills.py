import pytest

from pupa.scrape.bill import Bill

@pytest.mark.parametrize('field,value,assertion', [
    ('MatterRestrictViewViaWeb', False, False),
    ('MatterRestrictViewViaWeb', True, True),
    ('MatterStatusName', 'Draft', True),
    ('MatterStatusName', 'Passed', False),
    ('legistar_url', None, True),
])
def test_is_restricted(scraper, matter, field, value, assertion):
    '''
    Unit test for `_is_restricted` function on bill scraper.
    This function accepts as an argument a dict of matter values.
    '''
    matter[field] = value

    assert scraper._is_restricted(matter) == assertion

@pytest.mark.parametrize('field,value,assertion', [
    ('MatterRestrictViewViaWeb', True, True),
    ('MatterRestrictViewViaWeb', False, False),
    # ('MatterRestrictViewViaWeb', True),
    # ('MatterStatusName', 'Draft'),
    # ('MatterStatusName', 'Passed'),
    # ('legistar_url', None),
])
def test_scraper(scraper, matter, field, value, assertion, mocker):
    matter[field] = value
    mocker.patch('lametro.LametroBillScraper.matter', return_value=matter)

    for bill in scraper.scrape(matter_ids='2017-0643'):
        if type(bill) == Bill:
            assert bill.extras['restrict_view'] == assertion
