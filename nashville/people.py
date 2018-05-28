import datetime
from pupa.scrape import Person

from .utils import NashvilleScraper


class NashvillePersonScraper(NashvilleScraper):

    def scrape(self):
        yield from self.get_mayor_and_staff()
        yield from self.get_city_council()

    def get_mayor_and_staff(self):
        base_url = 'http://www.nashville.gov/Mayors-Office.aspx'
        doc = self.lxmlize(base_url)

        # Yield mayor
        (name, *summary, bio, email_updates) = doc.xpath(
            '//div[@id="dnn_ctr15874_HtmlModule_lblContent"]/descendant::*/text()')
        (bio_doc_link, ) = doc.xpath(
            '//div[@id="dnn_ctr15874_HtmlModule_lblContent"]/descendant::*/a[contains(@href, "/Mayors-Biography.aspx")]/@href')
        bio_doc = self.lxmlize(bio_doc_link)
        (name, *biography, image) = bio_doc.xpath(
            '//div[@id="dnn_ctr3974_HtmlModule_lblContent"]/descendant::*/text()')

        (image_url, ) = bio_doc.xpath(
            '//div[@id="dnn_ctr3974_HtmlModule_lblContent"]/descendant::*/a[@target="_blank"]/@href')

        mayor = Person(name=name,
                       image=image_url,
                       primary_org='executive',
                       role='Mayor',
                       summary=''.join(summary),
                       biography=''.join(biography),
                       )

        mayor.add_source(bio_doc_link)
        yield mayor

        # Yield Staff
        staff_table_rows = doc.xpath(
            '//div[@class="widget-container"]/div/table/tbody/tr')
        # TODO: Add contact details
        for row in staff_table_rows:
            (name, ) = row.xpath('./td/a/text()')
            (link, ) = row.xpath('./td/a/@href')
            (title, ) = row.xpath('./td/span/text()')
            (last, first) = name.split(',')
            formated_name = '{} {}'.format(first.strip(), last)
            staff = Person(name=formated_name,
                           primary_org='executive',
                           role=title)

            staff.add_source(link)
            yield staff

    def get_city_council(self):
        base_url = 'http://www.nashville.gov/Metro-Clerk/Metropolitan-Council/Council-Members.aspx'
        doc = self.lxmlize(base_url)
        council_member_rows = doc.xpath(
            '//table[@id="CouncilRoster"]/tbody/tr')
        # Skip the first row where the children are <th>
        council_member_rows = council_member_rows[1::]
        for row in council_member_rows:
            role = 'councilmember'
            (title_element, link_element, address_element,
             work_element, home_element) = row.xpath('./td')
            (title, *rest) = title_element.xpath('./text()')
            try:
                (link,) = link_element.xpath('./a/@href')
            except ValueError:
                # Vacant seats have no url we an skip
                continue

            (name, ) = link_element.xpath('./a/text()')
            contact_details = []
            formatted_address = self.strip_string_array(
                address_element.xpath('./text()'))
            (work_phone, ) = work_element.xpath('./text()')
            (home_phone, ) = home_element.xpath('./text()')
            contact_details.append(
                {'note': 'home', 'type': 'address', 'value': formatted_address, 'label': 'Address'})
            contact_details.append(
                {'note': 'home', 'type': 'voice', 'value': home_phone, 'label': 'Home Phone Number'})
            contact_details.append(
                {'note': 'work', 'type': 'voice', 'value': work_phone, 'label': 'Work Phone Number'})

            council_member_doc = self.lxmlize(link)
            (dnn_name, ) = council_member_doc.xpath(
                '//div[@id="dnn_ContentPane"]/div/a/@name')
            info_div_id = 'dnn_ctr{}_HtmlModule_lblContent'.format(dnn_name)
            (data_div, ) = council_member_doc.xpath(
                '//div[@id="{}"]'.format(info_div_id))
            (image_url,) = data_div.xpath('./p/img/@src')
            if ('Vice Mayor' in title):
                role = title

            council_member = Person(name=name,
                                    image=image_url,
                                    primary_org='executive',
                                    role=role,
                                    )
            council_member.contact_details = contact_details
            council_member.add_source(link)
            yield council_member
