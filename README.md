Scraping [Chicago Legistation](http://chicago.legistar.com)
-

The url for an piece of legislation is identified with and ID and a GUID. The ID is an integer N that seems to indicate 
that this legislation is the Nth item that has been introduced into the Chicago Legistar site. The GUID or
Globally unique identifier is a 32 hexadecimal digits with 4 embedded hyphens, as in 
"be21918b-28e2-4850-9cb2-09dd3a12aa4f."[1] 

Unfortunately, we cannot step through the legislative IDs, because we cannot guess the GUID.[2] So, we will have to
interact with the sites's forms, [as described in this stack overflow question](http://stackoverflow.com/questions/1480356/how-to-submit-query-to-aspx-page-in-python).

> python chi_leg_scraper.py

[1]: http://www.granicus.com/Files/API/Granicus-Training-Management-Suite-API-v5.pdf
[2]: This also means that we can't use Mjumbe Poe's [Legistar Scraper](https://scraperwiki.com/scrapers/philadelphia_legislative_files/)

# Nonstandard mechanize dependency
The current stable branch of mechanize [has a bug in it](https://github.com/jjlee/mechanize/pull/58), use https://github.com/abielr/mechanize
