from pupa.scrape import Scraper
import lxml.html
import lxml.etree as etree
import traceback
import datetime
from collections import defaultdict
import itertools
import pytz
import re

class LegistarScraper(Scraper):
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


    def parseDetails(self, detail_div) :
        """
        Parse the data in the top section of a detail page.
        """
        detail_query = ".//*[starts-with(@id, 'ctl00_ContentPlaceHolder1_lbl')"\
                       "     or starts-with(@id, 'ctl00_ContentPlaceHolder1_hyp')]"
        fields = detail_div.xpath(detail_query)
        details = {}
        
        for field_key, field in itertools.groupby(fields, 
                                                  fieldKey) :
            field = list(field)
            field_1, field_2 = field[0], field[-1]
            key = field_1.text_content().replace(':', '').strip()
            if field_2.find('.//a') is not None :
                value = []
                for link in field_2.xpath('.//a') :
                    value.append({'label' : link.text_content().strip(),
                                  'url' : self._get_link_address(link)})
            else :
                value = field_2.text_content().strip()

            details[key] = value

        return details


    def parseDataTable(self, table):
        """
        Legistar uses the same kind of data table in a number of
        places. This will return a list of dictionaries using the
        table headers as keys.
        """
        headers = table.xpath(".//th[starts-with(@class, 'rgHeader')]")
        rows = table.xpath(".//tr[@class='rgRow' or @class='rgAltRow']")


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
                    value = value.replace(tzinfo=pytz.timezone(self.timezone))

                except ValueError:
                    pass


                # Is it a link?
                address = None
                link = field.find('.//a')

                if link is not None:
                    address = self._get_link_address(link)
                if address is not None:
                    value = {'label': value, 'url': address}

                data[key] = value

            yield data, keys, row

          except Exception as e:
            print('Problem parsing row:')
            print(etree.tostring(row))
            print(traceback.format_exc())
            raise e


    def _get_link_address(self, link):
        if 'onclick' in link.attrib :
            onclick = link.attrib['onclick']
            if onclick is not None and onclick.startswith("radopen('"):
                url = self.base_url + onclick.split("'")[1]
        elif 'href' in link.attrib : 
            url = link.attrib['href']
        else :
            url = None

        return url

    def sessionSecrets(self, page) :

        payload = {}
        payload['__EVENTARGUMENT'] = None
        payload['__VIEWSTATE'] = page.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        payload['__EVENTVALIDATION'] = page.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]

        return(payload)


def fieldKey(x) :
    field_id = x.attrib['id']
    field = re.split(r'hyp|lbl', field_id)[-1]
    field = field.rstrip('X2')
    return field
