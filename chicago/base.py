import urllib.parse


class ElmsAPI:
    BASE_URL = "https://api.chicityclerkelms.chicago.gov"

    def _endpoint(self, path):
        return urllib.parse.urljoin(self.BASE_URL, path)

    def _paginate(self, url, params=None):
        """
        To paginate through APIs we will use both an offset strategy
        and a cursor strategy.

        The elms site only allows a max offset of 100,000 records. If
        we want more than that, we can accomplist that by using the
        a sort key as a cursor.

        Basically, we sort the records by some feature in ascending
        order. This feature is our "cursor." We step through the data
        as much as we can using offsets. Once we are at the max
        offset, we find the minimum value of cursor in the last page
        of date, and then add a new filter condition that the cursor
        has to be greater than or equal to that minimum value.

        We reset the offset back to 0 and restart the offset walking.
        """

        max_offset = 100000
        if "sort" in params:
            cursor_feature = params["sort"].split()[0]
        else:
            cursor_feature = None

        original_filter = params["filter"]

        if params is None:
            params = {}

        params["skip"] = 0
        response = self.get(url, params=params)

        data = response.json()
        total = data["meta"]["count"]
        yield from data["data"]

        while total > max_offset:

            for offset in range(100, max_offset, 100):
                params["skip"] = offset
                response = self.get(url, params=params)
                data = response.json()
                yield from data["data"]

            if cursor_feature:
                cursor_location = min(matter[cursor_feature] for matter in data["data"])
                params["filter"] = (
                    f"({original_filter}) and "
                    f"({cursor_feature} gt {cursor_location} or "
                    f" {cursor_feature} eq {cursor_location})"
                )
                params["skip"] = 0
                response = self.get(url, params=params)

                data = response.json()
                total = data["meta"]["count"]
                yield from data["data"]

            else:
                raise ValueError(
                    f"We don't know how to skip more than {max_offset}. Please provide a sort param."
                )

        for offset in range(100, total, 100):
            params["skip"] = offset
            response = self.get(url, params=params)
            data = response.json()
            yield from data["data"]
