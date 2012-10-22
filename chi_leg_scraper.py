import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import time
import datetime
import mechanize
from collections import defaultdict

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

        data = self._data(event_target)

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
      legislation.append(row.fetch("a")[0]['href'].split('&Options')[0])
      try:
        legislation[3] = datetime.datetime.strptime(legislation[3], '%m/%d/%Y')
      except ValueError :
        legislation[3] = ''

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
          values.append(cell.text.replace('&nbsp;', ' ').strip())
      else :
        keys.append(cell.text)
      i += 1

    details = defaultdict(str)
    details.update(dict(zip(keys, values)))

    try:
      details[u'Attachments:'] = soup.fetch('span', {'id' : 'ctl00_ContentPlaceHolder1_lblAttachments2' })[0].a['href']
    except IndexError :
      pass

    try:
      details[u'Related files:'] = soup.fetch('span', {'id' : 'ctl00_ContentPlaceHolder1_lblRelatedFiles2' })[0].a['href']
    except IndexError :
      pass



    history_row = soup.fetch('tr', {'id' : re.compile('ctl00_ContentPlaceHolder1_gridLegislation_ctl00')})

    history_keys = ["date", "journal_page", "action_by", "status", "results", "votes", "meeting_details"]

    history = []

    for row in history_row :
      values = []
      for key, cell in zip(history_keys, row.fetch('td')) :
        if key in ['votes', 'meeting_details'] :
          try:
            values.append(cell.a['href'])
          except KeyError:
            values.append('')
        elif key == 'date':
          values.append(datetime.datetime.strptime(cell.text.replace('&nbsp;', ' ').strip(), '%m/%d/%Y'))
        else:
          values.append(cell.text.replace('&nbsp;', ' ').strip())

          
      history.append(dict(zip(history_keys, values)))


    return details, history

  def _data(self, event_target) :
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

    return data


      





