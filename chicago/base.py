import urllib.parse

class ElmsAPI:
    BASE_URL = "https://api.chicityclerkelms.chicago.gov"

    def _endpoint(self, path):
        return urllib.parse.urljoin(self.BASE_URL, path)

    
    def _paginate(self, url, params=None):

        if params is None:
            params = {}

        params['skip'] = 0
        response = self.get(url, params=params)

        data = response.json()
        total = data['meta']['count']

        yield from data['data']

        for offset in range(100, total, 100):
            params['skip'] = offset
            response = self.get(url, params=params)
            data = response.json()
            yield from data['data']
