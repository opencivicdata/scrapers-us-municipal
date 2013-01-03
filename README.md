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

# Usage

    from legistar.scraper import LegistarScraper
    from legistar.config import Config, DEFAULT_CONFIG

    #__________________________________________________________________________
    #
    # Configure and create a scraper

    config = Config(
      hostname = 'chicago.legistar.com',
    ).defaults(DEFAULT_CONFIG)
    scraper = LegistarScraper(config)

    #__________________________________________________________________________
    #
    # Get a summary listing of all of the legislation

    all_legislation = scraper.searchLegislation('')

    #__________________________________________________________________________
    #
    # Get more detail for a particular piece of legislation

    for legislation_summary in all_legislation:
      (legislation_attrs, legislation_history) = \
        scraper.expandLegislationSummary(legislation_summary)
      break
    # NOTE: searchLegislation returns an iterator; you may not use subscript
    # indexing (e.g., all_legislation[0]). You may, however, achieve the same
    # thing with all_legislation.next()

    #__________________________________________________________________________
    #
    # Get details about legislation history, such as voting results

    for history_summary in legislation_history:
      (history_detail, votes) = scraper.expandHistorySummary(history_summary)


# Nonstandard mechanize dependency
The current stable branch of mechanize [has a bug in it](https://github.com/jjlee/mechanize/pull/58), use https://github.com/abielr/mechanize
