from pupa.scrape import Scraper
from pupa.scrape import Bill
import lxml.html
from lxml import etree
from datetime import datetime


class MiamidadeBillScraper(Scraper):

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def key_and_value(self,content,info_dict):
        if content.strip():
            key,val = content.split(":",1)
            if val.strip():
                info_dict[key.strip()] = val.strip()



    def matter_table_to_dict(self, page):
        info_dict = {}
        info_table = page.xpath("//body/table")[1]
        table_rows = info_table.xpath("./tr")
        for row in table_rows:
            tds = row.xpath("./td")
            for td in tds:
                inner_table = td.xpath("./table")
                if len(inner_table) == 0:
                    self.key_and_value(td.text_content(),info_dict)

                else:
                    for inner_row in inner_table[0].xpath("./tr"):
                        innermost_tables = inner_row.xpath(".//table")
                        if len(innermost_tables) > 0:
                            #deal with weird multi-row values
                            #which have extra tables.
                            for t in innermost_tables:
                                innermost_trs = t.xpath(".//tr")
                                for innermost_tr in innermost_trs:
                                    innermost_tds = innermost_tr.xpath(".//td")
                                    potential_key = innermost_tds[0].text_content()
                                    if ":" in potential_key:
                                        key = potential_key.replace(":","").strip()
                                        info_dict[key.strip()] = []
                                    value = innermost_tds[1].text_content().strip()
                                    if value:
                                        info_dict[key].append(value)

                        else:
                            multirow = False #sometimes fields span two TDs. arg.
                            for inner_td in inner_row.xpath("./td"):
                                content = inner_td.text_content()
                                if multirow:
                                    self.key_and_value(prev_content+content,
                                        info_dict)
                                    multirow = False
                                elif "Title:" in content or "Notes:" in content:
                                    prev_content = content
                                    multirow = True
                                else:
                                    self.key_and_value(content, info_dict)

        return info_dict

    def process_action_table(self,page,bill):
        try:
            action_table = page.xpath("//table//td//strong[text()='Legislative History']")[0]
        except IndexError:
            self.warning("Bill has no actions")
            return

        action_table = action_table.getparent().getparent().getparent().getparent()
        trs = action_table.xpath(".//tr")
        for tr in trs[2:]:
            content = tr.text_content().strip()
            if content and not (content.startswith("REPORT")):
                tds = tr.xpath("./td")
                actor = tds[0].text_content().strip()
                date = tds[1].text_content().strip()
                if date:
                    date = datetime.strptime(date,"%m/%d/%Y")
                    date = "-".join([str(date.year),
                                    str(date.month).zfill(2),
                                    str(date.day).zfill(2)])

                else:
                    self.warning("Action without a date, skipping")
                    continue
                action = tds[3].text_content().strip()
                sent_to = tds[4].text_content().strip()
                if action and sent_to:
                    action = action + " to " + sent_to

                if action == "Adopted":
                    bill.add_action(action, date,
                        classification="passage")
                else:
                    bill.add_action(action, date)

                returned = tds[6].text_content().strip()
                if returned:
                    return_date = datetime.strptime(returned,"%m/%d/%Y")
                    return_date = "-".join([str(return_date.year),
                                            str(return_date.month).zfill(2),
                                            str(return_date.day).zfill(2)])
                    bill.add_action("Returned by {sent_to}".format(sent_to=sent_to),
                        return_date)



    def scrape(self):
        #need to figure out reasonable dates for each session
        #for now just throwing in recent ones.
        start_date = "11-24-2014"
        end_date = "11-24-2015"
        base_url = ("http://www.miamidade.gov/govaction/Legislative.asp?begdate={start_date}" +
                    "&enddate={end_date}&MatterType=AllMatters&submit1=Submit")
        scrape_url = base_url.format(start_date=start_date,end_date=end_date)
        doc = self.lxmlize(scrape_url)
        matters = doc.xpath("//a[contains(@href,'matter.asp')]/@href")
        for matter_link in matters:
            yield self.scrape_matter(matter_link)

    def scrape_matter(self, matter_link):
        matter_types = {
        "Additions":"other",
        "Administrative Order":"order",
        "Annual Evaluation":"other",
        "Bid Advertisement":"other",
        "Bid Awards":"other",
        "Bid Contract":"contract",
        "Bid Protest":"other",
        "Bid Rejection":"other",
        "Birthday Scroll":"commemoration",
        "Certificate of Appreciation":"commemoration",
        "Change Order":"order",
        "Citizen's Presentation":"other",
        "Commendation":"commemoration",
        "Conflict Waiver":"other",
        "Congratulatory Certificate":"commemoration",
        "Deferrals":"other",
        "Discussion Item":"other",
        "Distinguished Visitor":"other",
        "Joint Meeting/Workshop":"other",
        "Mayoral Veto":"other",
        "Miscellaneous":"other",
        "Nomination":"nomination",
        "Oath of Office":"other",
        "Omnibus Reserve":"bill",
        "Ordinance":"ordinance",
        "Plaque":"commemoration",
        "Proclamation":"proclamation",
        "Professional Service Agreement":"contract",
        "Public Hearing":"other",
        "Report":"other",
        "Request for Proposals":"other",
        "Request for Qualifications":"other",
        "Request to Advertise":"other",
        "Resolution":"resolution",
        "Resolution of Sympathy":"resolution",
        "Service Awards":"commemoration",
        "Special Item":"other",
        "Special Presentation":"other",
        "Supplement":"other",
        "Swearing-In":"other",
        "Time Sensitive Items":"other",
        "Withdrawals":"other",
        "Workshop Item":"other",
        "Zoning":"other",
        "Zoning Resolution":"resolution"
        }
        matter_doc = self.lxmlize(matter_link)
        info_dict = self.matter_table_to_dict(matter_doc)
        print(info_dict)
        #we're going to use the year of the intro date as the session
        #until/unless we come up with something better
        intro_date = datetime.strptime(info_dict["Introduced"],"%m/%d/%Y")
        session = str(intro_date.year)
        category = matter_types[info_dict["File Type"]]
        if category == 'other':
            bill = Bill(identifier=info_dict["File Number"],
                legislative_session=session,
                title=info_dict["File Name"]
                )
        else:
            bill = Bill(identifier=info_dict["File Number"],
                legislative_session=session,
                title=info_dict["File Name"],
                classification=category
                )
        for spons in info_dict["Sponsors"]:
            if spons == "NONE":
                continue
            try:
                name,spons_type = spons.rsplit(",",1)
            except ValueError:
                name = spons
                spons_type = "Sponsor"
            primary = True if "Prime Sponsor" in spons_type else False
            entity = "person"
            if "committee" in name:
                entity = committee
            bill.add_sponsorship(name,spons_type,entity,primary)
        if "Indexes" in info_dict:
            for subj in info_dict["Indexes"]:
                if subj.strip() and subj.strip() != "NONE":
                    bill.add_subject(subj.strip())
        if "Title" in info_dict and info_dict["Title"].strip():
            note = "bill's long title'"
            if ("Note" in info_dict and info_dict["Note"].strip()):
                note = info_dict["Note"]
            bill.add_abstract(abstract=info_dict["Title"],note=note)
        self.process_action_table(matter_doc,bill)
        bill.add_source(matter_link)

        yield bill