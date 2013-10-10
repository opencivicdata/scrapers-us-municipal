from pupa.scrape import Scraper
from pupa.scrape.helpers import Legislator, Organization
import lxml.html
import datetime
import traceback

MEMBERLIST = 'https://chicago.legistar.com/People.aspx'

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

        while next_page : 

            event_target = next_page.attrib['href'].split("'")[1]
            br.select_form('aspnetForm')
            data = self._data(br.form, event_target)

            del data['ctl00$ContentPlaceHolder1$gridPeople$ctl00$ctl02$ctl01$ctl01']
            # print data
            data = urllib.urlencode(data)
            page = lxmlize(url, payload)

            yield page

            next_page = page.xpath("//a[@class='rgCurrentPage']/following-sibling::a[1]")


    def councilMembers(self, follow_links=True) :
        for page in self.pages(MEMBERLIST) :
            table = page.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridPeople_ctl00']")[0]


            for councilman, headers, row in self.parseDataTable(table):

                if follow_links and type(councilman['Person Name']) == dict :
                    detail_url = councilman['Person Name']['url']
                    councilman_details = self.lxmlize(detail_url)
                    img = councilman_details.xpath("./img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        councilman['Photo'] = img.get['src']

                yield councilman

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
    
    def parseDataTable(self, table):
        """
        Legistar uses the same kind of data table in a number of
        places. This will return a list of dictionaries using the
        table headers as keys.
        """
        headers = table.xpath('//th')
        rows = table.xpath("//tr[starts-with(@id, 'ctl00_ContentPlaceHolder1_')]")
        keys = {}
        for index, header in enumerate(headers):
            keys[index] = header.text_content().replace('&nbsp;', ' ').strip()

        for row in rows:
          try:
            data = {}

            for index, field in enumerate(row.xpath("./td")):
                key = keys[index]
                value = field.text_content().replace('&nbsp;', ' ').strip()

                try:
                    value = datetime.datetime.strptime(value, self.date_format)
                except ValueError:
                    pass

                # Is it a link?
                address = None
                link = field.find('a')
                if link is not None:
                    address = self._get_link_address(link)
                if address is not None:
                    value = {'label': value, 'url': address}
                    
                data[key] = value

            yield data, keys, row
          except Exception as e:
            print 'Problem parsing row:'
            print row
            print traceback.format_exc()
            raise e
    


class PersonScraper(LegistarScraper):




    def get_people(self):
        for councilman in self.councilMembers() :
            
            p = Legislator(councilman['Person Name']['label'],
                           post_id = councilman['Ward/Office'])
            p.add_source(MEMBERLIST)

            yield p



