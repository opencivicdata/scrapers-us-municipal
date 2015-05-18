from pupa.scrape import Event
from .legistar import LegistarScraper
from collections import defaultdict
import datetime
import lxml
import lxml.etree
import pytz

EVENTSPAGE = "https://chicago.legistar.com/Calendar.aspx/"

class ChicagoEventsScraper(LegistarScraper):
    base_url = "https://chicago.legistar.com/"
    timezone = "US/Central"

    def eventPages(self, event_url, search_type='all') :

        page = self.lxmlize(event_url)

        if search_type == 'all' :
            payload = self.sessionSecrets(page)

            payload['ctl00$ContentPlaceHolder1$lstYears'] = 'All Years'
            payload['ctl00_ContentPlaceHolder1_lstYears_ClientState'] = '{"logEntries":[],"value":"All","text":"All Years","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'


            payload['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$lstYears'

            return self.pages(event_url, payload)

        else :
            return self.pages(page)


    def scrape(self, follow_links=True):
        for page in self.eventPages(EVENTSPAGE):
            events_table = page.xpath("//table[@class='rgMasterTable']")[0]
            for events, headers, rows in self.parseDataTable(events_table) :
                if follow_links and type(events['Meeting\xa0Details']) == dict :
                    detail_url = events['Meeting\xa0Details']['url']
                    meeting_details = self.lxmlize(detail_url)

                    agenda_table = meeting_details.xpath(
                        "//table[@id='ctl00_ContentPlaceHolder1_gridMain_ctl00']")[0]
                    agenda = self.parseDataTable(agenda_table)

                else :
                    meeting_details = False
                    
                location_string = events[u'Meeting\xa0Location']
                location_list = location_string.split('--', 2)
                location = ', '.join(location_list[0:2])
                if not location :
                    continue

                when = self.toTime(events[u'Meeting\xa0Date'])
                time_string = events[u'Meeting\xa0Time']
                if time_string :
                    event_time = datetime.datetime.strptime(time_string,
                                                            "%I:%M %p")
                    when = when.replace(hour=event_time.hour)
                    
                status_string = location_list[-1].split('Chicago, Illinois')
                if len(status_string) > 1 and status_string[1] :
                    status_text = status_string[1].lower()
                    print(status_text)
                    if any(phrase in status_text
                            for phrase in ('public hearing',
                                            'budget hearing',
                                            'special meeting')):
                        continue
                    elif any(phrase in status_text 
                           for phrase in ('rescheduled to',
                                          'postponed to',
                                          'reconvened to',
                                          'recessed',
                                          'cancelled',
                                          'new date and time',
                                          'rescheduled indefinitely',
                                          'rescheduled for',
                                          'changing time',)) :
                        status = 'cancelled'
                    elif status_text in ('rescheduled') :
                        status = 'cancelled'
                    else :
                        print(status_text)
                        #we are skipping these for now because
                        #they are almost all duplictes.
                        continue
                elif datetime.datetime.utcnow().replace(tzinfo = pytz.utc) > when :
                    status = 'confirmed'
                else :
                    status = 'passed'
                            

                e = Event(name=events["Name"]["label"],
                          start_time=when,
                          timezone='US/Central',
                          location=location,
                          status=status)


                if events['Video'] != 'Not\xa0available' : 
                    e.add_media_link(note='Recording',
                                     url = events['Video']['url'],
                                     type="recording",
                                     media_type = 'text/html')

                addDocs(e, events, 'Agenda')
                addDocs(e, events, 'Notice')
                addDocs(e, events, 'Transcript')
                addDocs(e, events, 'Summary')

                e.add_participant(name=events["Name"]["label"],
                                  type="organization")

                if meeting_details :
                    e.add_source(detail_url)

                    for item, _, _ in agenda :
                        agenda_item = e.add_agenda_item(item["Title"])
                        agenda_item.add_bill(item["Record #"]['label'])

                else :
                    e.add_source(EVENTSPAGE)

                yield e

def addDocs(e, events, doc_type) :
    try :
        if events[doc_type] != 'Not\xa0available' : 
            e.add_document(note= events[doc_type]['label'],
                           url = events[doc_type]['url'],
                           media_type="application/pdf")
    except ValueError :
        pass
        
