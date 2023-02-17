import datetime
import re

import pytest
import requests_mock
import requests

from pupa.scrape.bill import Bill


def test_unnamed_board_correspondences(bill_scraper, matter, mocker):
    '''
    Test that unrestricted, unnamed board correspondences are scraped and given
    a temporary name.
    '''
    matter_id = matter['MatterFile']
    matter['MatterTypeName'] = 'Board Correspondence'
    matter['MatterTitle'] = ''

    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        mocker.patch('lametro.LametroBillScraper.matter', return_value=matter)
        mocker.patch('lametro.LametroBillScraper.text', return_value='')
        mocker.patch(
            'lametro.LametroBillScraper._is_restricted',
            return_value=False
        )

        scrape_results = []
        for bill in bill_scraper.scrape(matter_ids=matter_id):
            if type(bill) == Bill:
                scrape_results.append(bill)

        assert (
            len(scrape_results) == 1
        ), "Should scrape unnamed board correspondences"
        assert (
            scrape_results[0].title
        ), "Should assign unnamed board correspondences temporary name"


def test_is_restricted(bill_scraper, matter, public_private_bill_data):
    '''
    Tests that `_is_restricted` returns the correct value, given
    a dict of matter values.
    '''
    field, value, assertion = public_private_bill_data
    matter[field] = value

    assert bill_scraper._is_restricted(matter) == assertion


def test_scraper(bill_scraper, matter, public_private_bill_data, mocker):
    '''
    Test that the scraper correctly assigns the value of 'restrict_view'
    to bill extras.
    '''
    field, value, assertion = public_private_bill_data
    matter[field] = value
    matter_id = matter['MatterFile']

    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        mocker.patch('lametro.LametroBillScraper.matter', return_value=matter)
        mocker.patch('lametro.LametroBillScraper.text', return_value='')

        for bill in bill_scraper.scrape(matter_ids=matter_id):
            if type(bill) == Bill:
                assert bill.extras['restrict_view'] == assertion


@pytest.mark.parametrize('intro_date,num_bills_scraped', [
    ('2018-09-19T00:00:00', 1),
    ('2017-07-01T00:00:00', 1),
    ('2016-07-01T00:00:00', 1),
    ('2016-06-30T00:00:00', 0),
    ('2015-07-01T00:00:00', 0),
    ('2014-07-01T00:00:00', 0),
])
def test_private_scrape_dates(bill_scraper, matter, intro_date, num_bills_scraped, mocker):
    '''
    Test that the scraper skips early private bills (i.e., introduced before
    the START_DATE_PRIVATE_SCRAPE timestamp) and also scrapes later ones.
    '''
    matter['MatterIntroDate'] = intro_date
    matter['MatterRestrictViewViaWeb'] = True
    matter_id = matter['MatterFile']

    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        mocker.patch('lametro.LametroBillScraper.matter', return_value=matter)
        mocker.patch('lametro.LametroBillScraper.text', return_value='')

        scrape_results = []
        for bill in bill_scraper.scrape(matter_ids=matter_id):
            if type(bill) == Bill:
                scrape_results.append(bill)

        assert len(scrape_results) == num_bills_scraped
