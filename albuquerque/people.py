from pupa.scrape import Scraper, Legislator, Committee
import lxml.html


class PersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self._scrape_committees()
        yield self._scrape_people()

    def _scrape_committees(self):
        url = "http://www.cabq.gov/council/committees"
        page = self.lxmlize(url)
        root = page.xpath("//div[@id='parent-fieldname-text']")[0]
        h3s = root.xpath("./h3")
        ps = root.xpath("./p")[2:]
        uls = root.xpath("./ul")
        for h3, p, ul in zip(h3s, ps, uls):
            name = h3.text_content()
            org = Committee(name=name)
            org.add_source(url)

            for person in ul.xpath(".//li"):
                who = person.text_content()
                title = 'member'
                if ", chair" in who.lower():
                    title = 'chair'
                    who = who.replace(", Chair", "")
                org.add_member(name=who,
                               role=title)
                yield org

    def _scrape_people(self):
        url = 'http://www.cabq.gov/council/councilors'
        page = self.lxmlize(url)
        names = page.xpath("//div[@id='parent-fieldname-text']/*")[3:]
        it = iter(names)
        for entry in zip(it, it, it):
            name, info, _ = entry
            image_small = name.xpath(".//img")[0].attrib['src']
            name = name.text_content()
            infopage, email, policy_analyst = info.xpath(".//a")
            phone = info.xpath(".//b")[-1].tail.strip()
            district = infopage.text_content()
            homepage = self.lxmlize(infopage.attrib['href'])
            photo = homepage.xpath(
                "//div[@class='featureContent']//img"
            )[0].attrib['src']

            bio = "\n".join((x.text_content() for x in homepage.xpath(
                "//div[@class='featureContent']//div[@class='stx']/p")))

            p = Legislator(name=name,
                           post_id=district,
                           image=photo,
                           biography=bio)

            p.add_source(url)
            p.add_source(infopage.attrib['href'])
            yield p
