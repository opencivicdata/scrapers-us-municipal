import datetime
import re

import lxml, lxml.html

from pupa.scrape import Scraper
from pupa.models import Event

class EventScraper(Scraper):
    ARLINGTON_MEETING_PAGE = 'http://arlington.granicus.com/ViewPublisher.php?view_id=2'

    def _organize_cells(self, table_type, cells):
        if table_type=='upcoming':
            return {
                'title': cells[0],
                'date': cells[1],
                'agenda': cells[2]
            }
        elif table_type=='archive':
            return {
                'title': cells[0],
                'date': cells[1],
                'duration': cells[2],
                'agenda': cells[3],
                'minutes': cells[4],
                'video': cells[5],
                'audio': cells[6]
            }

    def scrape(self):
        meetings_html = self.urlopen(self.ARLINGTON_MEETING_PAGE)
        meetings_lxml = lxml.html.fromstring(meetings_html)
        
        for meeting_type in ('archive', 'upcoming'):
            for meeting in meetings_lxml.cssselect('#%s tbody tr' % meeting_type):
                
                # attempt to map the cells across table types. 
                # if the sizes mismatch, ignore this one (it's an "empty" message)
                try:
                    cell_mapping = self._organize_cells(meeting_type, meeting.cssselect('td'))
                except:
                    continue

                meeting_title = cell_mapping['title'].text
                meeting_date = datetime.datetime.fromtimestamp(int(cell_mapping['date'].cssselect('span')[0].text))

                e = Event(name=meeting_title, when=meeting_date, location='unknown')
                e.add_source(self.ARLINGTON_MEETING_PAGE)                

                # detect agenda url, if present
                meeting_agenda_url = None
                if len(cell_mapping['agenda'].cssselect('a'))>0:
                    meeting_agenda_url = cell_mapping['agenda'].cssselect('a')[0].attrib.get('href')

                # follow the agenda URL and attempt to extract associated documents
                if meeting_agenda_url is not None:
                    e.add_link(meeting_agenda_url)
                    e.add_document(name='Agenda', url=meeting_agenda_url, mimetype='text/html')                    

                    meeting_agenda_html = self.urlopen(meeting_agenda_url)
                    meeting_agenda_lxml = lxml.html.fromstring(meeting_agenda_html)
                    for link in meeting_agenda_lxml.cssselect('a'):
                        link_url = link.attrib.get('href','')
                        if not len(link_url):
                            continue
                        if 'metaviewer.php' in link_url.lower():
                            # NOTE: application/pdf is a guess, may not always be correct
                            if link.text is not None:
                                e.add_document(name=link.text, url=link_url, mimetype='application/pdf') 

                # skip everything below here for the 'upcoming' table
                if meeting_type=='upcoming':
                    continue

                # detect video
                # TODO: extract actual mp4 files
                video_cell = cell_mapping['video'].cssselect('a')
                if len(video_cell)>0:
                    video_url_match = re.search(r"http://(.*?)'", video_cell[0].attrib.get('onclick',''))
                    if video_url_match is not None:
                        e.add_media_link(name="Video", url=video_url_match.group(0), mimetype='text/html')

                # detect audio
                audio_cell = cell_mapping['audio'].cssselect('a')
                if len(audio_cell)>0:
                    e.add_media_link(name="Audio", url=audio_cell[0].attrib.get('href', ''), mimetype='audio/mpeg')

                # detect minutes
                minutes_cell = cell_mapping['minutes'].cssselect('a')
                if len(minutes_cell)>0:
                    e.add_media_link(name="Minutes", url=minutes_cell[0].attrib.get('href', ''), mimetype='text/html')

                yield e
