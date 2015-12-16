from pupa.scrape import Event
from legistar.events import LegistarEventsScraper
from collections import defaultdict
import datetime
import lxml
import lxml.etree
import pytz

class ChicagoEventsScraper(LegistarEventsScraper) :
    EVENTSPAGE = "https://chicago.legistar.com/Calendar.aspx"
    BASE_URL = "https://chicago.legistar.com/"
    TIMEZONE = "US/Central"

    def scrape(self):
        for event, agenda in self.events() :

            description = None

            location_string = event[u'Meeting Location']

            location_list = location_string.split('--', 2)
            location = ', '.join(location_list[0:2])
            if not location :
                continue

            when = self.toTime(event[u'Meeting Date'])

            event_time = event['iCalendar'].subcomponents[0]['DTSTART'].dt
            when = when.replace(hour=event_time.hour,
                                minute=event_time.minute)

            status_string = location_list[-1].split('Chicago, Illinois')
            if len(status_string) > 1 and status_string[1] :
                status_text = status_string[1].lower()
                if any(phrase in status_text 
                       for phrase in ('rescheduled to',
                                      'postponed to',
                                      'reconvened to',
                                      'rescheduled to',
                                      'meeting recessed',
                                      'recessed meeting',
                                      'postponed to',
                                      'recessed until',
                                      'deferred',
                                      'time change',
                                      'date change',
                                      'recessed meeting - reconvene',
                                      'cancelled',
                                      'new date and time',
                                      'rescheduled indefinitely',
                                      'rescheduled for',)) :
                    status = 'cancelled'
                elif status_text in ('rescheduled', 'recessed') :
                    status = 'cancelled'
                elif status_text in ('meeting reconvened',
                                     'reconvened meeting',
                                     'recessed meeting',
                                     'reconvene meeting',
                                     'rescheduled hearing',
                                     'rescheduled meeting',) :
                    status = confirmedOrPassed(when)
                elif status_text in ('amended notice of meeting',
                                     'room change',
                                     'amended notice',
                                     'change of location',
                                     'revised - meeting date and time') :
                    status = confirmedOrPassed(when)
                elif 'room' in status_text :
                    location = status_string[1] + ', ' + location
                elif status_text in ('wrong meeting date',) :
                    continue
                else :
                    print(status_text)
                    description = status_string[1].replace('--em--', '')
                    status = confirmedOrPassed(when)
            else :
                status = confirmedOrPassed(when)


            if description :
                e = Event(name=event["Name"]["label"],
                          start_time=when,
                          description=description,
                          timezone='US/Central',
                          location_name=location,
                          status=status)
            else :
                e = Event(name=event["Name"]["label"],
                          start_time=when,
                          timezone='US/Central',
                          location_name=location,
                          status=status)


            if event['Video'] != 'Not\xa0available' : 
                e.add_media_link(note='Recording',
                                 url = event['Video']['url'],
                                 type="recording",
                                 media_type = 'text/html')

            self.addDocs(e, event, 'Agenda')
            self.addDocs(e, event, 'Notice')
            self.addDocs(e, event, 'Transcript')
            self.addDocs(e, event, 'Summary')

            e.add_participant(name=event["Name"]["label"],
                              type="organization")

            if agenda :
                e.add_source(event['Meeting Details']['url'])

                
                for item, _, _ in agenda :
                    agenda_item = e.add_agenda_item(item["Title"])
                    if item["Record #"] :
                        agenda_item.add_bill(item["Record #"]['label'])

            else :
                e.add_source(self.EVENTSPAGE)

            yield e

def confirmedOrPassed(when) :
    if datetime.datetime.utcnow().replace(tzinfo = pytz.utc) > when :
        status = 'confirmed'
    else :
        status = 'passed'
    
    return status
