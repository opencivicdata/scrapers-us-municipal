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

@pytest.mark.parametrize('item_sequence,should_error', [
    (12, True),
    (11, False),
])
def test_sequence_duplicate_error(event_scraper,
                                  api_event, 
                                  web_event,
                                  event_agenda_item,
                                  item_sequence,
                                  should_error,
                                  mocker):
    with requests_mock.Mocker() as m:
        matcher = re.compile('webapi.legistar.com')
        m.get(matcher, json={}, status_code=200)

        matcher = re.compile('metro.legistar.com')
        m.get(matcher, json={}, status_code=200)

        api_event['event_details'] = [{'note': 'web', 
                                      'url': 'https://metro.legistar.com/MeetingDetail.aspx?ID=642118&GUID=F19B2133-928C-4390-9566-C293C61DC89A&Options=info&Search='}]
        
        event_agenda_item_b = event_agenda_item.copy()
        event_agenda_item_b['EventItemAgendaSequence'] = item_sequence

        mocker.patch('lametro.LametroEventScraper._merge_events', return_value=[(api_event, web_event)])
        mocker.patch('lametro.LametroEventScraper.agenda', return_value=[event_agenda_item, event_agenda_item_b])

        if should_error:
            with pytest.raises(ValueError) as excinfo:
                for event in event_scraper.scrape():
                    assert 'An agenda has duplicate agenda items on the Legistar grid'\
                           .format(api_event['EventId'])\
                           in str(excinfo.value)

                    assert event['EventBodyName'] in str(excinfo.value)
        else:
            for event in event_scraper.scrape():
                assert len(event.agenda) == 2
