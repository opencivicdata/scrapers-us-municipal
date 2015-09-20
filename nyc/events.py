from legistar.events import LegistarEventsScraper
from pupa.scrape import Event
from collections import deque

import datetime
import re

class NYCEventsScraper(LegistarEventsScraper):
    TIMEZONE = 'America/New_York'
    EVENTSPAGE = "http://legistar.council.nyc.gov/Calendar.aspx/"
    BASE_URL = "http://legistar.council.nyc.gov/"

    def scrape(self):
        last_events = deque(maxlen=10)
        for event, agenda in self.events(since=2011) :
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

            time_string = event['Meeting Time']
            if time_string in ('Deferred',) :
                status = 'cancelled'
                event_time = None
            else :
                event_time = datetime.datetime.strptime(time_string,
                                                        "%I:%M %p")
                when = when.replace(hour=event_time.hour,
                                    minute=event_time.minute)

                if self.now() < when :
                    status = 'confirmed'
                else :
                    status = 'passed'

            description = event['Meeting\xa0Topic']
            if any(each in description 
                   for each 
                   in ('Multiple meeting items',
                       'AGENDA TO BE ANNOUNCED')) :
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

            if event['Multimedia'] != 'Not\xa0available' : 
                e.add_media_link(note='Recording',
                                 url = event['Multimedia']['url'],
                                 type="recording",
                                 media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Minutes')

            participating_orgs = [event["Name"]]

            if other_orgs : 
                other_orgs = re.sub('Jointl*y with the ', '', other_orgs)
                participating_orgs += re.split(' and the |, the ', other_orgs)
            else :
                print(other_orgs)

            for org in participating_orgs :
                e.add_committee(name=org)

            if agenda :
                e.add_source(event["Meeting Details"]['url'])

                
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
                e.add_source(self.EVENTSPAGE)

            yield e
