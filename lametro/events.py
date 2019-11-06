import datetime
import logging

from legistar.events import LegistarAPIEventScraper
from pupa.scrape import Event, Scraper
from legistar.base import LegistarScraper


LOGGER = logging.getLogger(__name__)

class UnmatchedEventError(Exception):
    def __init__(self, events):
        message_format = "Can't find companion for Event {0} at {1} on {2} - {3} {4}"
        if type(events) is dict:
            message = message_format.format(events['EventId'], events['EventTime'], \
            events['EventDate'], EventInSiteURL['EventInSiteURL'], '')
        elif type(events) is list:
            message = ''
            for event in events:
                temp = message_format.format(event['EventId'], event['EventTime'], \
                            event['EventDate'], event['EventInSiteURL'], '\n')
                message += temp
        else:
            message = "Can't find companion event"

        super().__init__(message)

class LametroEventScraper(LegistarAPIEventScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com/'
    EVENTSPAGE = "https://metro.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Los_Angeles"

    def _pair_events(self, events):
        paired_events = []
        unpaired_events = {}

        for incoming_event in events:
            try:
                partner_event = unpaired_events[incoming_event.partner_key]
            except KeyError:
                unpaired_events[incoming_event.key] = incoming_event

            else:
                del unpaired_events[incoming_event.partner_key]
                paired_events.append(incoming_event)
                paired_events.append(partner_event)

        return paired_events, unpaired_events.values()

    def _find_partner(self, event):
        '''
        Attempt to find other-language partner of an
        event. Sometimes English events won't have Spanish
        partners, but every Spanish event should have an
        English partner.
        '''
        results = list(self.search('/events/', 'EventId',
                                   event.partner_search_string))
        if results:
            partner, = results
            partner = LAMetroAPIEvent(partner)
            assert event.is_partner(partner)
            return partner

        elif event.is_spanish:
            raise UnmatchedEventError(event)

        else:
            return None

    def api_events(self, *args, **kwargs):
        '''
        For meetings, Metro provides an English audio recording and
        sometimes a Spanish audio translation. Due to limitations with
        the InSite system, multiple audio recordings can't be
        associated with a single InSite event. So, Metro creates two
        InSite event entries for the same actual event, one with the
        English audio and the other with the Spanish audio. The Spanish
        InSite event entry has the same name as the English event entry,
        except the name is suffixed with ' (SAP)'.

        We need to merge these companion events. In order to do that,
        we must ensure that if we scrape one member of a pair, we also
        scrape its partner.

        This method subclasses the normal api_event method to ensure
        that we get both members of pairs.
        '''
        partial_scrape = kwargs.get('since_datetime', False)

        events = (LAMetroAPIEvent(event) for event
                  in super().api_events(*args, **kwargs))

        paired, unpaired = self._pair_events(events)

        yield from paired

        for unpaired_event in unpaired:
            yield unpaired_event

            # if are not getting every single event then it's possible
            # that one member of a pair of English and Spanish will
            # be included in the our partial scrape and the other
            # member won't be. So, we try to find the partners for
            # unpaired events.

            # Spanish broadcasting didn't start until 5/16/2018, so we
            # check the date of any unpaired events to make sure they
            # should have a pair.

            spanish_start_date = datetime.datetime(2018, 5, 15, 0, 0, 0, 0)
            if partial_scrape:
                partner_event = self._find_partner(unpaired_event)
                if partner_event is not None:
                    yield partner_event
                elif unpaired_event['EventDate'] > spanish_start_date:
                    raise UnmatchedEventError(unpaired_event)

    def _merge_events(self, events):
        english_events = []
        spanish_events = {}

        for event, web_event in events:
            web_event = LAMetroWebEvent(web_event)

            if event.is_spanish:
                try:
                    assert event.key not in spanish_events
                except AssertionError:
                    raise AssertionError('{0} already exists as a key with a value of {1}'.format(event.key, spanish_events[event.key]))
                spanish_events[event.key] = (event, web_event)
            else:
                english_events.append((event, web_event))

        for event, web_event in english_events:
            event_details = []
            event_audio = []

            event_details.append({
                'url': web_event['Meeting Details']['url'],
                'note': 'web',
            })

            if web_event.has_audio:
                event_audio.append(web_event['Meeting video'])

            matches = spanish_events.pop(event.partner_key, None)

            if matches:
                spanish_event, spanish_web_event = matches

                event['SAPEventId'] = spanish_event['EventId']
                event['SAPEventGuid'] = spanish_event['EventGuid']

                event_details.append({
                    'url': spanish_web_event['Meeting Details']['url'],
                    'note': 'web (sap)',
                })

                if spanish_web_event.has_audio:
                    spanish_web_event['Meeting video']['label'] = 'Audio (SAP)'
                    event_audio.append(spanish_web_event['Meeting video'])

            event['event_details'] = event_details
            event['audio'] = event_audio

        try:
            assert not spanish_events  # These should all be merged with an English event.
        except AssertionError:
            unpaired_events = [event for event, _ in spanish_events.values()]
            raise UnmatchedEventError(unpaired_events)

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

            # Events can have an EventAgendaStatusName of "Final", "Final Revised",
            # and "Final 2nd Revised."
            # We classify these events as "passed."
            status_name = event['EventAgendaStatusName']
            if status_name.startswith('Final'):
                status = 'passed'
            elif status_name == 'Draft':
                status = 'confirmed'
            elif status_name == 'Canceled':
                status = 'cancelled'
            else:
                status = 'tentative'

            location = event["EventLocation"]

            if not location:
                # We expect some events to have no location. LA Metro would
                # like these displayed in the Councilmatic interface. However,
                # OCD requires a value for this field. Add a sane default.
                location = 'Not available'

            e = Event(event_name,
                      start_date=event["start"],
                      description='',
                      location_name=location,
                      status=status)

            e.pupa_id = str(event['EventId'])

            # Metro requires the EventGuid to build out MediaPlayer links.
            # Add both the English event GUID, and the Spanish event GUID if
            # it exists, to the extras dict.
            e.extras = {'guid': event['EventGuid']}

            legistar_api_url = self.BASE_URL + '/events/{0}'.format(event['EventId'])
            e.add_source(legistar_api_url, note='api')

            if event.get('SAPEventGuid'):
                e.extras['sap_guid'] = event['SAPEventGuid']

            if 'event_details' in event:
                # if there is not a meeting detail page on legistar
                # don't capture the agenda data from the API
                for item in self.agenda(event):
                    agenda_item = e.add_agenda_item(item["EventItemTitle"])
                    if item["EventItemMatterFile"]:
                        identifier = item["EventItemMatterFile"]
                        agenda_item.add_bill(identifier)

                    if item["EventItemAgendaNumber"]:
                        # To the notes field, add the item number as given in the agenda minutes
                        note = "Agenda number, {}".format(item["EventItemAgendaNumber"])
                        agenda_item['notes'].append(note)

                    # The EventItemAgendaSequence provides
                    # the line number of the Legistar agenda grid.
                    agenda_item['extras']['item_agenda_sequence'] = item['EventItemAgendaSequence']

                # Historically, the Legistar system has duplicated the EventItemAgendaSequence,
                # resulting in data inaccuracies. The scrape should fail in such cases, until Metro
                # cleans the data.
                item_agenda_sequences = [item['extras']['item_agenda_sequence'] for item in e.agenda]
                if len(item_agenda_sequences) != len(set(item_agenda_sequences)):
                    error_msg = 'An agenda has duplicate agenda items on the Legistar grid: \
                        {event_name} on {event_date} ({legistar_api_url}). \
                        Contact Metro, and ask them to remove the duplicate EventItemAgendaSequence.'

                    raise ValueError(error_msg.format(event_name=e.name,
                                                      event_date=e.start_date.strftime("%B %d, %Y"),
                                                      legistar_api_url=legistar_api_url))

            e.add_participant(name=body_name,
                              type="organization")

            if event.get('SAPEventId'):
                e.add_source(self.BASE_URL + '/events/{0}'.format(event['SAPEventId']),
                             note='api (sap)')

            if event['EventAgendaFile']:
                e.add_document(note= 'Agenda',
                               url = event['EventAgendaFile'],
                               media_type="application/pdf")

            if event['EventMinutesFile']:
                e.add_document(note='Minutes',
                               url=event['EventMinutesFile'],
                               media_type="application/pdf")

            elif web_event['Published minutes'] != 'Not\xa0available':
                e.add_document(note=web_event['Published minutes']['label'],
                               url=web_event['Published minutes']['url'],
                               media_type="application/pdf")

            for audio in event['audio']:
                try:
                    redirect_url = self.head(audio['url']).headers['Location']

                except KeyError:
                    # In some cases, the redirect URL does not yet
                    # contain the location of the audio file. Skip
                    # these events, and retry on next scrape.
                    continue

                # Sometimes if there is an issue getting the Spanish
                # audio created, Metro has the Spanish Audio link
                # go to the English Audio.
                #
                # Pupa does not allow the for duplicate media links,
                # so we'll ignore the the second media link if it's
                # the same as the first media link.
                #
                # Because of the way that the event['audio'] is created
                # the first audio link is always English and the
                # second is always Spanish
                e.add_media_link(note=audio['label'],
                                 url=redirect_url,
                                 media_type='text/html',
                                 on_duplicate='ignore')

            if event['event_details']:
                for link in event['event_details']:
                    e.add_source(**link)
            else:
                e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

            yield e

    def _suppress_item_matter(self, item, agenda_url):
        '''
        Agenda items in Legistar do not always display links to
        associated matter files even if the same agenda item
        in the API references a Matter File. The agenda items
        we scrape should honor the suppression on the Legistar
        agendas.

        This is also practical because matter files that are hidden
        in the Legistar Agenda do not seem to available for scraping
        on Legistar or through the API
        '''

        if item['EventItemMatterFile'] is not None:

            if item['EventItemMatterStatus'] == 'Draft':
                suppress = True
            elif item['EventItemMatterType'] == 'Closed Session':
                suppress = True
            else:
                suppress = False

            if suppress:
                item['EventItemMatterFile'] = None


class LAMetroAPIEvent(dict):
    '''
    This class is for adding methods to the API event dict
    to faciliate maching events with their other-language
    partners.
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

    @property
    def partner_key(self):
        return (self._partner_name, self['EventDate'])

    @property
    def key(self):
        return (self['EventBodyName'], self['EventDate'])


class LAMetroWebEvent(dict):
    '''
    This class is for adding methods to the web event dict
    to facilitate labeling and sourcing audio appropriately.
    '''

    web_scraper = LegistarScraper(retry_attempts=3,
                                  requests_per_minute=0)

    @property
    def has_audio(self):
        return self['Meeting video'] != 'Not\xa0available'

