class Config (dict):
  def defaults(self, defs):
    """
    Update from the keys in defs where this dictionary has no corresponding
    key.
    """
    for key in defs:
      if key not in self:
        self[key] = defs[key]
    return self


DEFAULT_CONFIG = Config(
  date_format='%m/%d/%Y',
  fulltext=True,
  sponsor_links=True,
)
