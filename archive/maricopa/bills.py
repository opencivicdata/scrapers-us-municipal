from os.path import join, abspath, dirname

import sh
import lxml.html
from libmproxy import proxy, flow

from pupa.utils.legistar import LegistarScraper
from pupa.scrape import Bill


class BillScraper(LegistarScraper):
    url = 'https://maricopa.legistar.com/Legislation.aspx'
    columns = (
        'bill_id', 'type', 'status',
        'created', 'action', 'title')
