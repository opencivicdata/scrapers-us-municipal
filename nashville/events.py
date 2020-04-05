import datetime
import pytz
from pupa.scrape import Event

from .utils import NashvilleScraper


class NashvilleEventScraper(NashvilleScraper):

    def scrape(self):
        yield from self.scheduled_meetings()
        # needs to be implemented
        # yield from self.meeting_minutes_archive()

    def scheduled_meetings(self):
        base_url = 'http://www.nashville.gov/Metro-Council/Council-Events-Calendar.aspx'
        doc = self.lxmlize(base_url)
        event_anchor = doc.xpath('//ul[@class="eventswidget"]/descendant::*/a')
        for anchor in event_anchor:
            (event_link,) = anchor.xpath('./@href')
            meeting_doc = self.lxmlize(event_link)
            dnn_name = self.get_dnn_name(meeting_doc)
            event_id = 'dnn_ctr{}_EventDetails_pnlEvent'.format(dnn_name)
            (title, ) =  meeting_doc.xpath('//div[@id="{}"]/h1/text()'.format(event_id))
            date_time =  meeting_doc.xpath('//div[@id="{}"]/p/em/text()'.format(event_id))
            
            date_time = self.strip_string_array(date_time)
            try:
                start = datetime.datetime.strptime(date_time, '%m-%d-%Y %I:%M %p')
            except ValueError:
                start = datetime.datetime.strptime(date_time.replace('.', ''), '%m/%d/%Y %I:%M %p')
            tz = pytz.timezone("US/Central")
            start = tz.localize(start)
            event_location_id = 'dnn_ctr{}_EventDetails_pnlLocation'.format(dnn_name)
            try:
                (location_name, *address) =  meeting_doc.xpath('//div[@id="{}"]/p/text()'.format(event_location_id))
            except ValueError:
                location_name = ' - '
            description =  meeting_doc.xpath('//div[@id="{}"]/p[3]/text()'.format(event_id))
            description = self.strip_string_array(description)
            # @TODO: Marking everything as confirmed - need to learn how cancelled meetings are posted
            status = 'confirmed'
            # @TODO: Geocode *address
            e = Event(
                    name=title,
                    start_date=start,
                    location_name=location_name,
                    description=description,
                    status=status
                )
            e.add_source(event_link)
            yield e

    def meeting_minutes_archive(self):
        # Prior
        # http://www.nashville.gov/Metro-Clerk/Legislative/Minutes.aspx
        pass
