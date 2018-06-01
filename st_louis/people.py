from pupa.scrape import Person, Organization
from .utils import Urls, StlScraper, HumanName

class StLouisPersonScraper(StlScraper):

	def scrape(self):
		# FIXME `yield` or `yield from`?
		yield from self.scrape_people()
		yield from self.scrape_committees()

	def scrape_people(self):
		for ward_num in range(1, self.jurisdiction.WARD_COUNT + 1):
			yield self.scrape_alderman(ward_num)

	def scrape_committees(self):
		for comm_num in range(1, self.COMMITTEE_COUNT + 1):
			yield from self.scrape_committee(comm_num)

	def scrape_alderman(self, ward_num):
		ward_url = "{}/ward-{}".format(Urls.ALDERMEN_HOME, ward_num)
		alderman_url = self.alderman_url(ward_url)
		alderman_page = self.lxmlize(alderman_url)

		# person's name is the only <h1> tag on the page
		raw_name = alderman_page.xpath("//h1/text()")[0]
		name = HumanName.name_firstandlast(raw_name)

		# initialize person object with appropriate data so that pupa can 
		# automatically create a membership object linking this person to
		# a post in the jurisdiction's "Board of Aldermen" organization
		district = "Ward {} Alderman".format(ward_num)
		person = Person(name=name, district=district, role="Alderman", 
										primary_org="legislature")

		# set additional fields
		person.image = alderman_page.xpath("//div/img/@src")[0]
		phone_number = alderman_page.xpath("//strong[text()='Phone:']/../text()")[1].strip()
		person.add_contact_detail(type="voice", value=phone_number)

		# add sources
		person.add_source(alderman_url, note="profile")
		person.add_source(ward_url, note="ward")

		return person

	def scrape_committee(self, comm_num):
                url = self.committee_url(comm_num)
                page = self.lxmlize(url)
                # get title
                comm_name = page.xpath("//h1/text()")[0]

                # create object
                comm = Organization(name=comm_name,
                                    classification="committee",
                                    chamber="legislature")
                comm.add_source(url=url)

		# add posts
                comm.add_post(label="chair", role="chair")
		# FIXME do we need a separate post for each member?
		# FIXME is member an appropriate name?
                comm.add_post(label="member", role="member") 

		# helper for finding other nodes
                landmark_node = page.xpath("//h2[text()='Committee Members']")[0]

		# add memberships
                member_names = landmark_node.xpath("following-sibling::div/ul/li/a/text()")
                fl_names = [HumanName.name_firstandlast(name) for name in member_names]
                print("My attempt to scrub people's names:", 
                      list(zip(member_names, fl_names)))
                chair_name, *other_names = fl_names
                if chair_name not in {'Lewis Reed'} :
                        comm.add_member(chair_name, role="chair")
                for name in other_names:
                        if name not in {'Lewis Reed'} :
                                comm.add_member(name, role="member")
		# add description 
                about_node = page.xpath("//h2[text()='About']")[0]
                (description, ) = about_node.xpath("parent::div//div[@class='content-block']/p[2]/text()")
                description = description.strip()
                comm.extras = {"description": description}

                yield comm


	def alderman_url(self, ward_url):
		ward_page = self.lxmlize(ward_url)
		# each ward page contains a link to the current alderman's profile.
		# the text of the link says "Email <Jane Doe>" where Jane Doe is the
		# name of the alderman.
		# find that link by selecting for <a> tags whose text contains 'Email'
		return ward_page.xpath("//a[contains(text(), 'Email')]//@href")[0]

	def committee_url(self, comm_num):
		return Urls.COMMITTEES_HOME + "?committeeDetail=true&comId={}".format(comm_num)

	# TODO move this?
	COMMITTEE_COUNT = 15
