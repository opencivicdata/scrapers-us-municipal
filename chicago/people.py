from pupa.scrape import Scraper
from pupa.scrape.helpers import Legislator, Membership, Organization
import lxml.html
import datetime
import traceback
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    img = councilman_details.xpath("//img[@id='ctl00_ContentPlaceHolder1_imgPhoto']")
                    if img :
                        councilman['Photo'] = img[0].get('src')

                    committee_table = councilman_details.xpath("//table[@id='ctl00_ContentPlaceHolder1_gridDepartments_ctl00']")[0]
                    
                    committees = self.parseDataTable(committee_table)

                    yield councilman, committees

                else :
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
                link = field.getchildren()[0].find('a')
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
    



class ChicagoPersonScraper(LegistarScraper):
    

    
    def get_people(self):
        for councilman, committees in self.councilMembers() :
            contact_types = {
                "City Hall Office": ("address", "City Hall Office"),
                "City Hall Phone": ("phone", "City Hall Phone"),
                "Ward Office Phone": ("phone", "Ward Office Phone"),
                "Ward Office Address": ("address", "Ward Office Address"),
                "Fax": ("fax", "Fax")
            }
            
            contacts = []
            for contact_type, (_type, note) in contact_types.items () :
                if councilman[contact_type] : 
                    contacts.append({"type": _type,
                                     "value": councilman[contact_type],
                                     "note": note})

            if councilman["E-mail"] : 
                contacts.append({"type" : "email",
                                 "value" : councilman['E-mail']['label'],
                                 'note' : 'E-mail'})


            p = Legislator(councilman['Person Name']['label'],
                           post_id = councilman['Ward/Office'],
                           image=councilman['Photo'],
                           contact_details = contacts)


            if councilman['Website'] :
                p.add_link('homepage', councilman['Website']['url'])
            p.add_source(MEMBERLIST)

            for committee, _, _ in committees :
                print committee
                if committee['Legislative Body']['label'] :
                    if committee['Legislative Body']['label'] not in ('City Council', 'Office of the Mayor') :
                        p.add_committee_membership(committee['Legislative Body']['label'], 
                                                   role= committee["Title"])
                        


            yield p



