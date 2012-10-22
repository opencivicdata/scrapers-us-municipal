import sqlite3
conn = sqlite3.connect("chicago_legislation.db")
c = conn.cursor()


c.execute("DROP TABLE IF EXISTS legislation")
c.execute("DROP TABLE IF EXISTS sponsors")
c.execute("DROP TABLE IF EXISTS legislation_history")

c.execute("CREATE TABLE sponsors "
          "(id TEXT, sponsor TEXT, "
          "PRIMARY KEY (id, sponsor))")

c.execute("CREATE TABLE legislation "
          "(id TEXT, type TEXT, status TEXT, intro_date DATE, "
          " main_sponsor TEXT, title TEXT, url TEXT, topic TEXT, "
          " attachment TEXT, related_files TEXT, current_controller TEXT, "
          " PRIMARY KEY (id))")

c.execute("CREATE TABLE legislation_history "
          "(id TEXT, status TEXT, "
          " votes TEXT, meeting_details TEXT, action_by TEXT, "
          " date TEXT, results TEXT, journal_page INT), "
          " UNIQUE(id, status, votes, meeting_details, action_by, "
          "        date, results, journal_page)")

conn.commit()
c.close()
          
          
