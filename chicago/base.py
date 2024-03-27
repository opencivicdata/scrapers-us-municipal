import urllib.parse


class ElmsAPI:
    BASE_URL = "https://api.chicityclerkelms.chicago.gov"

    def _endpoint(self, path):
        return urllib.parse.urljoin(self.BASE_URL, path)

    def _paginate(self, url, params=None):

        max_skip = 100000
        if "sort" in params:
            sorting_feature = params["sort"].split()[0]
        else:
            sorting_feature = None

        original_filter = params["filter"]

        if params is None:
            params = {}

        params["skip"] = 0
        response = self.get(url, params=params)

        data = response.json()
        total = data["meta"]["count"]
        yield from data["data"]

        while total > max_skip:

            for offset in range(100, max_skip, 100):
                params["skip"] = offset
                response = self.get(url, params=params)
                data = response.json()
                yield from data["data"]

            if sorting_feature:
                sort_constraint = min(
                    matter[sorting_feature] for matter in data["data"]
                )
                params["filter"] = (
                    f"({original_filter}) and "
                    f"({sorting_feature} gt {sort_constraint} or "
                    f" {sorting_feature} eq {sort_constraint})"
                )
                params["skip"] = 0
                response = self.get(url, params=params)

                data = response.json()
                total = data["meta"]["count"]
                yield from data["data"]

            else:
                raise ValueError(
                    f"We don't know how to skip more than {max_skip}. Please provide a sort param."
                )

        for offset in range(100, total, 100):
            params["skip"] = offset
            response = self.get(url, params=params)
            data = response.json()
            yield from data["data"]
