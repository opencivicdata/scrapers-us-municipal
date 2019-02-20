import pytest

from pupa.scrape.bill import Bill

    
def test_is_restricted(scraper, matter, public_private_bill_data):
    '''
    Tests that `_is_restricted` returns the correct value, given
    a dict of matter values.
    '''
    field, value, assertion = public_private_bill_data
    matter[field] = value

    assert scraper._is_restricted(matter) == assertion


def test_scraper(scraper, matter, public_private_bill_data, mocker):
    '''
    Test that the scraper correctly assigns the value of 'restrict_view'
    to bill extras.
    '''
    field, value, assertion = public_private_bill_data
    matter[field] = value
    mocker.patch('lametro.LametroBillScraper.matter', return_value=matter)

    for bill in scraper.scrape(matter_ids='2017-0643'):
        if type(bill) == Bill:
            assert bill.extras['restrict_view'] == assertion
