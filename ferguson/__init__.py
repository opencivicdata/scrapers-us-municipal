from pupa.scrape import Jurisdiction, Organization

from .people import FergusonPersonScraper


class Ferguson(Jurisdiction):
    division_id = 'ocd-division/country:us/state:mo/place:ferguson'
    classification = 'council'
    name = 'Ferguson City Council'
    url = 'http://www.fergusoncity.com/56/Government'
    parties = []

    scrapers = {
        "people": FergusonPersonScraper,
    }

    def get_organizations(self):
        org = Organization(name="Ferguson City Council",
                           classification="legislature")

        org.add_contact_detail(
            type='email',
            value='citycouncil@fergusoncity.com'
        )

        org.add_post(
            label="Mayor",
            role="Mayor",
            division_id=self.division_id
        )

        WARDS = 3
        for ward in range(1, WARDS + 1):
            org.add_post(
                label="Council Member Ward {}".format(ward),
                role="Council Member Ward {}".format(ward),
                division_id=self.division_id,
                num_seats=2
            )
        yield org
