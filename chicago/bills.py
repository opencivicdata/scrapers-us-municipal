from legistar.bills import LegistarBillScraper
from pupa.scrape import Bill, VoteEvent
from pupa.utils import _make_pseudo_id
import datetime
import pytz



class ChicagoBillScraper(LegistarBillScraper):
    BASE_URL = 'https://chicago.legistar.com/'
    LEGISLATION_URL = 'https://chicago.legistar.com/Legislation.aspx'
    TIMEZONE = "US/Central"

    VOTE_OPTIONS = {'yea' : 'yes',
                    'rising vote' : 'yes',
                    'nay' : 'no',
                    'recused' : 'excused'}

    def session(self, action_date) :
        if action_date < datetime.datetime(2011, 5, 18, 
                                           tzinfo=pytz.timezone(self.TIMEZONE)) :
            return "2007"
        elif action_date < datetime.datetime(2015, 5, 18,
                                             tzinfo=pytz.timezone(self.TIMEZONE)) :
            return "2011"
        else :
            return "2015"

    def scrape(self):
        unreachable_urls = []

        for leg_summary in self.legislation(created_after=datetime.datetime(2015, 5, 17)) :
            title = leg_summary['Title'].strip()

            if not title or not leg_summary['Intro\xa0Date'] :
                continue
                # https://chicago.legistar.com/LegislationDetail.aspx?ID=1800754&GUID=29575A7A-5489-4D8B-8347-4FC91808B201&Options=Advanced&Search=
                # doesn't have an intro date

            bill_type = BILL_TYPES[leg_summary['Type']]

            bill_session = self.session(self.toTime(leg_summary['Intro\xa0Date']))
            bill = Bill(identifier=leg_summary['Record #'],
                        legislative_session=bill_session,
                        title=title,
                        classification=bill_type,
                        from_organization={"name":"Chicago City Council"})

            bill.add_source(leg_summary['url'])

            try :
                leg_details = self.legDetails(leg_summary['url'])
            except IndexError :
                unreachable_urls.append(leg_summary['url'])
                yield bill
                continue

            for related_bill in leg_details.get('Related files', []) :
                lower_title = title.lower()
                if "sundry" in title or "miscellaneous" in title: #these are ominbus
                    bill.add_related_bill(identifier = related_bill['label'],
                                          legislative_session = bill.legislative_session,
                                          relation_type='replaces')
                #for now we're skipping related bills if they
                #don't contain words that make us think they're
                #in a ominbus relationship with each other
                
            for i, sponsor in enumerate(leg_details.get('Sponsors', [])) :
                if i == 0 :
                    primary = True
                    sponsorship_type = "Primary"
                else :
                    primary = False
                    sponsorship_type = "Regular"

                sponsor_name = sponsor['label']

                # Does the Mayor/Clerk introduce legisislation as
                # individuals role holders or as the OFfice of City
                # Clerk and the Office of the Mayor?
                entity_type = 'person'
                if sponsor_name.startswith(('City Clerk', 
                                            'Mendoza, Susana')) :
                    sponsor_name = 'Office of the City Clerk'
                    entity_type = 'organization'
                elif sponsor_name.startswith(('Emanuel, Rahm',)) :
                    sponsor_name = 'Office of the Mayor'
                    entity_type = 'organization'
                if not sponsor_name.startswith(('Misc. Transmittal',
                                                'No Sponsor',
                                                'Dept./Agency')) :
                    bill.add_sponsorship(sponsor_name, 
                                         sponsorship_type,
                                         entity_type,
                                         primary,
                                         entity_id = _make_pseudo_id(name=sponsor_name))

            if 'Topic' in leg_details :
                for subject in leg_details[u'Topic'].split(',') :
                    bill.add_subject(subject)

            for attachment in leg_details.get('Attachments', []) :
                if attachment['label'] :
                    bill.add_version_link(attachment['label'],
                                          attachment['url'],
                                          media_type="application/pdf")

            for action in self.history(leg_summary['url']) :
                action_description = action['Action']
                try :
                    action_date =  self.toTime(action['Date']).date().isoformat()
                except AttributeError : # https://chicago.legistar.com/LegislationDetail.aspx?ID=1424866&GUID=CEC53337-B991-4268-AE8A-D4D174F8D492
                    continue

                if action_description :
                    try :
                        responsible_org = action['Action\xa0By']['label']
                    except TypeError  :
                        responsible_org = action['Action\xa0By']
                    if responsible_org == 'City Council' :
                        responsible_org = 'Chicago City Council'

                    act = bill.add_action(action_description,
                                          action_date,
                                          organization={'name': responsible_org},
                                          classification=ACTION_CLASSIFICATION[action_description])

                    if action_description == 'Referred' :
                        try :
                            leg_details['Current Controlling Legislative Body']['label']
                            controlling_bodies = [leg_details['Current Controlling Legislative Body']]
                        except TypeError :
                            controlling_bodies = leg_details['Current Controlling Legislative Body']
                        if controlling_bodies :
                            for controlling_body in controlling_bodies :
                                body_name = controlling_body['label']
                                if body_name.startswith("Joint Committee") :
                                    act.add_related_entity(body_name,
                                                           'organization')
                                else :
                                    act.add_related_entity(body_name,
                                                           'organization',
                                                           entity_id = _make_pseudo_id(name=body_name))


                    if 'url' in action['Action\xa0Details'] :
                        action_detail_url = action['Action\xa0Details']['url']
                        result, votes = self.extractVotes(action_detail_url)

                        if votes and result : # see https://github.com/datamade/municipal-scrapers-us/issues/15
                            action_vote = VoteEvent(legislative_session=bill.legislative_session, 
                                               motion_text=action_description,
                                               organization={'name': responsible_org},
                                               classification=None,
                                               start_date=action_date,
                                               result=result,
                                               bill=bill)
                            action_vote.add_source(action_detail_url)

                            for option, voter in votes :
                                action_vote.vote(option, voter)

                            yield action_vote
                            
            yield bill
        print(unreachable_urls)

ACTION_CLASSIFICATION = {'Referred' : 'committee-referral',
                         'Re-Referred' : 'committee-referral',
                         'Recommended to Pass' : 'committee-passage-favorable',
                         'Passed as Substitute' : 'passage',
                         'Adopted' : 'passage',
                         'Approved' : 'passage',
                         'Passed'  : 'passage',
                         'Substituted in Committee' : 'substitution',
                         'Failed to Pass' : 'failure',
                         'Recommended Do Not Pass' : 'committee-passage-unfavorable',
                         'Amended in Committee' : 'amendment-passage',
                         'Placed on File' : 'filing',
                         'Withdrawn' : 'withdrawal',
                         'Signed by Mayor' : 'executive-signature',
                         'Appointment' : 'appointment',
                         'Introduced (Agreed Calendar)' : 'introduction',
                         'Direct Introduction' : 'introduction',
                         'Remove Co-Sponsor(s)' : None,
                         'Add Co-Sponsor(s)' : None,
                         'Tabled' : 'deferred',
                         'Rules Suspended - Immediate Consideration' : None,
                         'Committee Discharged' : None,
                         'Held in Committee' : 'committee-failure',
                         'Recommended for Re-Referral' : None,
                         'Published in Special Pamphlet' : None,
                         'Adopted as Substitute' : None,
                         'Deferred and Published' : None,
                         'Approved as Amended' : 'passage',
}


BILL_TYPES = {'Ordinance' : 'ordinance',
              'Resolution' : 'resolution',
              'Order' : 'order',
              'Claim' : 'claim',
              'Oath of Office' : None,
              'Communication' : None,
              'Appointment' : 'appointment',
              'Report' : None}

BLACKLIST_URLS = {'https://chicago.legistar.com/LegislationDetail.aspx?ID=2394619&GUID=89741E39-7BB0-4E17-B6C4-04E66B5B7AD2', 
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2394571&GUID=516813F1-8918-4B61-971A-C7603FC14379',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2394526&GUID=E74CD6FE-507F-4C5F-9BA3-EC21E25E44E6',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2393890&GUID=B9CFF38C-DC72-4A0D-ABFF-378E127D90A9',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2393817&GUID=BC05E7BF-AE68-4DB5-84CB-7DC0665FEDEE',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2393796&GUID=735995CC-72A8-4D33-AFC2-FCF6A80F41C4',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2393453&GUID=FF80CF81-6D37-4661-B2C6-C56D761EA922',
                  'https://chicago.legistar.com/LegislationDetail.aspx?ID=2369521&GUID=5E1B3403-1665-4BF7-A89A-34C2FAC38E76'}

