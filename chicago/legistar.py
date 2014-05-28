from pupa.scrape import Scraper
import lxml.html
import lxml.etree
import traceback
import datetime
from collections import defaultdict

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


    def _get_link_address(self, link_soup):
        # If the link doesn't start with a #, then it'll send the browser
        # somewhere, and we should use the href value directly.
        href = link_soup.get('href')
        if href is not None and not href.startswith('#'):
          return href

        # If it does start with a hash, then it causes some sort of action
        # and we should check the onclick handler.
        else:
          onclick = link_soup.get('onclick')
          if onclick is not None and onclick.startswith("radopen('"):
            return onclick.split("'")[1]

        # Otherwise, we don't know how to find the address.
        return None

    def sessionSecrets(self, page) :

        payload = {}
        payload['__EVENTARGUMENT'] = None
        payload['__VIEWSTATE'] = page.xpath("//input[@name='__VIEWSTATE']/@value")[0]
        payload['__EVENTVALIDATION'] = page.xpath("//input[@name='__EVENTVALIDATION']/@value")[0]

        return(payload)


