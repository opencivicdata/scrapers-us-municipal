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

    def _pair_events(self, events):
        paired_events = []
        unpaired_events = []

        for incoming_event in events:
            try:
                partner_event, = [e for e in unpaired_events
                                  if incoming_event.is_partner(e)]
            except ValueError:
                unpaired_events.append(incoming_event)

            else:
                unpaired_events.remove(partner_event)
                paired_events.append(incoming_event)
                paired_events.append(partner_event)

        return paired_events, unpaired_events

    def _find_partner(self, event):

        results = list(self.search('/events/', 'EventId',
                                   event.partner_search_string))
        if results:
            partner, = results
            partner = LAMetroAPIEvent(partner)
            assert event.is_partner(partner)
            return partner

        elif event.is_spanish:
            raise ValueError("Can't find English companion for Spanish Event {}".format(event['EventId']))

        else:
            return None
        

    def api_events(self, *args, **kwargs):
        '''
        For meetings, Metro provides an English audio recording and a
        Spanish recording. Due to limitations with the InSite system,
        multiple audio recordings can't be associated with a single
        InSite event. So, Metro creates two InSite event entries for
        the same actual event, one Insite event entry has the English
        audio and the other has the Spanish Audio. The Spanish InSite
        event entry has the same name as the English event entry,
        except the name is suffixed with ' (SAP)'.

        We need to merge these companion events. In order to do that,
        we must ensure that if we scrape one member of pair, we also
        scrape its partner.

        This method subclasses the normal api_event method to ensure
        that we get both members of pairs.
        '''
        events = (LAMetroAPIEvent(event) for event
                  in super().api_events(*args, **kwargs))

        paired, unpaired = self._pair_events(events)

        yield from paired

        for unpaired_event in unpaired:
            yield unpaired_event

            partner_event = self._find_partner(unpaired_event)
            if partner_event is not None:
                yield partner_event

    def _merge_events(self, events):
        english_events = []
        spanish_events = []
        
        for event, web_event in events:
            if event.is_spanish:
                spanish_events.append((event, web_event))
            else:
                english_events.append((event, web_event))

        for event, web_event in english_events:
            
            matches = [spanish_web_event['Audio']
                       for spanish_event, spanish_web_event
                       in spanish_events
                       if event.is_partner(spanish_event)]
            if matches:
                spanish_audio, = matches
                event['audio'] = [web_event['Audio'], spanish_audio]
            else:
                event['audio'] = [web_event['Audio']]
                
        return english_events

    def scrape(self, window=None) :
        if window:
            n_days_ago = datetime.datetime.utcnow() - datetime.timedelta(float(window))
        else:
            n_days_ago = None

        events = self.events(n_days_ago)

        for event, web_event in self._merge_events(events):
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

            for audio in event['audio']:
                if audio != 'Not\xa0available':
                
                    try:
                        redirect_url = self.head(audio['url']).headers['Location']
                
                    except KeyError:
                        # In some cases, the redirect URL does not yet
                        # contain the location of the audio file. Skip
                        # these events, and retry on next scrape.
                        continue
                
                
                    e.add_media_link(note=audio['label'],
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
            

class LAMetroAPIEvent(dict):
    '''
    This classs if for adding methods to the event dict
    to faciliate maching events with their other-language
    partners
    '''

    @property
    def is_spanish(self):
        return self['EventBodyName'].endswith(' (SAP)')

    @property
    def _partner_name(self):
        if self.is_spanish:
            return self['EventBodyName'].rstrip(' (SAP)')
        else:
            return self['EventBodyName'] + ' (SAP)'

    def is_partner(self, other):
        return (self._partner_name == other['EventBodyName'] and
                self['EventDate'] == other['EventDate'] and
                self['EventTime'] == other['EventTime'])

    @property
    def partner_search_string(self):
        search_string = "EventBodyName eq '{}'".format(self._partner_name)
        search_string += " and EventDate eq datetime'{}'".format(self['EventDate'])
        search_string += " and EventTime eq '{}'".format(self['EventTime'])

        return search_string

    
