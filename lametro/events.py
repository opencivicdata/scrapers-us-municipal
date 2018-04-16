import datetime

import requests
from legistar.events import LegistarAPIEventScraper
from legistar.events import LegistarEventsScraper
from pupa.scrape import Scraper
from pupa.scrape import Event

class LametroEventScraper(LegistarAPIEventScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com/'
    EVENTSPAGE = "https://metro.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Los_Angeles"

    def _get_partner_event_name(self, event):
        '''
        Generate name of partner event by adding or removing the (SAP) suffix.
        '''
        event_name = event['EventBodyName']

        if event_name.endswith('(SAP)'):
            return event_name.rstrip('(SAP)')

        else:
            return '{} (SAP)'.format(event_name)

    def _sort_event_pair(self, pair):
        '''
        Given event pair like "Board of Directors" and "Board of Directors (SAP)",
        return tuple such that English event comes first.
        '''
        event_pair = sorted(pair, key=lambda x: x['EventBodyName'])
        return tuple(event_pair)

    def _pair_english_with_spanish_events(self, events):
        paired_events = []
        unpaired_events = []

        for incoming_event in events:
            partner_name = self._get_partner_event_name(incoming_event)

            try:
                partner_event, = [e for e in unpaired_events
                                  if e['EventBodyName'] == partner_name
                                  and all(e[k] == incoming_event[k] for k in ['EventDate', 'EventTime'])]

            except ValueError:
                unpaired_events.append(incoming_event)

            else:
                event_pair = self._sort_event_pair([incoming_event, partner_event])
                paired_events.append(event_pair)

        return paired_events, unpaired_events

    def api_events(self, *args, **kwargs):
        '''
        Return tuples of (English, Spanish) events. Events that cannot
        be found are None.
        '''
        events = list(super().api_events(*args, **kwargs))
        paired, unpaired = self._pair_english_with_spanish_events(events)

        yield from paired

        for unpaired_event in unpaired:
            partner_name = self._get_partner_event_name(unpaired_event)

            try:
                partner_event, = self.search(EventBodyName=partner_name,
                                             EventDate=unpaired_event['EventDate'],
                                             EventTime=unpaired_event['EventTime'])

            except ValueError:
                if unpaired_event['EventBodyName'].endswith('(SAP)'):
                    # TO-DO: Should we yield unpaired Spanish events?
                    yield (None, unpaired_event)

                else:
                    yield (unpaired_event, None)

            else:
                event_pair = self._sort_event_pair([unpaired_event, partner_event])
                yield event_pair

    def scrape(self, window=None) :
        if window:
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        else:
            n_days_ago = None
        for event, web_event in self.events(n_days_ago):

            body_name = event["EventBodyName"]

            if 'Board of Directors -' in body_name:
                body_name, event_name = [part.strip()
                                         for part
                                         in body_name.split('-')]
            else:
                event_name = body_name

            status_name = event['EventAgendaStatusName']
            if status_name == 'Draft':
                status = 'confirmed'
            elif status_name == 'Final':
                status = 'passed'
            elif status_name == 'Canceled':
                status = 'cancelled'
            else:
                status = 'tentative'

            e = Event(event_name,
                      start_date=event["start"],
                      description='',
                      location_name=event["EventLocation"],
                      status=status)

            e.pupa_id = str(event['EventId'])

            # Metro requires the EventGuid to build out MediaPlayer links
            e.extras = {'guid': event['EventGuid']}

            for item in self.agenda(event):
                agenda_item = e.add_agenda_item(item["EventItemTitle"])
                if item["EventItemMatterFile"]:
                    identifier = item["EventItemMatterFile"]
                    agenda_item.add_bill(identifier)

                if item["EventItemAgendaNumber"]:
                    # To the notes field, add the item number as given in the agenda minutes
                    note = "Agenda number, {}".format(item["EventItemAgendaNumber"])
                    agenda_item['notes'].append(note)

            e.add_participant(name=body_name,
                              type="organization")

            e.add_source(self.BASE_URL + '/events/{EventId}'.format(**event),
                         note='api')

            if event['EventAgendaFile']:
                e.add_document(note= 'Agenda',
                               url = event['EventAgendaFile'],
                               media_type="application/pdf")

            if event['EventMinutesFile']:
                e.add_document(note= 'Minutes',
                               url = event['EventMinutesFile'],
                               media_type="application/pdf")

            # Update 'e' with data from https://metro.legistar.com/Calendar.aspx, if that data exists.
            if web_event['Audio'] != 'Not\xa0available':

                try:
                    redirect_url = self.head(web_event['Audio']['url']).headers['Location']

                except KeyError:

                    # In some cases, the redirect URL does not yet contain the
                    # location of the audio file. Skip these events, and retry
                    # on next scrape.

                    continue


                e.add_media_link(note=web_event['Audio']['label'],
                                 url=redirect_url,
                                 media_type='text/html')

            if web_event['Recap/Minutes'] != 'Not\xa0available':
                e.add_document(note=web_event['Recap/Minutes']['label'],
                               url=web_event['Recap/Minutes']['url'],
                               media_type="application/pdf")

            if web_event['Meeting Details'] != 'Meeting\xa0details':
                if requests.head(web_event['Meeting Details']['url']).status_code == 200:
                    e.add_source(web_event['Meeting Details']['url'], note='web')
                else:
                    e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

            yield e
