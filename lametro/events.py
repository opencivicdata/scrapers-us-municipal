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

    def scrape(self) :
        for event, web_event in self.events():

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
                status = ''

            e = Event(event_name,
                      start_date=event["start"],
                      description='',
                      location_name=event["EventLocation"],
                      status=status)

            e.pupa_id = str(event['EventId'])

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
