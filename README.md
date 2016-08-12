municipal-scrapers
==================

source for municipal scrapers

To find out more about the ins and outs of these scrapers, as well as how to create your own, head on over to [docs.opencivicdata.org's scraping page](http://docs.opencivicdata.org/en/latest/scrape/index.html).

Issues?
-------

Issues with the data coming from these scrapers should be filed at the [OCD Data issue tracker](https://sunlight.atlassian.net/browse/DATA/)

All Open Civic Data issues can be browsed and filed at [the Open Civic Data JIRA instance](https://sunlight.atlassian.net/browse/OCD/).

## Development
Requires python3, postgresql

### Initialization
Assuming that you want to have your database be called `opencivicdata` on your local machine

```bash
pip install -r requirements.txt
createdb opencivicdata
export DATABASE_URL=postgresql:///opencivicdata
pupa dbinit us
pupa init YOUR_CITY_SCRAPER
```

### Testing
Before submitting a PR, please run `pupa update YOUR_CITY_SCRAPER`

```bash
export DATABASE_URL=postgresql:///opencivicdata
pupa update YOUR_CITY_SCRAPER
```
