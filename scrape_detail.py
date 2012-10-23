import sqlite3
from chi_leg_scraper import ChicagoLegistar
import time

uri = 'http://chicago.legistar.com/Legislation.aspx'
scraper = ChicagoLegistar(uri)

conn = sqlite3.connect("~/legistar-scrape/chicago_legislation.db")
c1 = conn.cursor()
c2=conn.cursor()

c1.execute('SELECT id, url FROM legislation '
           'WHERE id '
           'NOT IN (SELECT id FROM legislation_history) '
           'OR status NOT IN ("Passed", "Withdrawn")')



for zoning_request in  c1.fetchall() :
  id, detail_url = zoning_request
  print detail_url

  details, history = scraper.parseLegislationDetail('http://chicago.legistar.com/' + detail_url)


  c2.execute('UPDATE legislation SET '
             'status = ?, main_sponsor = ?, title = ?, '
             'attachment = ?, current_controller= ?, topic=?, '
             'related_files = ? '
             'WHERE id = ?',
              (details['Status:'],
               details['Sponsors:'],
               details['Title:'],
               details['Attachments:'],
               details['Current Controlling Legislative Body:'],
               details['Topic:'],
               details['Related files:'],
               id)
               )

  for action in history:
    
    c2.execute('INSERT OR IGNORE INTO legislation_history '
               '(id, status, votes, meeting_details, action_by, '
               ' date, results, journal_page) '
               'VALUES '
               '(?, ?, ?, ?, ?, ?, ?, ?)',
               (id,
                action['status'],
                action['votes'],
                action['meeting_details'],
                action['action_by'],
                action['date'],
                action['results'],
                action['journal_page']))
             



  time.sleep(5)

  
  
  conn.commit()


conn.close()
