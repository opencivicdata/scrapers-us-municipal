from pupa.scrape import Scraper
from pupa.scrape import Person

import lxml.html
class MiamidadePersonScraper(Scraper):

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def scrape(self):
        yield from self.get_people()
        #committees can go in here too


    def get_people(self):
        people_base_url = "http://miamidade.gov/wps/portal/Main/government"
        doc = self.lxmlize(people_base_url)
        person_list = doc.xpath("//div[contains(@id,'elected')]//span")
        titles = ["Chairman","Vice Chair"]
        for person in person_list:
            info = person.text_content().strip().split("\r")
            position = info[0].strip()
            name = " ".join(info[1:-1])
            name = name.replace("Website | Contact", "")
            for title in titles:
                name = name.replace(title,"")
            name = name.strip()
            url = person.xpath(".//a[contains(text(),'Website')]/@href")[0]
            image = person.xpath(".//img/@src")[0]
            if position.startswith('District'):
                pers = Person(name=name,
                              image=image,
                              district=position+" Commissioner",
                              primary_org='legislature',
                              role="Commissioner")
            else:
                pers = Person(name=name,
                              image=image,
                              district=position,
                              primary_org='legislature',
                              role=ROLES[position])

                
            pers.add_source(people_base_url, note="Miami-Dade government website")
            pers.add_source(url, note="individual's website")

            #the commissioners have consistent site format
            if "district" in position.lower():
                person_doc = self.lxmlize(url)
                contact_rows = person_doc.xpath("//div[@class='leftContentContainer']//p")
                for line in contact_rows:
                    line_text = line.text_content()
                    if "email" in line_text.lower():
                        email_address = line_text.replace("Email:","").strip()
                        pers.add_contact_detail(type="email",
                                                value=email_address)
                        continue
                    try:
                        office,phone,fax = line_text.strip().split("\n")
                    except ValueError:
                        #ick, it's all on one line.
                        if "downtown office" in line_text.lower():
                            office = "Downtown Office"
                        elif "district office" in line_text.lower():
                            office = "District Office"
                        else:
                            continue
                        phone = line_text[15:27]
                        fax = line_text[33:45]

                    if "office" not in office.lower():
                        continue
                        #social is also available in here
                        #but I don't see a place to put it
                    phone = phone.replace("Phone","").strip()
                    fax = fax.replace("Fax","").strip()
                    pers.add_contact_detail(type="voice", #phone is not allowed ????
                            value=phone,
                            note=office.strip())

                    pers.add_contact_detail(type="fax", #phone is not allowed ????
                            value=fax,
                            note=office.strip())


            yield pers

            
ROLES = {'Office of the Mayor' : 'Mayor',
         'Clerk, Circuit and County Courts' : 'Clerk, Circuit and County Courts',
         'Property Appraiser': 'Property Appraiser'}
