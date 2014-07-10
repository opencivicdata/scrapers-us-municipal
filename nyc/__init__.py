from pupa.scrape import Jurisdiction

from legistar.ext.pupa import (
    LegistarPeopleScraper, LegistarEventsScraper, LegistarBillsScraper,
    generate_orgs)


class NewYorkCity(Jurisdiction):
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ny/place:new_york'
    name = 'New York City'
    url = 'http://council.nyc.gov/'
    parties = [{'name': 'Democratic' }, {'name': 'Republican' }]

    legislative_sessions = [
        {'name': '2014', 'identifier': '2014'},
        ]

    scrapers = {
        "people": LegistarPeopleScraper,
        "events": LegistarEventsScraper,
        "bills": LegistarBillsScraper,
    }

    def get_organizations(self):
        for org in generate_orgs(pupa_jurisdiction=self):
            if org.classification != 'legislature':
                yield org
                continue

            # NYC Council has 51 districts, each with the integer as an id.
            for district in range(1, 52):
                org.add_post(
                    label='District %d' % district, role='Council Member')

            yield org