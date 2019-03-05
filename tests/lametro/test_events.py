import pytest
import requests_mock
import requests
import re

from pupa.scrape.event import Event

@pytest.mark.parametrize('status_name,status', [
    ('Final', 'passed'), 
    ('Final Revised', 'passed'),
    ('Final 2nd Revised', 'passed'),
    ('Draft', 'confirmed'),
    ('Canceled', 'cancelled')
])
def test_status_assignment(event_scraper, 
                           event, 
                           web_event,
                           status_name,
                           status, 
                           mocker):
    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        matcher = re.compile('metro.legistar.com')
        m.get(matcher, json={}, status_code=200)

        event['EventAgendaStatusName'] = status_name

        mocker.patch('lametro.LametroEventScraper._merge_events', return_value=[(event, web_event)])

        for event in event_scraper.scrape():
            assert event.status == status