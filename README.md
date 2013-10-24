# Pupa Legistar

Pupa compliant python library for scraping [Legistar sites](http://www.granicus.com/Legistar/Product-Overview.aspx) 
-- legislation management sites hosted by by [Granicus](http://www.granicus.com/Streaming-Media-Government.aspx).

Legistar sites include 
- [Chicago](http://chicago.legistar.com)
- [Philadelphia](http://phila.legistar.com)
- [Oakland](http://oakland.legistar.com/legislation.aspx)
- and many other cities

Pupa framework for managing municipal data
- [standard](https://github.com/opencivicdata/pupa)
- [docs](http://opencivicdata.readthedocs.org/en/latest/)

# Requirements

* python 2.7
* mongo

# Installation

```console
> pip install -r requirements.txt
> python setup.py install 
```

# Setup

Everything should be set up to run already with this repository, but if you want to change your mongo settings, edit `pupa_settings.py`

# Usage

Make sure you have mongo installed and running.

Init the mongo collection. Default database is `pupa`
```console
pupa init chicago 
```

Run the scraper. This will generate a bunch of static json files in `scraped_data` and stuff them in to the `pupa` database.
```console
pupa update chicago
```