import scrapelib
import lxml.html
import json
import re
import pprint
import dateutil.parser

class VimeoScraper(scrapelib.Scraper):
    def committee_archive_links(self):

        url = "https://www.chicityclerk.com/committee-meeting-video-archives"
        response = self.get(url)

        tree = lxml.html.fromstring(response.text)

        committee_link_elements = tree.xpath(
            ".//article//a[starts-with(@href, 'https://vimeo.com')]"
        )
        committee_links = {
            link.text: link.attrib["href"] for link in committee_link_elements
        }

        return committee_links

    def committee_archive(self, url):

        response = self.get(url)
        json_string = re.search('(\[{"itemListElement".*?) </script>', response.text).group(1)

        data, = json.loads(json_string)

        for item in data['itemListElement']:
            name = item["name"]
            url = item["embedUrl"].split('?')[0]
            date_str, committee_name = name.split(' - ')
            date = dateutil.parser.parse(date_str).date()

            yield {"committee_name": name, "date": date, "url": url}
            

if __name__ == "__main__":
    import pprint

    scraper = VimeoScraper()

    for committee, archive_url in scraper.committee_archive_links().items():
        for video in scraper.committee_archive(archive_url):
            print(video)
        break
