import re
from collections import defaultdict
from io import StringIO

from lxml.html import fromstring

from pupa.scrape import BaseBillScraper
from pupa.utils import convert_pdf
from pupa.models import Bill

from .utils import Urls


agenda_list = ("http://cityclerk.cityofboise.org/city-council-meetings/"
               "council-agendas/2012-agendas/")


class BillScraper(BaseBillScraper):

    def get_agenda_urls(self):
        xpath = '//a/@href'
        urls = self.urls.agenda_list.doc.xpath(xpath)
        for url in filter(re.compile('\d+ca.pdf$', re.I).search, urls):
            yield url
        for url in filter(re.compile('\d+sm.pdf$', re.I).search, urls):
            yield url

    def get_bill_ids(self):
        self.urls = Urls(dict(agenda_list=agenda_list), scraper=self)
        for agenda_url in self.get_agenda_urls():
            self.urls.add(agenda=agenda_url)
            doc = self.urls.agenda.pdf_to_lxml

            titles = defaultdict(StringIO)
            for url in doc.xpath('//a'):
                if 'href' not in url.attrib:
                    continue
                href = url.attrib['href']
                if re.search(r'[ro]\-\d+\-\d+\.pdf$', href):
                    titles[href].write(url.text_content())

            for item in titles.items():
                try:
                    yield from self.parse_title(item)
                except Exception:
                    # Because PDF scraping is terrible.
                    continue

    def parse_title(self, item):
        url, title = item
        chunks = title.getvalue().split('\xa0')
        chunks = list(filter(None, chunks))

        # Fix problem of agenda item number connected to bill_id.
        if len(chunks[0]) > 3:
            bill_id = chunks.pop(0)
            if '.' in bill_id:
                print(bill_id)
                agenda_item, bill_id = bill_id.split('.')
            else:
                agenda_item = None
                bill_id = chunks.pop(0)
        else:
            agenda_item = chunks.pop(0)
            bill_id = chunks.pop(0)

        # Fix issue of different spacing betwixt bill_id and title.
        title = ' '.join(chunks)
        if len(bill_id) > 20:
            bill_id, title_start = bill_id.split(' ', 1)
            title = title_start + ' ' + title

        if not bill_id:
            return

        yield bill_id, dict(agenda_item=agenda_item, title=title, url=url)

    def get_type(self, bill_id):
        first = bill_id[0]
        try:
            return dict(R='resolution', O='ordinance')[first]
        except KeyError:
            raise self.ContinueScraping()

    def get_bill(self, bill_id, **kwargs):
        url = kwargs.pop('url')
        agenda_item = kwargs.pop('agenda_item')
        _type = self.get_type(bill_id)
        bill = Bill(bill_id, self.session, type=_type, **kwargs)
        bill.add_source(url, note='detail')
        return bill
