import sqlite3
conn = sqlite3.connect("chicago_legislation.db")
c = conn.cursor()


c.execute("DROP TABLE IF EXISTS legislation")
c.execute("DROP TABLE IF EXISTS sponsors")

c.execute("CREATE TABLE sponsors "
          "(id TEXT, sponsor TEXT, "
          "PRIMARY KEY (id, sponsor))")

c.execute("CREATE TABLE legislation "
          "(id TEXT, type TEXT, status TEXT, intro_date DATE, "
          "main_sponsor TEXT, title TEXT, url TEXT, topic TEXT, "
          "attachment TEXT, PRIMARY KEY (id))")




conn.commit()
c.close()
          
          
