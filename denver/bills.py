import re
from collections import defaultdict
from io import StringIO

from lxml.html import fromstring

from pupa.scrape import BaseBillScraper
from pupa.utils import convert_pdf
from pupa.scrape import Bill

from .utils import Urls


search_url = (
    'http://www.denvergov.org/sirepub/items.aspx?'
    'stype=advanced&meettype=-%20All%20Types%20-&meetdate=This%20Year')


class BillScraper(BaseBillScraper):

    def get_bill_ids(self):
        self.urls = Urls(dict(search=search_url), scraper=self)

        rows = ('id', 'number', 'type', 'status', 'meeting_type',
                'meeting_date', 'district', 'sponsor', 'title')
        xpath = '//tr[contains(@class, "datagrid")]'
        for tr in self.urls.search.xpath(xpath)[1:]:
            bill_id = re.search(r'\((.+)\)', tr.attrib['onclick']).group(1)
            data = [td.text_content() for td in tr.xpath('td')[1:]]
            yield bill_id, dict(zip(rows, [bill_id] + data))

    def get_bill(self, bill_id, **kwargs):
        url = 'http://www.denvergov.org/sirepub/item.aspx?itemid=%s' % bill_id
        self.urls.add(detail=url)

        bill_id = kwargs.pop('number')
        bill = Bill(bill_id, self.session, kwargs['title'], 'butt',
                    type=['bills'])
        bill.add_source(url, note='detail')

        xpath = '//table[contains(@class, "history")]/tr'
        for tr in self.urls.detail.xpath(xpath):
            import pdb; pdb.set_trace()

        return bill
