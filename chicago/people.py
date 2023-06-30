import datetime

from pupa.scrape import Organization, Person, Scraper

from .base import ElmsAPI


class ChicagoPersonScraper(ElmsAPI, Scraper):
    def _bodies(self, filters):
        for body in self._paginate(
            self._endpoint("/body"),
            {"filter": filters},
        ):
            yield body

    def scrape(self, window=None):

        (city_council,) = self._bodies("bodyType eq 'Full City Council'")

        alders = {}

        for term in city_council["members"]:
            person_name = term["displayName"].strip()
            if "vacant" in person_name.lower():
                continue

            if person_name in alders:
                person = alders[person_name]
            else:
                alders[person_name] = person = Person(person_name)
                person.extras["personId"] = term["personId"]

            person.add_term(
                "Alderman",
                "legislature",
                district=f"Ward {term['ward']}",
                start_date=datetime.datetime.fromisoformat(term["startDate"]).date(),
                end_date=datetime.datetime.fromisoformat(term["endDate"]).date(),
            )

        for person in alders.values():
            person_url = self._endpoint(f"/person/{person.extras['personId']}")
            person.add_source(person_url, note="api")

            response = self.get(person_url)
            person_details = response.json()

            if image := person_details["photo"]:
                person.image = image

            if web_site := person_details["site"]:
                person.add_link(web_site.strip())

            if email := person_details["email"]:
                person.add_contact_detail(type="email", value=email, note="E-mail")

            if ward_phone := person_details["phone"]:
                person.add_contact_detail(
                    type="voice", value=ward_phone, note="Ward Office Phone"
                )

            if ward_fax := person_details["fax"]:
                person.add_contact_detail(
                    type="fax", value=ward_fax, note="Ward Office Fax"
                )

            if ward_street_number := person_details["address"]:
                ward_address = f'{ward_street_number}\n{person_details["city"]}, {person_details["state"]} {person_details["zip"]}'
                person.add_contact_detail(
                    type="address", value=ward_address, note="Ward Office Address"
                )

            if city_hall_phone := person_details["phone2"]:
                person.add_contact_detail(
                    type="voice", value=city_hall_phone, note="City Hall Office Phone"
                )

            if city_hall_fax := person_details["fax"]:
                person.add_contact_detail(
                    type="fax", value=city_hall_fax, note="City Hall Office Fax"
                )

            if city_hall_street_number := person_details["address2"]:
                city_hall_address = f'{city_hall_street_number}\n{person_details["city2"]}, {person_details["state2"]} {person_details["zip2"]}'
                person.add_contact_detail(
                    type="address",
                    value=city_hall_address,
                    note="City Hall Office Address",
                )

        for body in self._bodies("bodyType eq 'Committee'"):

            org = Organization(
                body["body"],
                classification="committee",
                parent_id={"name": "Chicago City Council"},
            )

            org.add_source(self._endpoint(f'/body/{body["bodyId"]}'), note="api")

            for term in body["members"]:
                person_name = term["displayName"].strip()
                if person_name in {"Allen, Thomas"}:
                    continue
                person = alders[person_name]
                person.add_membership(
                    body["body"],
                    role="Member",
                    start_date=datetime.datetime.fromisoformat(
                        term["startDate"]
                    ).date(),
                    end_date=datetime.datetime.fromisoformat(term["endDate"]).date(),
                )

            yield org

        for body in self._bodies("bodyType eq 'Joint Committee'"):

            org = Organization(
                body["body"],
                classification="committee",
                parent_id={"name": "Chicago City Council"},
            )

            org.add_source(self._endpoint(f'/body/{body["bodyId"]}'), note="api")

            yield org

        for person in alders.values():
            yield person
