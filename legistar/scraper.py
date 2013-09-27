import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import time
import datetime
import mechanize
from collections import defaultdict
import slate
import cStringIO
import pdfminer

class LegistarScraper (object):
  """
  A programatic interface onto a hosted Legistar website.
  """

  def __init__(self, config):
    """
    Construct a new Legistar scraper.  Pass in the host name of the Legistar
    instance, e.g. 'phila.legistar.com'.
    """
    self.config = config
    self.host = 'https://%s/' % self.config['hostname']
    self.fulltext = self.config['fulltext']
    self.sponsor_links = self.config['sponsor_links']
    
    # Assume that the legislation and calendar URLs are constructed regularly.
    self._legislation_uri = (
      self.host + self.config.get('legislation_path', 'Legislation.aspx'))
    self._calendar_uri = (
      self.host + self.config.get('calendar_path', 'Calendar.aspx'))
    self._people_uri = (
      self.host + self.config.get('people_path', 'People.aspx'))
    
  def searchLegislation(self, search_text, created_before=None, created_after=None, num_pages = None):
    """
    Submit a search query on the legislation search page, and return a list
    of summary results.
    """
    br = self._get_new_browser()
    br.open(self._legislation_uri)

    try:
      # Check to see if we are on Advanced Search Page
      br.find_link(text_regex='Simple.*')

    except mechanize.LinkNotFoundError:
      # If it's not there, then we are on the simple search form.
      br = self._switch_to_advanced_search(br)

    br.select_form('aspnetForm')
    br.form.set_all_readonly(False)

    # Enter the search parameters
    # TODO: Each of the possible form fields should be represented as keyword
    # arguments to this function. The default query string should be for the
    # the default 'Legislative text' field.
    br.form['ctl00$ContentPlaceHolder1$txtText'] = search_text


    if created_before or created_after:
      if created_before :
        creation_date = created_before
        relation = '<'
      else:
        creation_date = created_after
        relation = '>'

      br.form['ctl00$ContentPlaceHolder1$radFileCreated'] = [relation]
      br.form['ctl00_ContentPlaceHolder1_txtFileCreated1_dateInput_ClientState'] = '{"enabled":true,"emptyMessage":"","validationText":"%s-00-00-00","valueAsString":"%s-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}' % (creation_date, creation_date)


    # Submit the form
    data = self._data(br.form, None)

    # Return up to one million search results
    data['ctl00_ContentPlaceHolder1_lstMax_ClientState'] = '{"value":"1000000"}'

    data['ctl00$ContentPlaceHolder1$btnSearch'] = 'Search Legislation'
    data['ctl00_ContentPlaceHolder1_lstYearsAdvanced_ClientState'] = '{"logEntries":[],"value":"All","text":"All Years","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'

    data = urllib.urlencode(data)

    response = _try_connect(br, self._legislation_uri, data)

    # Loop through the pages, yielding each of the results
    all_results = False
    while all_results is False :
      soup = BeautifulSoup(response.read())

      legislation_iter = self.parseSearchResults(soup)
      for legislation in legislation_iter:
        yield legislation


      current_page = soup.fetch('a', {'class': 'rgCurrentPage'})
      if current_page :
        current_page = current_page[0]
        print 'page', current_page.text
        print
        next_page = current_page.findNextSibling('a')
      else :
        next_page = None

      if next_page :
        event_target = next_page['href'].split("'")[1]

        br.select_form('aspnetForm')
        data = self._data(br.form, event_target)
        data = urllib.urlencode(data)
        response = _try_connect(br, self._legislation_uri, data)

      else :
        all_results = True

    raise StopIteration

  def parseSearchResults(self, soup) :
    """Take a page of search results and return a sequence of data
    of tuples about the legislation, of the form

    ('Document ID', 'Document URL', 'Type', 'Status', 'Introduction Date'
     'Passed Date', 'Main Sponsor', 'Title')
    """
    table = soup.find('table', id='ctl00_ContentPlaceHolder1_gridMain_ctl00')
    for legislation, headers, row in self.parseDataTable(table):
      # Do legislation search-specific stuff
      # ------------------------------------
      # First column should be the ID of the record.
      id_key = headers[0]
      try:
        legislation_id = legislation[id_key]['label']
      except TypeError:
        continue
      legislation_url = legislation[id_key]['url']
      legislation[id_key] = legislation_id
      legislation['URL'] = self.host + legislation_url.split('&Options')[0]

      yield legislation

  def parseDataTable(self, table_soup):
    """
    Legistar uses the same kind of data table in a number of places. This will
    return a list of dictionaries using the table headers as keys.
    """
    headers = table_soup.fetch('th')
    rows = table_soup.fetch('tr', id=re.compile('ctl00_ContentPlaceHolder1_'))

    keys = {}
    for index, header in enumerate(headers):
      keys[index] = header.text.replace('&nbsp;', ' ').strip()

    for row in rows:
      try:
        data = {}

        parse_dates = ('date_format' in self.config)
        for index, field in enumerate(row.fetch("td")):
          key = keys[index]
          value = field.text.replace('&nbsp;', ' ').strip()

          # Is it a date?
          if parse_dates:
            try:
              value = datetime.datetime.strptime(value, self.config['date_format'])
            except ValueError:
              pass

          # Is it a link?
          address = None
          link = field.find('a')
          if link is not None:
            address = self._get_link_address(link)
            if address is not None:
              value = {'label': value, 'url': self.host + address}

          data[key] = value

        yield data, keys, row
      except Exception as e:
        print 'Problem parsing row:'
        print row
        raise e

  def _lowercase_keys(self, d):
    outp = {}
    for k,v in d.items():
      outp[k.lower()] = d[k]
    return outp

  def expandLegislationSummary(self, summary):
    """
    Take a row as given from the searchLegislation method and retrieve the
    details of the legislation summarized by that row.
    """
    return self.expandSummaryRow(self._lowercase_keys(summary), self.parseLegislationDetail)

  def expandHistorySummary(self, summary):
    """
    Take a row as given from the parseLegislationDetail method and retrieve the
    details of the history event summarized by that row.
    """
    return self.expandSummaryRow(self._lowercase_keys(summary), self.parseHistoryDetail)

  def expandSummaryRow(self, summary, parse_function):
    """
    Take a row from a data table and use the URL value from that row to
    retrieve more details. Parse those details with parse_function.
    """
    detail_uri = summary['url']

    br = self._get_new_browser()
    connection_complete = False

    response = _try_connect(br, detail_uri)

    f = response.read()
    soup = BeautifulSoup(f)
    return parse_function(soup)

  def parseLegislationDetail(self, soup):
    """Take a legislation detail page and return a dictionary of
    the different data appearing on the page

    Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
    """
    # Pull out the top matter
    detail_div = soup.find('div', {'id' : 'ctl00_ContentPlaceHolder1_pageDetails'})
    details = self._get_general_details(detail_div)

    # Treat the attachments specially
    attachments_span = soup.find('span', id='ctl00_ContentPlaceHolder1_lblAttachments2')
    if attachments_span is not None:
      details[u'Attachments'] = []
      for a in attachments_span.findAll('a') :
        if self.fulltext :
          fulltext = self._extractPdfText(self.host + a['href'])
        else:
          fulltext = ''

        details[u'Attachments'].append(
          {'url': self.host + a['href'],
           'label': a.text,
           'fulltext' : fulltext }
          )

    sponsors_span = soup.find('span', id='ctl00_ContentPlaceHolder1_lblSponsors2')
    sponsors = []
    if sponsors_span is not None :
      if self.sponsor_links:
        for a in sponsors_span.findAll('a') :
          sponsors.append(a.text)
      else:
        sponsors = sponsors_span.text.split(',')
    details[u'Sponsors'] = sponsors

    topics_span = soup.find('span', id='ctl00_ContentPlaceHolder1_lblIndexes2')
    topics = []
    if topics_span is not None :
      topics = [topic.strip() for topic in topics_span.text.split(',')]
    details[u'Topics'] = topics

    related_file_span = soup.find('span', {'id' : 'ctl00_ContentPlaceHolder1_lblRelatedFiles2' })
    if related_file_span is not None:
      details[u'Related files:'] = ','.join([
        self.host + a['href']
        for a in related_file_span.findAll('a')])

    # Break down the history table
    history_table = soup.find('div', id='ctl00_ContentPlaceHolder1_pageHistory').fetch('table')[1]
    history = []
    for event, headers, row in self.parseDataTable(history_table):
      for key, val in event.items():
        if isinstance(val, dict) and val['url'].startswith('HistoryDetail.aspx'):
          event['URL'] = self.host + val['url']
      history.append(event)

    return details, history

  def parseHistoryDetail(self, soup):
    # Pull out the top matter
    detail_div = soup.find('div', {'id' : 'ctl00_ContentPlaceHolder1_pageTop1'})
    details = self._get_general_details(detail_div, label_suffix='Prompt', value_suffix='')

    # Break down the votes table
    votes_table = soup.find('div', id='ctl00_ContentPlaceHolder1_gridVote').find('table')
    votes = []
    for vote, headers, row in self.parseDataTable(votes_table):
      votes.append(vote)

    return details, votes

  def councilMembers(self, follow_links=True) :
    br = self._get_new_browser()
    response = br.open(self._people_uri)

    # Loop through the pages, yielding each of the results
    all_results = False
    while all_results is False :
      soup = BeautifulSoup(response.read())
      table = soup.find('table', id='ctl00_ContentPlaceHolder1_gridPeople_ctl00')

      for councilman, headers, row in self.parseDataTable(table):

        if follow_links and type(councilman['Person Name']) == dict :
          detail_url = self.host + councilman['Person Name']['url']
          response = br.open(detail_url)
          soup = BeautifulSoup(response.read())
          img = soup.find('img', {'id' : 'ctl00_ContentPlaceHolder1_imgPhoto'})
          if img :
            councilman['Photo'] = self.host + img['src']

        yield councilman

      current_page = soup.fetch('a', {'class': 'rgCurrentPage'})
      if current_page :
        current_page = current_page[0]
        next_page = current_page.findNextSibling('a')
      else :
        next_page = None

      if next_page :
        print 'reading page', next_page.text
        print
        event_target = next_page['href'].split("'")[1]
        print event_target
        br.select_form('aspnetForm')
        data = self._data(br.form, event_target)

        # del data['ctl00$ContentPlaceHolder1$gridPeople$ctl00$ctl02$ctl01$ctl01']
        # data['__ASYNCPOST'] = True
        # data['__EVENTARGUMENT'] = ''
        # data['__LASTFOCUS'] = ''
        # data['ctl00_ContentPlaceHolder1_tabTop_ClientState'] = '{"selectedIndexes":["0"],"logEntries":[],"scrollState":{}}'
        # data['ctl00_RadScriptManager1_TSM'] = ';;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en-US:89093640-ae6b-44c3-b8ea-010c934f8924:ea597d4b:b25378d2;Telerik.Web.UI, Version=2012.2.912.40, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:6aabe639-e731-432d-8e00-1a2e36f6eee0:16e4e7cd:f7645509:24ee1bba:e330518b:1e771326:8e6f0d33:ed16cbdc:6a6d718d:2003d0b8:c8618e41:58366029'
        # data['ctl00_tabTop_ClientState'] = '{"selectedIndexes":["6"],"logEntries":[],"scrollState":{}}'
        # data['ctl00$RadScriptManager1'] = 'ctl00$ContentPlaceHolder1$ctl00$ContentPlaceHolder1$gridPeoplePanel|ctl00$ContentPlaceHolder1$gridPeople$ctl00$ctl02$ctl00$ctl04'
        # data['RadAJAXControlID'] = 'ctl00_ContentPlaceHolder1_RadAjaxManager1'

        # print data
        data = urllib.urlencode(data)
        response = _try_connect(br, self._people_uri, data)

      else :
        all_results = True

    raise StopIteration

  def councilCalendar(self, search_type='upcoming') :
    br = self._get_new_browser()
    br.open(self._calendar_uri)

    if search_type == 'all' : 
      print 'Scraping all event data'
      br.select_form('aspnetForm')

      br.form.set_all_readonly(False)
      data = self._data(br.form, 'ctl00$ContentPlaceHolder1$lstYears')
      
      # delete extraneous form values
      del data[None]
      del data['ctl00$ContentPlaceHolder1$gridCalendar$ctl00$ctl02$ctl01$ctl02']
      del data['ctl00$ContentPlaceHolder1$gridCalendar$ctl00$ctl02$ctl01$ctl04']

      # search for all years
      data['ctl00$ContentPlaceHolder1$lstYears'] = 'All Years'
      data['ctl00_ContentPlaceHolder1_lstYears_ClientState'] = '{"logEntries":[],"value":"All","text":"All Years","enabled":true,"checkedIndices":[],"checkedItemsTextOverflows":false}'

      data = urllib.urlencode(data)
      response = _try_connect(br, self._calendar_uri, data)

    else :
      response = br.open(self._calendar_uri)


    # Loop through the pages, yielding each of the results
    all_results = False
    while all_results is False :
      soup = BeautifulSoup(response.read())

      table = soup.find('table', id='ctl00_ContentPlaceHolder1_gridCalendar_ctl00')
      for event, headers, row in self.parseDataTable(table):

        if type(event['Agenda']) == dict :
          detail_url = event['Agenda']['url']
          if self.fulltext :
            event['Agenda']['fulltext'] = self._extractPdfText(detail_url)
          else:
            event['Agenda']['fulltext'] = ''

        if type(event['Minutes']) == dict :
          detail_url = event['Minutes']['url']
          if self.fulltext :
            event['Minutes']['fulltext'] = self._extractPdfText(detail_url)
          else:
            event['Minutes']['fulltext'] = ''

        yield event

      current_page = soup.fetch('a', {'class': 'rgCurrentPage'})
      if current_page :
        current_page = current_page[0]
        next_page = current_page.findNextSibling('a')
      else :
        next_page = None

      if next_page :
        print 'reading page', next_page.text
        print
        event_target = next_page['href'].split("'")[1]
        br.select_form('aspnetForm')
        data = self._data(br.form, event_target)
        
        del data[None]
        del data['ctl00$ContentPlaceHolder1$gridCalendar$ctl00$ctl02$ctl01$ctl02']
        del data['ctl00$ContentPlaceHolder1$gridCalendar$ctl00$ctl02$ctl01$ctl04']
        del data['ctl00$ContentPlaceHolder1$chkOptions$1']
        del data['ctl00$ButtonRSS']

        data = urllib.urlencode(data)
        response = _try_connect(br, self._calendar_uri, data)

      else :
        all_results = True

    raise StopIteration
    
    
  def _get_general_details(self, detail_div, label_suffix='', value_suffix='2'):
    """
    Parse the data in the top section of a detail page.
    """
    keys = []
    values = []

    
    for span in detail_div.fetch('span'):
      # key:value pairs are contained within <span> elements that have
      # corresponding ids. The key will have id="ctl00_..._x", and the value
      # will have id="ctl00_..._x2".
      #
      # Look for values and find matching keys. This is not the most
      # efficient solution (should be N^2 time in the number of span elements),
      # but it'll do.
      if span.has_key('id') and span['id'].endswith(value_suffix):
        key = span['id'][:-len(value_suffix)] if value_suffix else span['id']
        label_span = detail_div.find('span', id=(key + label_suffix))
        if label_span:
          label = label_span.text.strip(':')
          value = span.text.replace('&nbsp;', ' ').strip()
          keys.append(label)
          # TODO: Convert to datetime when appropriate
          values.append(value)

      for a in detail_div.fetch('a'):
        if a.has_key('id') and a['id'].endswith(value_suffix):
          key = a['id'][:-len(value_suffix)].replace('hyp', 'lbl')
          label_span = detail_div.find('span', id=key)
          if label_span:
            label = label_span.text.strip(':')
            value = a.text.replace('&nbsp;', ' ').strip()
            keys.append(label)
            # TODO: Convert to datetime when appropriate
            values.append(value)



    details = dict(zip(keys, values))
    return details
  
  def _extractPdfText(self, pdf_data, tries_left=5):
    """
    Given an http[s] URL, a file URL, or a file-like object containing
    PDF data, return the text from the PDF. Cache URLs or data that have
    already been seen.
    """
    print pdf_data
    pdf_key = pdf_data
    if pdf_key.startswith('file://'):
      path = pdf_key[7:]
      pdf_data = open(path).read()
    elif pdf_key.startswith('http://') or pdf_key.startswith('https://'):
      try:
        
        pdf_data = cStringIO.StringIO(urllib2.urlopen(pdf_key).read())

      # Protect against removed PDFs (ones that result in 404 HTTP
      # response code). I don't know why they've removed some PDFs
      # but they have.
      except urllib2.HTTPError, err:
        if err.code == 404:
          return ''
        else:
          raise

      # Been getting timeout exceptions every so often, so try again
      # if timed out.
      except urllib2.URLError, err:
          if tries_left:
            return self._extractPdfText(pdf_key, tries_left-1)

    try:
      doc = slate.PDF(pdf_data)
    except pdfminer.psparser.PSException:
      print 'not a PDF or bad PDF, ignoring it'
      return ''

    return '\n'.join(doc)

  def _unradio(self, control):
    """
    For a radio button or a check box, get the value as a string instead of a
    list. For unchecked checkboxes, simply use an empty string.
    """
    if control.type in ['radio', 'checkbox'] :
      if len(control.value) == 1 :
        return control.value[0]
      else :
        return ''
    else :
      return control.value

  def _data(self, form, event_target=None):
    """
    Get a dictionary mapping {name:value} for each of the inputs in the given
    mechanize browser form.
    """
    data = dict([(control.name, self._unradio(control))
                 for control in form.controls
                 if control.type != 'submit'])

    data.update({'__EVENTTARGET' : event_target})

    return data

  def _get_new_browser(self):
    return mechanize.Browser()

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

  def _switch_to_advanced_search(self, br) :
    br.select_form('aspnetForm')
    data = self._data(br.form, 'ctl00$ContentPlaceHolder1$btnSwitch')
    data['__EVENTARGUMENT'] = ''
    data['ctl00_tabTop_ClientState'] = '{"selectedIndexes":["2"],"logEntries":[],"scrollState":{}}'
    data['ctl00_RadScriptManager1_TSM'] = ';;System.Web.Extensions, Version=4.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35:en-US:89093640-ae6b-44c3-b8ea-010c934f8924:ea597d4b:b25378d2;Telerik.Web.UI, Version=2012.2.912.40, Culture=neutral, PublicKeyToken=121fae78165ba3d4:en-US:6aabe639-e731-432d-8e00-1a2e36f6eee0:16e4e7cd:f7645509:24ee1bba:e330518b:1e771326:8e6f0d33:ed16cbdc:f46195d3:19620875:874f8ea2:39040b5c:f85f9819:2003d0b8:aa288e2d:c8618e41:58366029'

    data = urllib.urlencode(data)
    response = br.open(self._legislation_uri, data)

    try:
      # Check for the link to the advanced search form
      br.find_link(text_regex='.*Simple.*')

    except mechanize.LinkNotFoundError:
      # If it's not there, then we're already on the advanced search form.
      raise ValueError('Not on the advanced search page')


    return br


def _try_connect(br, uri, data=None) :
  response = False
  for attempt in xrange(1,6):
    try:
      response = br.open(uri, data, timeout=30)
      break
    except Exception as e :
      print 'Timed Out'
      print 'sleep for', str(attempt*30)
      time.sleep(attempt*30)
      print e

  if response :
    return response
  else :
    print uri
    raise urllib2.URLError("Timed Out")
