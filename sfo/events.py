from legistar.events import LegistarEventsScraper
from pupa.scrape import Event
from collections import deque

import datetime
import re

class SFEventScraper(LegistarEventsScraper):
    TIMEZONE = 'US/Pacific'
    EVENTSPAGE = "https://sfgov.legistar.com/Calendar.aspx"
    BASE_URL = "https://sfgov.legistar.com"

    def scrape(self):
        last_events = deque(maxlen=10)
        for event, agenda in self.events(since=2015) :
            other_orgs = ''
            extras = []

            if '--em--' in event[u'Meeting Location'] :
                location_string, note = event[u'Meeting Location'].split('--em--')[:2]
                for each in note.split(' - ') :
                    if each.startswith('Join') :
                        other_orgs = each
                    else :
                        extras.append(each)
            else :
                location_string = event[u'Meeting Location']

            location_list = location_string.split('-', 2)
            location = ', '.join([each.strip() for each in location_list[0:2]])
            if not location :
                continue

            when = self.toTime(event[u'Meeting Date'])

            event_time = event['iCalendar'].subcomponents[0]['DTSTART'].dt
            when = when.replace(hour=event_time.hour,
                                minute=event_time.minute)

            time_string = event['Meeting Time']
            if time_string in ('Deferred',) :
                status = 'cancelled'
            elif self.now() < when :
                status = 'confirmed'
            else :
                status = 'passed'

            description = ''

            event_name = event['Name']

            event_id = (event_name, when)

            if event_id in last_events :
                continue
            else :
                last_events.append(event_id)

            e = Event(name=event_name,
                      start_time=when,
                      timezone=self.TIMEZONE,
                      description=description,
                      location_name=location,
                      status=status)

            if extras :
                e.extras = {'location note' : ' '.join(extras)}

            MEDIA_COLUMNS = ['Video', 'Audio', 'Transcript']

            for media_format in MEDIA_COLUMNS :

                if event[media_format] != 'Not\xa0available' :
                    e.add_media_link(note=media_format.capitalize(),
                                     url = event[media_format]['url'],
                                     type=media_format.lower(),
                                     media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Minutes')

            if event['Name'] == 'City Council Stated Meeting' :
                participating_orgs = ['New York City Council']
            elif 'committee' in event['Name'].lower() :
                participating_orgs = [event["Name"]]
            else :
                participating_orgs = []

            if other_orgs :
                other_orgs = re.sub('Jointl*y with the ', '', other_orgs)
                participating_orgs += re.split(' and the |, the ', other_orgs)

            for org in participating_orgs :
                e.add_committee(name=org)

            if agenda :
                e.add_source(event["Meeting Details"]['url'], note='web')


                for item, _, _ in agenda :
                    if item["Name"] :
                        agenda_item = e.add_agenda_item(item["Name"])
                        if item["File\xa0#"] :
                            if item['Action'] :
                                note = item['Action']
                            else :
                                note = 'consideration'
                            agenda_item.add_bill(item["File\xa0#"]['label'],
                                                 note=note)
            else :
                e.add_source(self.EVENTSPAGE, note='web')

            yield e
