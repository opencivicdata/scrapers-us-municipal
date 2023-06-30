import scrapelib
import lxml.html
import pprint
import dateutil.parser
import re


class VimeoScraper(scrapelib.Scraper):
    def __init__(self):
        super().__init__()

        data = self.get("https://vimeo.com/_next/viewer").json()
        self.headers["Authorization"] = f"jwt {data['jwt']}"

    def committee_archive_links(self):

        url = "https://www.chicityclerk.com/committee-meeting-video-archives"
        response = self.get(url)

        tree = lxml.html.fromstring(response.text)

        committee_link_elements = tree.xpath(
            ".//article//a[starts-with(@href, 'https://vimeo.com')]"
        )

        committee_links = {}
        for link in committee_link_elements:
            url = link.attrib["href"]
            showcase_number = url.split("/")[-1]
            committee_links[link.text] = {
                "url": url,
                "showcase_number": showcase_number,
            }

        return committee_links

    def committee_archive(self, committee_link):

        # todo is pagingation witht the page attribute

        page = 1
        while True:
            url = f'https://api.vimeo.com/albums/{committee_link["showcase_number"]}/videos'
            params = {
                "page": str(page),
                "sort": "date",
                "direction": "desc",
                "fields": "description,duration,is_free,live,name,pictures.sizes.link,pictures.sizes.width,pictures.uri,privacy.download,privacy.view,content_rating_class,type,uri,user.link,user.name,user.pictures.sizes.link,user.pictures.sizes.width,user.uri",
                "per_page": "100",
                "filter": "",
                "_hashed_pass": "",
            }

            try:
                response = self.get(url, params=params)
            except scrapelib.HTTPError as error:
                # if we paginate beyond the data, we get a 400 status code
                if error.response.status_code == 400:
                    break
                else:
                    raise

            data = response.json()

            for item in data["data"]:

                patterns = (
                    r"^\d{4}[ -]+[A-Za-z.]+ \d{1,2}",  # 2022 Sept 5 - foo
                    r"^[A-Za-z.]+ \d{1,2}[th,\.]* \d{4}",  # Sept 5, 2022 - foo
                    r"^\d{4} \d{1,2} [A-Za-z.]+",  # 2002 5 Sept - foo
                    r"[A-Za-z.]+ \d{1,2},? \d{4}$",  # foo - Sept 5, 2022
                    r"^\d{1,2} [A-Za-z.]+ \d{4}",  # 5 Sept 2022 - foo
                )

                name = item["name"]
                date_str = None

                for pattern in patterns:
                    try:
                        date_str = re.search(pattern, name).group()
                    except AttributeError:
                        continue
                    else:
                        break
                else:
                    no_dates = {
                        "Joint Committee: Housing and Real Estate; Zoning, Landmarks and Building Standards"
                    }
                    if name in no_dates:
                        continue
                    else:
                        raise ValueError(
                            f"Could not extract a date from '{name}' with any existing pattern"
                        )

                url = (committee_link["url"] + item["uri"]).replace("videos", "video")
                date = dateutil.parser.parse(date_str).date()

                yield {"date": date, "url": url}

            page += 1


if __name__ == "__main__":
    import pprint

    scraper = VimeoScraper()

    for committee, archive_url in scraper.committee_archive_links().items():
        for video in scraper.committee_archive(archive_url):
            print(video)
