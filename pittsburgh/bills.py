from legistar.bills import LegistarBillScraper, LegistarAPIBillScraper
from pupa.scrape import Bill, VoteEvent, Scraper
from pupa.utils import _make_pseudo_id
import datetime
import itertools
import pytz
import requests

def sort_actions(actions):
    action_time = 'MatterHistoryActionDate'
    action_name = 'MatterHistoryActionName'
    sorted_actions = sorted(actions,
                            key = lambda x: (x[action_time].split('T')[0],
                                             ACTION[x[action_name]]['order'],
                                             x[action_time].split('T')[1]))

    return sorted_actions

class PittsburghBillScraper(LegistarAPIBillScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/pittsburgh'
    BASE_WEB_URL = 'https://pittsburgh.legistar.com'
    TIMEZONE = "US/Eastern"

    VOTE_OPTIONS = {'yea' : 'yes',
                    'rising vote' : 'yes',
                    'nay' : 'no',
                    'recused' : 'excused'}
