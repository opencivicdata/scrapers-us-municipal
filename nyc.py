from pupa.scrape import Jurisdiction, Organization
from legistar.people import LegistarPersonScraper
import re


class NYCPersonScraper(LegistarPersonScraper):

    EXTRA_FIELDS = ('notes',)
    DEFAULT_PRIMARY_ORG = 'legislature'

    def modify_object_args(self, kwargs, item):
        notes = item.pop('notes')
        try:
            district, party, notes = re.match(
                r'District (\d+) - (?:Council (?:Member|Speaker) - )?(Democrat|Republican)?\s*~?(.*)',
                notes
            ).groups()
        except AttributeError:
            if notes.startswith('I. Daneek Miller'):
                district = '27'
                party = 'Democratic'
            else:
                print('could not parse: {}'.format(notes))
                raise

        if not party and kwargs['name'] == 'Vanessa L. Gibson':
            party = 'Democratic'
        elif party.startswith('Democrat'):
            party = 'Democratic'

        kwargs['district'] = district
        kwargs['party'] = party
        item['notes'] = notes.strip()


class NYC(Jurisdiction):
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ny/place:new_york'
    name = 'New York City'
    timezone = 'America/New_York'
    url = 'http://nyc.gov'

    parties = [
        {'name': 'Democratic'},
        {'name': 'Republican'}
    ]
    scrapers = {'people': NYCPersonScraper}

    def get_organizations(self):
        council = Organization('New York City Council', classification='legislature')
        for x in range(1,52):
            council.add_post(str(x), role='Council Member')
        yield council

    LEGISTAR_ROOT_URL = 'http://legistar.council.nyc.gov/'

    #    EVT_SEARCH_TABLE_TEXT_VIDEO = 'Multimedia'
    #    EVT_DETAIL_TEXT_VIDEO = 'Multimedia'
    #    EVT_DETAIL_TABLE_TEXT_VIDEO = 'Multimedia'

    #    BILL_CLASSIFICATIONS = {
    #        'Introduction': 'bill',
    #        'Local Law': 'bill',
    #        'Resolution': 'resolution',
    #        }

    #    ORG_CLASSIFICATIONS = {
    #        'Land Use': 'committee',
    #        'Subcommittee': 'committee',
    #        'Task Force': 'commission',
    #        'Town Hall Meeting': 'commission',
    #    }

    ##overrides('BillsAdapter.should_drop_sponsor')
    #def should_drop_sponsor(self, data):
    #    '''If this function retruns True, the sponsor obj is exluded from the
    #    sponsors list.
    #    '''
    #    return data['name'] in '(in conjunction with the Mayor)'

    ##overrides('BillsAdapter.gen_subjects')
    #def gen_subjects(self):
    #    name = self.data['name'].strip()
    #    if name:
    #        yield name

    ##overrides('VoteAdapter.classify_motion_text')
    #def classify_motion_text(self, motion_text):
    #    motion_text = motion_text.lower()
    #    if 'amended by' in motion_text:
    #        return ['amendment-passage']
    #    elif 'approved by council' in motion_text:
    #        return ['bill-passage']
    #    return []
