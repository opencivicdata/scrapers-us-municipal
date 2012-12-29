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
    self.uri = 'http://%s/' % self.config['hostname']

    # Assume that the legislation and calendar URLs are constructed regularly.
    self._legislation_uri = (
      self.uri + self.config.get('legislation_path', 'Legislation.aspx'))
    self._calendar_uri = (
      self.uri + self.config.get('calendar_path', 'Calendar.aspx'))

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
    headers = table.fetch('th')
    legislation_rows = table.fetch('tr', {'id':re.compile('ctl00_ContentPlaceHolder1_gridMain_ctl00__')})
    print "found some legislation!"
    print len(legislation_rows)

    keys = {}
    index = 0
    for index, header in enumerate(headers):
      keys[index] = header.text.replace('&nbsp;', ' ').strip()

    for row in legislation_rows:
      try:
        legislation = {}
        parse_dates = ('date_format' in self.config)
        for index, field in enumerate(row.fetch("td")):
          key = keys[index]
          value = field.text.strip()
          if parse_dates:
            try:
              value = datetime.datetime.strptime(value, self.config['date_format'])
            except ValueError:
              pass
          legislation[key] = value

        path = row.fetch("a")[0]['href'].split('&Options')[0]
        legislation['URL'] = self.uri + path

        yield legislation
      except KeyError:
        print 'Problem row:'
        print row
        pass

  def expandLegislationSummary(self, summary):
    """
    Take a row as given from the searchLegislation method and retrieve the
    details of the legislation summarized by that row.
    """
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
    return self.parseLegislationDetail(soup)

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

    try:
      details[u'Attachments:'] = ','.join([a['href'] for a in soup.fetch('span', {'id' : 'ctl00_ContentPlaceHolder1_lblAttachments2' })[0].findAll('a')])
    except IndexError :
      pass

    try:
      details[u'Related files:'] = ','.join([a['href'] for a in soup.fetch('span', {'id' : 'ctl00_ContentPlaceHolder1_lblRelatedFiles2' })[0].findAll('a')])
    except IndexError :
      pass



    history_row = soup.fetch('tr', {'id' : re.compile('ctl00_ContentPlaceHolder1_gridLegislation_ctl00')})

    history_keys = ["date", "journal_page", "action_by", "status", "results", "votes", "meeting_details"]

    history = []

    for row in history_row :
      values = []
      for key, cell in zip(history_keys, row.fetch('td')) :
        if key == 'meeting_details' :
          try:
            values.append(cell.a['href'])
          except KeyError:
            values.append('')
        elif key == 'votes' :
          try:
            values.append(cell.a['onclick'].split("'")[1])
          except KeyError:
            values.append('')
        elif key == 'date':
          try:
            values.append(datetime.datetime.strptime(cell.text.replace('&nbsp;', ' ').strip(), '%m/%d/%Y'))
          except ValueError:
            values.append('')
        else:
          values.append(cell.text.replace('&nbsp;', ' ').strip())


      history.append(dict(zip(history_keys, values)))


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
