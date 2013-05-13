import re
import itertools
import collections
from datetime import datetime
from functools import partial

import lxml.html
import lxml.etree


class Cached(object):
    '''Computes attribute value and caches it in instance.

    Example:
        class MyClass(object):
            def myMethod(self):
                # ...
            myMethod = Cached(myMethod)
    Use "del inst.myMethod" to clear cache.
    http://code.activestate.com/recipes/276643/
    '''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


class UrlData(object):
    '''Given a url, its nickname, and a scraper instance,
    provide the parsed lxml doc, the raw html, and the url
    '''
    def __init__(self, name, url, scraper, urls_object):
        '''urls_object is a reference back to the Urls container.
        '''
        self.url = url
        self.name = name
        self.scraper = scraper
        self.urls_object = urls_object

    def __repr__(self):
        return 'UrlData(url=%r)' % self.url

    @Cached
    def text(self):
        text = self.scraper.urlopen(self.url)
        self.urls_object.validate(self.name, self.url, text)
        return text

    @Cached
    def resp(self):
        '''Return the decoded html or xml or whatever. sometimes
        necessary for a quick "if 'page not found' in html:..."
        '''
        return self.text.response

    @Cached
    def doc(self):
        '''Return the page's lxml doc.
        '''
        doc = lxml.html.fromstring(self.text)
        doc.make_links_absolute(self.url)
        return doc

    @Cached
    def xpath(self):
        return self.doc.xpath

    @Cached
    def etree(self):
        '''Return the documents element tree.
        '''
        return lxml.etree.fromstring(self.text)


class UrlsMeta(type):
    '''This metaclass aggregates the validator functions marked
    using the Urls.validate decorator.
    '''
    def __new__(meta, name, bases, attrs):
        '''Just aggregates the validator methods into a defaultdict
        and stores them on cls._validators.
        '''
        validators = collections.defaultdict(set)
        for attr in attrs.values():
            if hasattr(attr, 'validates'):
                validators[attr.validates].add(attr)
        attrs['_validators'] = validators
        cls = type.__new__(meta, name, bases, attrs)
        return cls


class Urls(metaclass=UrlsMeta):
    '''Contains urls we need to fetch during this scrape.
    '''

    def __init__(self, urls, scraper):
        '''Sets a UrlData object on the instance for each named url given.
        '''
        self.urls = urls
        self.scraper = scraper
        for url_name, url in urls.items():
            url = UrlData(url_name, url, scraper, urls_object=self)
            setattr(self, url_name, url)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.urls)

    def __iter__(self):
        '''A generator of this object's UrlData members.
        '''
        for url_name in self.urls:
            yield getattr(self, url_name)

    def add(self, url_name, url):
        url_data = UrlData(url_name, url, self.scraper, urls_object=self)
        setattr(self, url_name, url_data)

    @staticmethod
    def validates(url_name, retry=False):
        '''A decorator to mark validator functions for use on a particular
        named url. Use like so:

        @Urls.validates('history')
        def must_have_actions(self, url, text):
            'Skip bill that hasn't been introduced yet.'
            if 'no actions yet' in text:
                raise Skip('Bill had no actions yet.')
        '''
        def decorator(method):
            method.validates = url_name
            method.retry = retry
            return method
        return decorator

    def validate(self, url_name, url, text):
        '''Run each validator function for the named url and its text.
        '''
        for validator in self._validators[url_name]:
            try:
                validator(self, url, text)
            except Exception as e:
                if validator.retry:
                    validator(self, url, text)
                else:
                    raise e

class PageContext(object):
    '''A class to maintain the state of a single bill scrape. It has
    references to the scraper, the bill object under construction,
    the session context, shortcuts for accessing urls and their lxml
    docs, etc.
    '''
    urls_dict = None
    urls_class = Urls

    def __init__(self, scraper, urls_dict=None):
        '''
        context: The Term188 TimespanScraper instance defined above.
        '''
        self.urls_dict = urls_dict or self.urls_dict or {}

        # More aliases for convience later:
        self.scraper = scraper

    @Cached
    def urls(self):
        return self.urls_class(self.urls_dict, scraper=self.scraper)

