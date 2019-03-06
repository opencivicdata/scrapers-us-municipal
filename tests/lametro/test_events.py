import pytest
import requests_mock
import requests
import re

from pupa.scrape.event import Event

@pytest.mark.parametrize('api_status_name,scraper_assigned_status', [
    ('Final', 'passed'), 
    ('Final Revised', 'passed'),
    ('Final 2nd Revised', 'passed'),
    ('Draft', 'confirmed'),
    ('Canceled', 'cancelled')
])
def test_status_assignment(event_scraper, 
                           api_event, 
                           web_event,
                           api_status_name,
                           scraper_assigned_status, 
                           mocker):
    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        matcher = re.compile('metro.legistar.com')
        m.get(matcher, json={}, status_code=200)

        api_event['EventAgendaStatusName'] = api_status_name

        mocker.patch('lametro.LametroEventScraper._merge_events', return_value=[(api_event, web_event)])

        for event in event_scraper.scrape():
            assert event.status == scraper_assigned_status