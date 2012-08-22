import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import itertools

class ChicagoLegistar :
  def __init__(self, uri) :
    self.data = {
      r'__VIEWSTATE' : r'',
      r'ctl00_RadScriptManager1_HiddenField' : r'', 
      r'ctl00_ContentPlaceHolder1_menuMain_ClientState' : r'',
      r'ctl00_ContentPlaceHolder1_gridMain_ClientState' : r''
      }

    self.headers = {
      'Content-Type': 'application/x-www-form-urlencoded'
      }

    f = urllib2.urlopen(uri)
    self.getStates(f)


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
    f = urllib2.urlopen(req).read()  #that's the actual call to the http site.

    result_page_urls = self.resultsUrls(f)

    return f, result_page_urls

  def resultsUrls(self, f) :

    soup = BeautifulSoup(f)
    self.getStates(f)


    result_page_urls = []

    for match in soup.fetch('a', {'href':re.compile('ctl02\$ctl00')}) :
      event_target = match['href'].split("'")[1]

      result_page_args =  {
        r'__EVENTTARGET' : event_target,
        r'__EVENTARGUMENT' : ''
      }

      fields = dict(self.data.items()
                    + self.search_args.items()
                    + result_page_args.items()
                    )
      # these have to be encoded    
      encoded_fields = urllib.urlencode(fields)

      req = urllib2.Request(uri, encoded_fields, self.headers)      

      result_page_urls.append(req)

    return result_page_urls

  def parseSearchResults(f) :
    """Take a page of search results and return a sequence of data
    of tuples about the legislation, of the form

    ('Document ID', 'Document URL', 'Type', 'Status', 'Introduction Date'
     'Passed Date', 'Main Sponsor', 'Title')
    """
    pass


  def parseLegislationDetail(f) :
    """Take a legislation detail page and return a dictionary of
    the different data appearing on the page

    Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
    """
    pass

if __name__ == '__main__' :

  uri = 'http://chicago.legistar.com/Legislation.aspx'
  scraper = ChicagoLegistar(uri)
  # First page of results
  f1, results = scraper.searchLegislation('zoning', ['legislative text'])
  # Second Page of results
  f2 = urllib2.urlopen(results[1])


  try:
    fout = open('tmp.htm', 'w')
  except:
    print('Could not open output file\n')

  fout.writelines(f2.readlines())
  fout.close()

