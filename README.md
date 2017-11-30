municipal-scrapers
==================

[![Build Status](https://travis-ci.org/datamade/scrapers-us-municipal.svg?branch=v0.0.32)](https://travis-ci.org/datamade/scrapers-us-municipal)

DataMade's source for municipal scrapers.

To find out more about the ins-and-outs of these scrapers, as well as how to create your own, head on over to [docs.opencivicdata.org's scraping page](http://docs.opencivicdata.org/en/latest/scrape/index.html).

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
```

Initializing the database may take some time - but if it above goes as expected, then you should see something like this:

```bash
Operations to perform:
  Apply all migrations: contenttypes, core, legislative, pupa
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying core.0001_initial... OK
  Applying legislative.0001_initial... OK
  Applying legislative.0002_more_extras... OK
  Applying legislative.0003_time_changes... OK
  Applying pupa.0001_initial... OK
  Applying pupa.0002_auto_20150906_1458... OK
  Applying pupa.0003_auto_20151118_0408... OK
  Applying pupa.0004_identifier... OK
  Applying pupa.0005_auto_20170522_1935... OK
  Applying pupa.0006_identifier_jurisdiction... OK
193484 divisions found in the CSV, and 0 already in the DB
```

Finally, initialize your new scraper (if you so desire):

```bash
pupa init YOUR_CITY_SCRAPER
```

## Troubleshooting

Your database expects the postgis extension. Do you have this? If not, running `pupa dbinit us` may throw an error: 

```bash
django.db.utils.ProgrammingError: permission denied to create extension "postgis"
HINT:  Must be superuser to create this extension.
```

Create this extension:

```bash
psql -d opencivicdata
CREATE EXTENSION postgis
```

At times, the release of ocd-django on PyPI differs from that of Github. This may cause problems if you need to create and run migrations. Specifically, you might encounter an `ImproperlyConfigured` error that instructs you to do the following:

```bash
You must either define the environment variable DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
```

Fix the problem by running:

```bash
export DJANGO_SETTINGS_MODULE=pupa.settings
```

Then, you should be able to successfully run:

```bash
django-admin makemigrations
django-admin migrate
```

### Testing
Before submitting a PR, please run `pupa update YOUR_CITY_SCRAPER`

```bash
export DATABASE_URL=postgresql:///opencivicdata
pupa update YOUR_CITY_SCRAPER
```

### Making changes to this fork

We want changes in this repo to all be rebased off `opencivicdata/scrapers-us-municipal`.

To achieve this, first pull from origin of the fork.

```bash
git pull origin master
```

Then, make your changes and commit them locally. Next, rebase your changes onto
upstream master.


```bash
git pull --rebase upstream master
```

Finally, force push your changes to the fork on Github.


```bash
git push -f origin master
```