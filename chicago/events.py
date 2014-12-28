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

                    
                location_string = events[u'Meeting\xa0Location']
                location_list = location_string.split('--')
                location = ', '.join(location_list[0:2])

                when = events[u'Meeting\xa0Date']
                time_string = events[u'Meeting\xa0Time']
                event_time = datetime.datetime.strptime(time_string,
                                                        "%I:%M %p")
                when = when.replace(hour=event_time.hour)
                when = when.replace(tzinfo=pytz.timezone("US/Central"))

                status_string = location_list[-1].split('Chicago, Illinois')
                if len(status_string) > 1 and status_string[1] :
                    status_text = status_string[1].lower()
                    if any(phrase in status_text 
                           for phrase in ('rescheduled to',
                                          'postponed to',
                                          'reconvened to',
                                          'recessed',
                                          'cancelled',
                                          'new date and time',
                                          'rescheduled indefinitely',
                                          'rescheduled for')) :
                        status = 'cancelled'
                    elif status_text in ('rescheduled') :
                        status = 'cancelled'
                    else :
                        print(status_text)
                elif datetime.datetime.utcnow().replace(tzinfo = pytz.utc) > when :
                    status = 'confirmed'
                else :
                    status = 'passed'
                            

                e = Event(name=events["Name"]["label"],
                          start_time=when,
                          timezone='US/Central',
                          location=location,
                          status=status)
                e.add_source(detail_url)
                if events['Video'] != 'Not\xa0available' : 
                    e.add_media_link(note='Recording',
                                     url = events['Video']['url'],
                                     type="recording",
                                     media_type = '???')

                addDocs(e, events, 'Agenda')
                addDocs(e, events, 'Notice')
                addDocs(e, events, 'Transcript')
                addDocs(e, events, 'Summary')

                if events["Name"]["label"] != "City Council" :
                    for item, _, _ in agenda :
                        agenda_item = e.add_agenda_item(item["Title"])
                        agenda_item.add_bill(item["Record #"]['label'])

                
                e.add_participant(name=events["Name"]["label"],
                                  type="organization")

                yield e

def addDocs(e, events, doc_type) :
    try :
        if events[doc_type] != 'Not\xa0available' : 
            e.add_document(note= events[doc_type]['label'],
                           url = events[doc_type]['url'],
                           media_type="application/pdf")
    except ValueError :
        pass
        
