# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .bills import LametroBillScraper
from .people import LametroPersonScraper
from .events import LametroEventScraper


class Lametro(Jurisdiction):
    division_id = "ocd-division/country:us/state:ca/county:los_angeles"
    classification = "transit_authority"
    name = "Los Angeles County Metropolitan Transportation Authority"
    url = "https://www.metro.net/"
    scrapers = {
        "bills": LametroBillScraper,
        "people": LametroPersonScraper,
        "events": LametroEventScraper,
    }

    legislative_sessions = []
    for year in range(2014, 2019):
        session = {"identifier": "{}".format(year),
                   "start_date": "{}-07-01".format(year),
                   "end_date": "{}-06-30".format(year + 1)}
        legislative_sessions.append(session)


    def get_organizations(self):
        org = Organization(name="Board of Directors", classification="legislature")

        org.add_post('Mayor of the City of Los Angeles',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/place:los_angeles')

        for district in range(1, 6):
            org.add_post('Los Angeles County Board Supervisor, District {}'.format(district),
                         'Board Member',
                         division_id='ocd-division/country:us/state:ca/county:los_angeles/council_district:{}'.format(district))

        org.add_post('Appointee of Mayor of the City of Los Angeles',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/place:los_angeles')

        org.add_post('Appointee of Governor of California',
                     'Nonvoting Board Member',
                     division_id='ocd-division/country:us/state:ca')

        org.add_post('Caltrans District 7 Director, Appointee of Governor of California',
                     'Nonvoting Board Member',  
                     division_id='ocd-division/country:us/state:ca')

        org.add_post('Appointee of Los Angeles County City Selection Committee, North County/San Fernando Valley sector',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:north_county_san_fernando_valley')

        org.add_post('Appointee of Los Angeles County City Selection Committee, Southwest Corridor sector',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:southwest_corridor')


        org.add_post('Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:san_gabriel_valley')

        org.add_post('Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                     'Board Member',
                     division_id='ocd-division/country:us/state:ca/county:los_angeles/la_metro_sector:southeast_long_beach')

        org.add_post('Chair', 'Chair')

        org.add_post('1st Vice Chair', '1st Vice Chair')

        org.add_post('2nd Vice Chair', '2nd Vice Chair')

        org.add_post("Chief Executive Officer", "Chief Executive Officer")

        org.add_source('https://metro.legistar.com/DepartmentDetail.aspx?ID=28529&GUID=44319A1A-B2B7-48CC-B857-ADCE9064573B', note='web')

        yield org

        org = Organization(name="Crenshaw Project Corporation", classification="corporation")
        org.add_source('https://metro.legistar.com/DepartmentDetail.aspx?ID=32216&GUID=D790CC05-ACCB-451C-B576-2952090769F1')
        yield org

        org = Organization(name="LA SAFE", classification="corporation")
        org.add_source('https://metro.legistar.com/DepartmentDetail.aspx?ID=30222&GUID=5F27DA83-633F-4FEA-A4B0-0477551061B6&R=aef57793-1826-4cfa-b6e3-d6b42cf77527')
        yield org
