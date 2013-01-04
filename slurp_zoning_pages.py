from legistar.scraper import LegistarScraper
from legistar.config import Config, DEFAULT_CONFIG


config = Config(
  hostname = 'chicago.legistar.com'
  )
scraper = LegistarScraper(config)


zoning_legislation = scraper.searchLegislation('zoning')
zoning_legislation.next()

legislation_attrs, legislation_history = scraper.expandLegislationSummary(zoning_legislation.next())

history_summary = legislation_history[0]

history_detail, votes = scraper.expandHistorySummary(history_summary)
    
print history_detail
print legislation_history

#print zoning_legislation.next()
