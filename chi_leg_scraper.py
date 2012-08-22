import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
from collections import defaultdict

class ChicagoLegistar :
  def __init__(self, uri) :
    self.data = defaultdict(str)

    f = urllib2.urlopen(uri)
    self.getStates(f)

    self.headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
      }

    self.data.update({
      r'__VIEWSTATE' : r'',
      r'ctl00_RadScriptManager1_HiddenField' : r'', 
      r'ctl00_ContentPlaceHolder1_menuMain_ClientState' : r'',
      r'ctl00_ContentPlaceHolder1_gridMain_ClientState' : r''
      })

  def getStates(self, f) :

    soup= BeautifulSoup(f)

    self.data['__VSTATE'] = soup.fetch('input', {'name' : '__VSTATE'})[0]['value']
    self.data['__EVENTVALIDATION'] = soup.fetch('input', {'name' : '__EVENTVALIDATION'})[0]['value']
  
 

  def searchLegislation(self, search_text, search_fields = None) :
    self.search_args = {
      r'ctl00$ContentPlaceHolder1$txtSearch' : search_text,   # Search text
      r'ctl00_ContentPlaceHolder1_lstYears_ClientState' : '{"value":"This Year"}', # Period to Include
      r'ctl00$ContentPlaceHolder1$lstTypeBasic' : 'All Types',  #types to include
    }

    for field in search_fields:
      if field == 'file number' :
        self.search_args[r'ctl00$ContentPlaceHolder1$chkID'] = 'on'
      elif field == 'legislative text' :
        self.search_args[r'ctl00$ContentPlaceHolder1$chkText'] = 'on'
      elif field == 'attachment' :
        self.search_args[r'ctl00$ContentPlaceHolder1$chkAttachments'] = 'on'
      elif field == 'other' :
        self.search_args[r'ctl00$ContentPlaceHolder1$chkOther'] = 'on'

    

    fields = dict(self.data.items()
                  + self.search_args.items()
                  + [(r'ctl00$ContentPlaceHolder1$btnSearch',
                      'Search Legislation')]
                  )

    # these have to be encoded    

    encoded_fields = urllib.urlencode(fields)
    
    req = urllib2.Request(uri, encoded_fields, self.headers)
    f= urllib2.urlopen(req)     #that's the actual call to the http site.

    return f

  def getResultsPages(self, f) :
    soup = BeautifulSoup(f)
    result_pages = []
    for match in soup.fetch('a', {'href':re.compile('ctl02\$ctl00')}) :
      result_pages.append(match['href'].split("'")[1])

    return result_pages

  def nextPage(self, f, result_page) :
    results_page = {
      r'__EVENTTARGET' : result_page,
      r'__EVENTARGUMENT' : ''
      }

    self.getStates(f)


    fields = dict(self.data.items()
                  + self.search_args.items()
                  + results_page.items()
                  )
    # these have to be encoded    
    encoded_fields = urllib.urlencode(fields)

    req = urllib2.Request(uri, encoded_fields, self.headers)
    f= urllib2.urlopen(req)     #that's the actual call to the http site.

    return f

if __name__ == '__main__' :

  uri = 'http://chicago.legistar.com/Legislation.aspx'
  scraper = ChicagoLegistar(uri)
  # First page of results
  f1 = scraper.searchLegislation('zoning', ['legislative text']).read()
  results = scraper.getResultsPages(f1)
  # Second Page of results
  f2 = scraper.nextPage(f1, results[1])
  # Third page of results
  f3 = scraper.nextPage(f1, results[2])

  try:
    fout = open('tmp.htm', 'w')
  except:
    print('Could not open output file\n')

  fout.writelines(f3.readlines())
  fout.close()

