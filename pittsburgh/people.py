import collections

from pupa.scrape import Person, Organization, Scraper
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper


class PittsburghPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = "http://webapi.legistar.com/v1/pittsburgh"
    WEB_URL = "https://pittsburgh.legistar.com"
    TIMEZONE = "America/New_York"

    # Override method in LegistarAPIPersonScraper class to pull in contact
    # info from call to /persons/PersonId endpoint

    def person_sources_from_office(self, office):
        person_api_url = (self.BASE_URL +
                          "/persons/{OfficeRecordPersonId}".format(**office))
        response = self.get(person_api_url)
        person_api_response = self.get(person_api_url).json()

        return person_api_url, person_api_response

    def scrape(self):
        body_types = self.body_types()
        city_council, = [body for body in self.bodies()
                         if body["BodyName"] == "City Council"]
        terms = collections.defaultdict(list)

        for office in self.body_offices(city_council):
            if "VACAN" not in office["OfficeRecordFullName"]:
                terms[office["OfficeRecordFullName"].strip()].append(office)

        web_scraper = LegistarPersonScraper(requests_per_minute=self.requests_per_minute)
        web_scraper.MEMBERLIST = "https://pittsburgh.legistar.com/People.aspx"
        web_scraper.COMMITTEELIST = "https://pittsburgh.legistar.com/Departments.aspx"

        if self.cache_storage:
            web_scraper.cache_storage = self.cache_storage

        if self.requests_per_minute == 0:
            web_scraper.cache_write_only = False

        web_info = {}
        for member in web_scraper.councilMembers():
            web_info[member["Person Name"]] = member

        members = {}
        for member, offices in terms.items():
            person = Person(member)
            for term in offices:
                role = term["OfficeRecordTitle"]
                person.add_term("Councilmember",
                                "legislature",
                                start_date = self.toDate(term["OfficeRecordStartDate"]),
                                end_date = self.toDate(term["OfficeRecordEndDate"]))

            if member in web_info:
                web = web_info[member]
                if web["E-mail"] and web["E-mail"]["label"] and web["E-mail"]["label"] != "N/A":
                    person.add_contact_detail(type="email",
                                        value=web["E-mail"]["label"],
                                        note="E-mail")

            person_source_data = self.person_sources_from_office(term)
            person_api_url, person_api_response = person_source_data
            person.add_source(person_api_url, note="api")

            if person_api_response["PersonAddress1"]:
                address = (person_api_response["PersonAddress1"] + ", " + person_api_response["PersonCity1"]
                          + ", " + person_api_response["PersonState1"] + " " + person_api_response["PersonZip1"])
                person.add_contact_detail(type="address",
                                    value=address,
                                    note="Office address")

            if person_api_response["PersonPhone"]:
                person.add_contact_detail(type="voice",
                                    value=person_api_response["PersonPhone"],
                                    note="Office phone")

            if person_api_response["PersonWWW"]:
                person.add_contact_detail(type="url",
                                    value=person_api_response["PersonWWW"],
                                    note="District website")

            members[member] = person


        for body in self.bodies():
            if body["BodyTypeId"] == body_types["Committee"]:
                body_name_clean = body["BodyName"].strip()
                organization = Organization(body_name_clean,
                             classification="committee",
                             parent_id={"name" : "Pittsburgh City Council"})

                organization.add_source(self.BASE_URL + "/bodies/{BodyId}".format(**body), note="api")

                for office in self.body_offices(body):
                    role = office["OfficeRecordMemberType"]
                    if role not in ("Vice Chair", "Chair") or role == "Councilmember":
                        role = "Member"

                    person = office["OfficeRecordFullName"].strip()
                    if person in members:
                        person = members[person]
                    else:
                        person = Person(person)

                    person.add_membership(body_name_clean,
                                     role=role,
                                     start_date = self.toDate(office["OfficeRecordStartDate"]),
                                     end_date = self.toDate(office["OfficeRecordEndDate"]))

                yield organization

        for person in members.values():
            yield person
