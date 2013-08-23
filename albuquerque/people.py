from pupa.scrape import Scraper
from pupa.models import Person, Organization


class PersonScraper(Scraper):

    def get_people(self):
        # committee
        tech = Organization('Technology')
        tech.add_post('Chairman', 'chairman')
        tech.add_source('https://example.com')
        yield tech

        # subcommittee
        ecom = Organization('Subcommittee on E-Commerce', parent=tech)
        ecom.add_source('https://example.com')
        yield ecom

        p = Person('Paul Tagliamonte', district='6', chamber='upper')
        p.add_membership(tech, role='chairman')
        p.add_source('https://example.com')
        yield p
