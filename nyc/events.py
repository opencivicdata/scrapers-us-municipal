from legistar.events import LegistarEventsScraper
from pupa.scrape import Event

import datetime
import re

class NYCEventsScraper(LegistarEventsScraper):
    TIMEZONE = 'America/New_York'
    EVENTSPAGE = "http://legistar.council.nyc.gov/Calendar.aspx/"
    BASEURL = "http://legistar.council.nyc.gov/"

    def scrape(self):
        for event, agenda in self.events() :
            if '--em--' in event[u'Meeting Location'] :
                location_string, other_orgs = event[u'Meeting Location'].split('--em--')[:2]
            else :
                location_string = event[u'Meeting Location'] 
                other_orgs = ''
            
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

            event_name = ' '.join([event['Name'], other_orgs])

            e = Event(name=event_name,
                      start_time=when,
                      timezone=self.TIMEZONE,
                      description=description,
                      location_name=location,
                      status=status)

            if event['Multimedia'] != 'Not\xa0available' : 
                e.add_media_link(note='Recording',
                                 url = event['Multimedia']['url'],
                                 type="recording",
                                 media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Minutes')

            participating_orgs = [event["Name"]]
            if other_orgs.startswith('Jointly with the') :
                other_orgs = other_orgs.replace('Jointly with the ', '')
                participating_orgs += re.split(' and the |, the ', other_orgs)

            for org in participating_orgs :
                e.add_participant(name=org,
                                  type="organization")

            if agenda :
                e.add_source(event["Meeting\xa0Details"]['url'])

                for item, _, _ in agenda :
                    if item["Name"] :
                        agenda_item = e.add_agenda_item(item["Name"])
                        if item["File #"] :
                            agenda_item.add_bill(item["Record #"]['label'])
            else :
                e.add_source(self.EVENTSPAGE)

            yield e

