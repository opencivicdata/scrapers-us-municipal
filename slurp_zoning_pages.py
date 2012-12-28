import sqlite3
from legistar_scraper import LegistarScraper

hostname = 'chicago.legistar.com'
scraper = LegistarScraper(hostname)



conn = sqlite3.connect("/home/ec2-user/legistar-scrape/chicago_legislation.db")
c = conn.cursor()

c.execute('select date(max(intro_date)) from legislation')
last_date = c.fetchone()[0]


legislation = scraper.searchLegislation('', last_date)
# Remove the final date field
[legs.pop(4) for legs in legislation]

c.executemany('INSERT OR IGNORE INTO legislation '
             '(id, type, status, intro_date, main_sponsor, title, url) '
              'VALUES '
              '(?, ?, ?, ?, ?, ?, ?)',
              legislation)

conn.commit()
conn.close()
