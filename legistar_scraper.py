import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
import re
import time
import datetime
import mechanize
from collections import defaultdict

class LegistarScraper :
  """
  A programatic interface onto a hosted Legistar website.
  """

  def __init__(self, config):
    """
    Construct a new Legistar scraper.  Pass in the host name of the Legistar
    instance, e.g. 'phila.legistar.com'.
    """
    self.config = config
    self.host = 'http://%s/' % self.config['hostname']

    # Assume that the legislation and calendar URLs are constructed regularly.
    self._legislation_uri = (
      self.host + self.config.get('legislation_path', 'Legislation.aspx'))
    self._calendar_uri = (
      self.host + self.config.get('calendar_path', 'Calendar.aspx'))

  def searchLegislation(self, search_text, last_date=None, num_pages = None):
    """
    Submit a search query on the legislation search page, and return a list
    of summary results.
    """
    br = self._get_new_browser()
    br.open(self._legislation_uri)
    br.select_form('aspnetForm')

    try:
      # Check for the link to the advanced search form
      br.find_link(text_regex='Advanced.*')

    except mechanize.LinkNotFoundError:
      # If it's not there, then we're already on the advanced search form.
      pass

    else:
      # If it is there, the navigate to the advanced search form.
      data = self._data(br.form, None)
      data['ctl00$ContentPlaceHolder1$btnSwitch'] = ''
      data = urllib.urlencode(data)

      br.open(self._legislation_uri, data)
      br.select_form('aspnetForm')

    # Enter the search parameters
    # TODO: Each of the possible form fields should be represented as keyword
    # arguments to this function. The default query string should be for the
    # the default 'Legislative text' field.
    br.form['ctl00$ContentPlaceHolder1$txtTit'] = search_text

    if last_date :
      br.form.set_all_readonly(False)
      br.form['ctl00$ContentPlaceHolder1$radFileCreated'] = ['>']
      br.form['ctl00_ContentPlaceHolder1_txtFileCreated1_dateInput_ClientState'] = '{"enabled":true,"emptyMessage":"","validationText":"%s-00-00-00","valueAsString":"%s-00-00-00","minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}' % (last_date, last_date)

    # Submit the form
    data = self._data(br.form, None)
    data['ctl00$ContentPlaceHolder1$btnSearch'] = 'Search Legislation'
    data = urllib.urlencode(data)

    response = br.open(self._legislation_uri, data)

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
        response = br.open(self._legislation_uri, data)

      else :
        all_results = True

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
      legislation_id = legislation[id_key]['label']
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
          value = field.text.strip()

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
              value = {'label': value, 'url': address}

          data[key] = value

        yield data, keys, row
      except Exception as e:
        print 'Problem parsing row:'
        print row
        raise e

  def expandLegislationSummary(self, summary):
    """
    Take a row as given from the searchLegislation method and retrieve the
    details of the legislation summarized by that row.
    """
    return self.expandSummaryRow(summary, self.parseLegislationDetail)

  def expandSummaryRow(self, summary, parse_function):
    detail_uri = summary['URL']

    br = self._get_new_browser()
    connection_complete = False

    for attempt in xrange(5):
      try:
        response = br.open(detail_uri, timeout=30)
        connection_complete = True
        break
      except Exception as e :
        print 'Timed Out'
        print e

    if not connection_complete:
      return None

    f = response.read()
    soup = BeautifulSoup(f)
    return parse_function(soup)

  def parseLegislationDetail(self, soup):
    """Take a legislation detail page and return a dictionary of
    the different data appearing on the page

    Example URL: http://chicago.legistar.com/LegislationDetail.aspx?ID=1050678&GUID=14361244-D12A-467F-B93D-E244CB281466&Options=ID|Text|&Search=zoning
    """
    detail_div = soup.find('div', {'id' : 'ctl00_ContentPlaceHolder1_pageDetails'})
    keys = []
    values = []
    i = 0

    for span in detail_div.fetch('span'):
      # key:value pairs are contained within <span> elements that have
      # corresponding ids. The key will have id="ctl00_..._x", and the value
      # will have id="ctl00_..._x2".
      #
      # Look for values and find matching keys. This is not the most
      # efficient solution (should be N^2 time in the number of span elements),
      # but it'll do.
      if span.has_key('id') and span['id'].endswith('2'):
        key = span['id'][:-1]
        label_span = detail_div.find('span', id=key)
        if label_span:
          label = label_span.text.strip(':')
          value = span.text.replace('&nbsp;', ' ').strip()
          keys.append(label)
          values.append(value)

    details = defaultdict(str)
    details.update(dict(zip(keys, values)))

    attachments_span = soup.find('span', id='ctl00_ContentPlaceHolder1_lblAttachments2')
    if attachments_span is not None:
      details[u'Attachments'] = [
        {'url': a['href'], 'label': a.text}
        for a in attachments_span.findAll('a')
      ]

    try:
      details[u'Related files:'] = ','.join([a['href'] for a in soup.fetch('span', {'id' : 'ctl00_ContentPlaceHolder1_lblRelatedFiles2' })[0].findAll('a')])
    except IndexError :
      pass

    history_table = soup.find('div', id='ctl00_ContentPlaceHolder1_pageHistory').fetch('table')[1]
    history = []
    for event, headers, row in self.parseDataTable(history_table):
      for key, val in event.items():
        if isinstance(val, dict) and val['url'].startswith('HistoryDetail.aspx'):
          event['URL'] = self.host + val['url']
      history.append(event)

    return details, history





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
