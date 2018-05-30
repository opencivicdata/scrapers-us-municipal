from os import path
from datetime import datetime
from collections import namedtuple
from pupa.scrape import Bill
from .utils import NashvilleScraper


class NashvilleBillScraper(NashvilleScraper):

    def scrape(self):
        yield from self.get_resolution_by_council_term()

    def get_resolution_by_council_term(self):
        base_url = 'http://www.nashville.gov/Metro-Clerk/Legislative/Resolutions.aspx'
        doc = self.lxmlize(base_url)
        dnn_name = self.get_dnn_name(doc)
        data_id = 'dnn_ctr{}_HtmlModule_lblContent'.format(dnn_name)
        council_term_urls = doc.xpath(
            '//div[@id="{}"]/p/a[contains(@href, ".aspx")]/@href'.format(data_id))
        for term_url in council_term_urls:
            yield from self.get_resolutions(term_url)

    def get_resolutions(self, url):
        doc = self.lxmlize(url)
        self.bill_session = self.get_session_year(url)

        current_year = datetime.now().year
        current_session = int(self.bill_session[0:4]) + 4 >= current_year
        if current_session:
            (dnn_name, ) = doc.xpath(
                '//div[contains(@class, "DnnModule-NV-LVMSLegislation-List")]/a/@name')
            bill_elements = doc.xpath(
                '//div[@id="dnn_ctr{}_LVMSLegislationList_pnlListWrap"]/p'.format(dnn_name))
            yield from self.get_session_bills(bill_elements)
            (second_list, ) = doc.xpath(
                '//div[contains(@class, "DnnModule-{}")]/following-sibling::div[1]'.format(dnn_name))
            yield from self.get_session_bills(second_list)
        else:
            dnn_name = self.get_dnn_name(doc)
            bill_elements = doc.xpath(
                '//div[@id="dnn_ctr{}_HtmlModule_lblContent"]/p'.format(dnn_name))
            yield from self.get_session_bills(bill_elements)

    def get_session_year(self, url):
        filename = path.basename(url)
        return filename.split('.')[0]

    def get_session_bills(self, bill_elements):

        title_p = None
        summary_p = None
        for idx, bill in enumerate(bill_elements):
            if idx % 2:
                # It is odd so lets create a new bill
                try:
                    (administrative_title, ) = title_p.xpath('./a/text()')
                except ValueError:
                    # The first row might be the title and won't contain an anchor tag
                    continue
                (link, ) = title_p.xpath('./a/@href')
                (title, ) = bill.xpath('./text()')
                (*classification, identifier) = administrative_title.split(' ')
                self.current_bill_identifier = identifier

                bill = Bill(identifier=identifier,
                            title=title,
                            classification='resolution',
                            legislative_session=self.bill_session,
                            from_organization={"name": "Nashville Metropolitan Council"})
                bill = self.get_bill_detail(link, bill)
                if(bill):
                    yield bill

            else:
                title_p = bill

    def get_bill_detail(self, url, bill):
        bill_doc = self.lxmlize(url)
        try:
            dnn_name = self.get_dnn_name(bill_doc)
            return self.dot_net_bill_detail(dnn_name, bill_doc, bill)
        except ValueError:
            # TODO: Handle non dot net bill pages
            pass

    def dot_net_bill_detail(self, dnn_name, bill_doc, bill):
        legislative_div_id = 'dnn_ctr{}_LVMSLegislationDetails_pnlLegislationDetails'.format(dnn_name)
        supporting_files = bill_doc.xpath('//div[@id="{}"]/descendant::*/a[contains(@href, "files")]/@href'.format(legislative_div_id))
        bill = self.sort_files(supporting_files, bill)
        try:
            (vote_pdf, ) = bill_doc.xpath('//div[@id="{}"]/descendant::*/a[contains(@href, "roll-call-votes")]/@href'.format(legislative_div_id))
            # TODO: Parse votes
            bill.add_document_link(note='roll-call-vote', url=vote_pdf, media_type="application/pdf")
        except ValueError:
            # Vote PDF is not available
            pass
        return bill
    
    def sort_files(self, supporting_files, bill):
        for support_file in supporting_files:
            filename = path.basename(support_file)
            if filename == self.current_bill_identifier + '.pdf':
                # This is the main bill file
                # TODO: Add sponsors
                bill.add_source(note='detail', url=support_file)
                
            else:
                try:
                    note = filename[:len(filename)-4].split('_')[1].lower()
                    bill.add_document_link(note=note, url=support_file, media_type="application/pdf")
                except:
                    # It is possible that the doc doesn't fit either format so let's add it as detail
                    bill.add_source(note='detail', url=support_file)

        return bill



