Legistar Scraper is a python library for scraping [Legistar sites](http://www.granicus.com/Legistar/Product-Overview.aspx) 
-- legislation management sites hosted by by [Granicus](http://www.granicus.com/Streaming-Media-Government.aspx).

Legistar sites include 
- [Chicago](http://chicago.legistar.com)
- [Philadelphia](http://phila.legistar.com)
- and many other cities

This software is under active development. It is currently known to work for Chicago and Philadelphia.

[![Build Status](https://travis-ci.org/fgregg/legistar-scrape.png?branch=master)](https://travis-ci.org/fgregg/legistar-scrape)
# Installation

```console
> pip install -r requirements.txt
> python setup.py install 
```

Note: The current stable branch of mechanize [has a bug in it](https://github.com/jjlee/mechanize/pull/58). If
you are installing the dependencies by hand, use https://github.com/abielr/mechanize.

# Example usage

```python
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
```
