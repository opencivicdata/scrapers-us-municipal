from legistar.scraper import LegistarScraper
from legistar.config import Config, DEFAULT_CONFIG


config = Config(
  hostname = 'chicago.legistar.com'
  )
scraper = LegistarScraper(config)


zoning_legislation = scraper.searchLegislation('zoning')

print scraper.expandLegislationSummary(zoning_legislation.next())
