import sqlite3
from chi_leg_scraper import ChicagoLegistar

uri = 'http://chicago.legistar.com/Legislation.aspx'
scraper = ChicagoLegistar(uri)
legislation = scraper.searchLegislation('zoning')

[legs.pop(4) for legs in legislation]

conn = sqlite3.connect("chicago_legislation.db")
c = conn.cursor()

c.executemany('INSERT OR IGNORE INTO legislation '
              '(id, type, status, intro_date, main_sponsor, title, url) '
              'VALUES '
              '(?, ?, ?, ?, ?, ?, ?)',
              legislation)

conn.commit()
