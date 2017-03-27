from legistar.events import LegistarAPIEventScraper
from legistar.events import LegistarEventsScraper

import requests
import lxml.html

from pupa.scrape import Scraper
from pupa.scrape import Event

class LametroEventScraper(LegistarAPIEventScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    # WEB_URL = 'https://metro.legistar.com'
    EVENTSPAGE = "https://metro.legistar.com/Calendar.aspx"
    TIMEZONE = "America/Los_Angeles"

    def scrape(self):

        web_scraper = LegistarEventsScraper(None, None)
        web_scraper.EVENTSPAGE = self.EVENTSPAGE

        for event in web_scraper.events():
            print(event)
            raise
        # GET the events page.
        url = self.WEB_URL + '/Calendar.aspx'
        entry = self.get(url).text
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)

        div_id = 'ctl00_ContentPlaceHolder1_divGrid'
        info_table = page.xpath("//body/form//div[@id='%s']//table" % div_id)

        print(lxml.html.tostring(info_table[0]))

        lxml.html.open_in_browser(info_table[0])
        # /div[@id='ctl00_divBody']")

        # /div[@id = ctl00_Div1]

        # /div[@id = ctl00_Div2]/div[@id=ctl00_divMiddle]/div[@id=ctl00_ContentPlaceHolder1_MultiPageCalendar]/div[@id=ctl00_ContentPlaceHolder1_pageGrid]/div[@id=ctl00_ContentPlaceHolder1_panMain]/div[@id=ctl00_ContentPlaceHolder1_divGrid]//table")



        # for table in info_table:
        #     print(lxml.html.tostring(table))
        # print(len(info_table))
        # print(lxml.html.tostring(info_table))
        # table_body = info_table.xpath("./tbody")[0]

        # # print(lxml.html.tostring(table_body))
        # table_rows = table_body.xpath("./tr")

        # print('$$$$$$$')
        # print(len(table_rows))
        # for row in table_rows:
        #     tds = row.xpath("./td")
        #     for td in tds:
        #         print("table data")
        #         print(td.text)
        #         print(lxml.html.tostring(td))


        for event in self.events():

            e = Event(event["EventBodyName"],
                      start_time=event["start"],
                      timezone=self.TIMEZONE,
                      location_name=event["EventLocation"],
                      )

            e.add_source((self.WEB_URL + '/MeetingDetail.aspx?ID={0}&GUID={1}&Options=info&Search=').format(event['EventId'], event['EventGuid']), note='web')

            # Get the audio source...then, add it.
            e.add_source('http://metro.granicus.com/MediaPlayer.php?view_id=2&clip_id=661')

            # Get the minutes PDF...then, add it.
            e.add_source('View.ashx?M=M&ID=517044&GUID=5B227E61-0C48-44F2-8F7B-74BAA576050F')
            # print(e)

            yield e

        # for event in self.events():
        #     body_name = event["EventBodyName"]
        #     if 'Board of Directors -' in body_name:
        #         body_name, event_name = [part.strip()
        #                                  for part
        #                                  in body_name.split('-')]
        #     else:
        #         event_name = body_name

        #     e = Event(event_name,
        #               start_time=event["start"],
        #               timezone=self.TIMEZONE,
        #               description='',
        #               location_name=event["EventLocation"],
        #               status=event["status"])

        #     for item in self.agenda(event):
        #         agenda_item = e.add_agenda_item(item["EventItemTitle"])
        #         if item["EventItemMatterFile"]:
        #             identifier = item["EventItemMatterFile"]
        #             agenda_item.add_bill(identifier)


        #     e.add_participant(name=body_name,
        #                       type="organization")

        #     meeting_detail_web = self.WEB_URL + '/MeetingDetail.aspx?ID={EventId}&GUID={EventGuid}'.format(**event)
        #     if requests.head(meeting_detail_web).status_code == 200:
        #         e.add_source(meeting_detail_web, note='web')
        #     else:
        #         e.add_source('https://metro.legistar.com/Calendar.aspx', note='web')

        #     e.add_source(self.BASE_URL + '/events/{EventId}'.format(**event),
        #                  note='api')

        #     if event['EventAgendaFile']:
        #         e.add_document(note= 'Agenda',
        #                        url = event['EventAgendaFile'],
        #                        media_type="application/pdf")

        #     if event['EventMinutesFile']:
        #         e.add_document(note= 'Minutes',
        #                        url = event['EventMinutesFile'],
        #                        media_type="application/pdf")


        #     yield e

    # def scrapeWebCalendar(self):


