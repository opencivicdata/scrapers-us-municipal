from pupa.scrape import Event
from .legistar import LegistarScraper
from collections import defaultdict
import datetime
import lxml
import lxml.etree

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


    def scrape(self):
        for page in self.eventPages(EVENTSPAGE):
            events_table = page.xpath("//table[@class='rgMasterTable']")[0]
            for events, headers, rows in self.parseDataTable(events_table) :
                print(events)
                location_string = events[u'Meeting\xa0Location']
                location_list = location_string.split('--')
                location = ', '.join(location_list[0:2])

                status_string = location_list[-1].split('Chicago, Illinois')
                if len(status_string) > 1 and status_string[1] :
                    status = status_string[1].lower()
                    if status not in ['cancelled', 'tentative', 'confirmed', 'passed'] :
                        print(status)
                        status = 'confirmed'
                else :
                    status = 'confirmed'



                when = events[u'Meeting\xa0Date']
                time_string = events[u'Meeting\xa0Time']
                event_time = datetime.datetime.strptime(time_string,
                                                        "%I:%M %p")
                when = when.replace(hour=event_time.hour)

                e = Event(name=events["Name"]["label"],
                          when=when,
                          location=location,
                          status=status)
                e.add_source(EVENTSPAGE)
                if events['Video'] != u'Not\xa0available' :
                    print(events['Video'])

                yield e


