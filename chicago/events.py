from pupa.scrape import Scraper
from pupa.models import Event
import datetime as dt
import lxml.html
import traceback
from collections import defaultdict
import datetime
import time

EVENTSPAGE = "https://chicago.legistar.com/Calendar.aspx/"

class LegistarScraper(Scraper) :
    date_format='%m/%d/%Y'
  

    def lxmlize(self, url, payload=None):
        entry = self.urlopen(url, 'POST', payload)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page


    def pages(self, url, payload=None) :
        page = self.lxmlize(url, payload)
        yield page

        next_page = page.xpath("//a[@class='rgCurrentPage']/following-sibling::a[1]")

        while len(next_page) > 0 : 

            payload = self.sessionSecrets(page)
            event_target = next_page[0].attrib['href'].split("'")[1]

            payload['__EVENTTARGET'] = event_target

            page = self.lxmlize(url, payload)

            yield page

            next_page = page.xpath("//a[@class='rgCurrentPage']/following-sibling::a[1]")


    def councilMembers(self, follow_links=True) :
        for page in self.pages(MEMBERLIST) :
            table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]

            for councilman, headers, row in self.parseDataTable(table):

                if follow_links and type(councilman['Person Name']) == dict :
                    detail_url = councilman['Person Name']['url']
                    councilman_details = self.lxmlize(detail_url)
                    img = councilman_details.xpath("//img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        councilman['Photo'] = img[0].get('src')

                    committee_table = councilman_details.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridDepartments_ctl00']")[0]
                    
                    committees = self.parseDataTable(committee_table)

                    yield councilman, committees

                else :
                    yield councilman

    def parseDataTable(self, table):
        """
        Legistar uses the same kind of data table in a number of
        places. This will return a list of dictionaries using the
        table headers as keys.
        """
        headers = table.xpath('.//th')
        rows = table.xpath(".//tr[starts-with(@id, 'ctl00_ContentPlaceHolder1_')]")


        keys = {}
        for index, header in enumerate(headers):
            keys[index] = header.text_content().replace('&nbsp;', ' ').strip()

        for row in rows:
          try:
            data = defaultdict(lambda : None)

            for index, field in enumerate(row.xpath("./td")):
                key = keys[index]
                value = field.text_content().replace('&nbsp;', ' ').strip()

                try:
                    value = datetime.datetime.strptime(value, self.date_format)
                except ValueError:
                    pass

                # Is it a link?
                address = None
                link = field.xpath('.//a')
                if len(link) > 0 :
                    address = self._get_link_address(link[0])
                if address is not None:
                    value = {'label': value, 'url': address}
                    
                data[key] = value

            yield data, keys, row

          except Exception as e:
            print 'Problem parsing row:'
            print row
            print traceback.format_exc()
            raise e

    def _get_link_address(self, link):
        # If the link doesn't start with a #, then it'll send the browser
        # somewhere, and we should use the href value directly.
        href = link.get('href')
        if href is not None and href != self.base_url :
          return href

        # If it does start with a hash, then it causes some sort of action
        # and we should check the onclick handler.
        else:
          onclick = link.get('onclick')
          if onclick is not None and 'open(' in onclick :
            return self.base_url + onclick.split("'")[1]

        # Otherwise, we don't know how to find the address.
        return None

    def sessionSecrets(self, page) :
        
        payload = {}
        #print page.xpath("//input[@name='__EVENTARGUMENT']/@value")
        payload['__EVENTARGUMENT'] = None
        payload['__VIEWSTATE'] = page.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        payload['__VSTATE'] = page.xpath("//input[@name='__VSTATE']/@value")[0]

        payload['__EVENTVALIDATION'] = page.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]

        return(payload)


    def eventPages(self, event_url, search_type='all') :

        page = self.lxmlize(event_url) 

        if search_type == 'all' :
            payload = self.sessionSecrets(page)

            payload['ctl00$ContentPlaceHolder1$lstYears'] = 'All Years'
            payload['ctl00_ContentPlaceHolder1_lstYears_ClientState'] = '{"logEntries":[],"value":"All","text":"All Years","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'


            payload['__EVENTTARGET'] = 'ctl00$ContentPlaceHolder1$lstYears'

            #print payload

            return self.pages(event_url, payload)

        else :
            return self.pages(page)



class ChicagoEventsScraper(LegistarScraper):
    base_url = "https://chicago.legistar.com/"

    def get_events(self):
        for page in self.eventPages(EVENTSPAGE) :
            events_table = page.xpath("//table[@class='rgMasterTable']")[0]
            for events, headers, rows in self.parseDataTable(events_table) :
                location_string = events[u'Meeting\xa0Location']
                location_list = location_string.split('--')
                location = ', '.join(location_list[0:2])
                
                status_string = location_list[-1].split('Chicago, Illinois')
                if len(status_string) > 1 and status_string[1] :
                    status = status_string[1].lower()
                    if status not in ['cancelled', 'tentative', 'confirmed', 'passed'] :
                        print status
                        status = 'confirmed'
                else :
                    status = 'confirmed'

                    
                
                when = events[u'Meeting\xa0Date']
                time_string = events[u'Meeting\xa0Time']
                event_time = datetime.datetime.strptime(time_string, 
                                                        "%I:%M %p")
                when = when.replace(hour=event_time.hour)

                e = Event(name=events["Name"]["label"],
                          session=self.session,
                          when=when,
                          location=location,
                          status=status)
                e.add_source(EVENTSPAGE)
                if events['Video'] != u'Not\xa0available' :
                    print events['Video']
                
                #e.add_media_link(
                yield e
                

                

        #     event = Event(name=name,
        #                   session=self.session,
        #                   when=when,
        #                   location=location)
                          
                          
                #print events
        
        # main = 
        # rows = main.xpath(".//tr")[1:]
        # for row in rows:
        #     if "No records were found." in row.text_content():
        #         self.warning("Hum. They don't seem to have events?")
        #         continue

        #     (name, date, _, time, where, details, notice,
        #      agenda, summary, video) = row.xpath(".//td")
        #     # _ nom's the image next to the date on the page.

        #     name = name.text_content().strip() # leaving an href on the table
        #     time = time.text_content().strip()
        #     location = where.text_content().strip()

        #     if "Deferred" in time:
        #         continue

        #     all_day = False
        #     if time == "":
        #         all_day = True
        #         when = dt.datetime.strptime(date.text.strip(),
        #                                     "%m/%d/%Y")
        #     else:
        #         when = dt.datetime.strptime("%s %s" % (date.text.strip(), time),
        #                                     "%m/%d/%Y %I:%M %p")

        #     event = Event(name=name,
        #                   session=self.session,
        #                   when=when,
        #                   location=location)
        #     event.add_source(url)

        #     agendas = agenda.xpath(".//a[@href]")
        #     for a in agendas:
        #         event.add_link(a.text, a.attrib['href'])

        #     summary = summary.xpath(".//a[@href]")
        #     for minute in summary:
        #         event.add_link(minute.text, minute.attrib['href'])

        #     yield event
