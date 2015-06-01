from pupa.scrape import Scraper
from pupa.models import Event

import requests, os
from dateutil.parser import parse as dt_parse

class ChattanoogaEventsScraper(Scraper):

    def __init__(self, *args, **kwargs):
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        assert self.api_key, 'You must set the environment variable GOOGLE_API_KEY'

        self.calendar_id = 'i53pg4qp4b4ba5ud5u5eubeci4@group.calendar.google.com'

        super(ChattanoogaEventsScraper, self).__init__(*args, **kwargs)

    def get_events(self):
        calendar_url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events?key=%s' % (self.calendar_id, self.api_key)

        response = requests.get(calendar_url)
        assert response.status_code == 200, 'Request failed'

        data = response.json()
        timezone = data.get('timeZone')
        items = data.get('items', [])
        for item in items:

            if item.get('created'):
                item['created'] = dt_parse(item['created'])

            if item.get('start') and item.get('start').get('dateTime'):
                item['start']['dateTime'] = dt_parse(item['start']['dateTime'])
            else:
                continue # skip to the next one because start time is required

            if item.get('end') and item.get('end').get('dateTime'):
                item['end']['dateTime'] = dt_parse(item['end']['dateTime'])

            if not item.get('summary') and item.get('description'):
                item['summary'] = item.get('description')
            elif not item.get('summary'):
                continue # skip because name is required

            try:
                event = Event(
                    name = item.get('summary'),
                    when = item.get('start').get('dateTime'),
                    location = item.get('location', ''),
                    description = item.get('description', item.get('summary')),
                    end = item.get('end').get('dateTime') if item.get('end') and item.get('end').get('dateTime') else None,
                    status = item.get('status', 'confirmed'),
                )
                event.add_source(item.get('htmlLink', 'http://www.google.com/calendar/embed?src=%s' % self.calendar_id))
                event.validate()
            except:
                continue # there was a validation error
            yield event