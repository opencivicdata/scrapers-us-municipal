scrapers-us-municipal
=====================

Source for municipal scrapers

To find out more about the ins and outs of these scrapers, as well as how to create your own, head on over to [docs.opencivicdata.org's scraping page](http://docs.opencivicdata.org/en/latest/scrape/index.html).

Issues?
-------

Issues with the data coming from these scrapers should be filed [in this repository](https://github.com/opencivicdata/scrapers-us-municipal/issues).

## Development

### With Docker

Requires Docker and Docker Compose

#### Initialization

```bash
docker-compose run --rm scrapers pupa init YOUR_CITY_SCRAPER
```

### Without Docker

Requires Python 3, PostGIS

#### Initialization
Assuming that you want to have your database be called `opencivicdata` on your local machine

```bash
pip install -r requirements.txt
createdb opencivicdata
export DATABASE_URL=postgresql:///opencivicdata
pupa dbinit us
pupa init YOUR_CITY_SCRAPER
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

## Testing

Before submitting a PR, please run your scraper.

### With Docker

```bash
docker-compose run --rm scrapers pupa update YOUR_CITY_SCRAPER
```

### Without Docker

```bash
export DATABASE_URL=postgresql:///opencivicdata
pupa update YOUR_CITY_SCRAPER
```
