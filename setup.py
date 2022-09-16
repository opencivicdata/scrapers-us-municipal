from setuptools import setup, find_packages

setup(
    name='muniscrapers',
    version='1.0.0',
    url='https://github.com/opencivicdata/scrapers-us-municipal',
    packages=find_packages(),    
    install_requires=['pupa', 'scraper-legistar'],
)
