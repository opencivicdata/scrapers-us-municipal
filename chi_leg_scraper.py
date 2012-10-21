import sqlite3
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import time
import mechanize

conn = sqlite3.connect("chicago_legislation.db")
c = conn.cursor()

class ChicagoLegistar :
  def __init__(self, uri):
    self.uri = uri
    self.br = mechanize.Browser()



  def searchLegislation(self, search_text, num_pages = None) :
    self.br.open(self.uri)
    self.br.select_form('aspnetForm')
    self.br.form['ctl00$ContentPlaceHolder1$txtTit'] = search_text
    self.br.submit(name='ctl00$ContentPlaceHolder1$btnSearch')

    

    all_results = False
    search_results = []

    while all_results is False :
      soup = BeautifulSoup(self.br.response().read())

      legislation = self.parseSearchResults(soup)
      search_results.extend(legislation)

      current_page = soup.fetch('a', {'class': 'rgCurrentPage'})[0]

      print 'page', current_page.text
      print legislation[0]
      print


      next_page = current_page.findNextSibling('a')
      
      if next_page :
        event_target = next_page['href'].split("'")[1]

        time.sleep(5)
        self.br.select_form('aspnetForm')


        data = dict([(control.name, control.value)
                     for control in self.br.form.controls
                     if (control.name.count('$') == 2
                         and control.type != 'submit'
                         and control.value not in [[],
                                                   '-Select-',
                                                   ['=']])])

                     
        data.update({'__VIEWSTATE': '',
                     'ctl00_RadScriptManager1_HiddenField' : '', 
                     'ctl00_ContentPlaceHolder1_menuMain_ClientState' : '',
                     'ctl00_ContentPlaceHolder1_gridMain_ClientState' : '',
                     '__VSTATE' : self.br.form['__VSTATE'],
                     '__EVENTVALIDATION' : self.br.form['__EVENTVALIDATION'],
                     '__EVENTTARGET' : event_target,
                     '__EVENTARGUMENT' : ''})


      
        data = urllib.urlencode(data)
        self.br.open(self.uri, data)

      else :
        all_results = True

    return search_results

  def parseSearchResults(self, soup) :
    """Take a page of search results and return a sequence of data
    of tuples about the legislation, of the form

    ('Document ID', 'Document URL', 'Type', 'Status', 'Introduction Date'
     'Passed Date', 'Main Sponsor', 'Title')
    """
    
    legislation_rows = soup.fetch('tr', {'id':re.compile('ctl00_ContentPlaceHolder1_gridMain_ctl00__')})
    print "found some legislation!"
    print len(legislation_rows)
    
    
    legislation_list = []
    for row in legislation_rows :
      legislation = []
      for field in row.fetch("td") :
        legislation.append(field.text)
      legislation.append(row.fetch("a")[0]['href'])
      legislation_list.append(legislation)
      
    return legislation_list


  def parseLegislationDetail(self, url) :
    """Take a legislation detail page and return a dictionary of
    the different data appearing on the page

    Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
    """
    f = urllib2.urlopen(url)
    soup = BeautifulSoup(f)
    detail_div = soup.fetch('div', {'id' : 'ctl00_ContentPlaceHolder1_pageDetails'})
    keys = []
    values = []
    i = 0
    for cell in  detail_div[0].fetch('td')[0:25] :
      if i % 2 :
          values.append(cell.text)
      else :
        keys.append(cell.text)
      i += 1

    details = dict(zip(keys, values))

    history_row = soup.fetch('tr', {'id' : re.compile('ctl00_ContentPlaceHolder1_gridLegislation_ctl00')})

    history_keys = ["date", "journal_page", "action_by", "status", "results", "votes", "meeting_details"]

    history = []

    for row in history_row :
      values = []
      for cell in row.fetch('td') :
        values.append(cell.text)
      history.append(dict(zip(history_keys, values)))

    print details
    print history
      


if True:
  uri = 'http://chicago.legistar.com/Legislation.aspx'
  scraper = ChicagoLegistar(uri)
  legislation = scraper.searchLegislation('zoning')

  [legs.pop(4) for legs in legislation]
  
  c.executemany('INSERT OR IGNORE INTO legislation '
                '(id, type, status, intro_date, main_sponsor, title, url) '
                'VALUES '
                '(?, ?, ?, ?, ?, ?, ?)',
                legislation)

  conn.commit()



if False:
    uri = 'http://chicago.legistar.com/Legislation.aspx'
    scraper = ChicagoLegistar(uri)
    leg_page = "http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466"
    
    scraper.parseLegislationDetail(leg_page) 

c.close()


