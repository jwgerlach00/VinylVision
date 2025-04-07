import json
import requests
import discogs.model as models
from discogs.utils import update_qs


class RequestsFetcher:
    """Fetches via HTTP from the Discogs API."""
    def fetch(self, client, method, url, data=None, headers=None, json=True):
        resp = requests.request(method, url, data=data, headers=headers)
        return resp.content, resp.status_code


class Client:
    BASE_URL = "https://api.discogs.com"
    _base_url = 'https://api.discogs.com'
    _fetcher = RequestsFetcher()

    def __init__(self, token: str, user_agent: str = "VinylVision/1.0"):
        self.headers = {
            "Authorization": f"Discogs token={token}",
            "User-Agent": user_agent
        }

    def _get(self, url):
        return self._request('GET', url)
    
    def _request(self, method, url, data=None):
        content, status_code = self._fetcher.fetch(self, method, url, data=data, headers=self.headers)

        if status_code == 204:
            return None

        body = json.loads(content.decode('utf8'))

        if 200 <= status_code < 300:
            return body
        else:
            raise RuntimeError(body['message'], status_code)

    def search(self, *query, **fields):
        """
        Search the Discogs database. Returns a paginated list of objects
        (Artists, Releases, Masters, and Labels). The keyword arguments to this
        function are serialized into the request's query string.
        """
        if query:
            unicode_query = []
            for q in query:
                try:
                    unicode_q = q.decode('utf8')
                except (UnicodeDecodeError, UnicodeEncodeError, AttributeError):
                    unicode_q = q
                unicode_query.append(unicode_q)
            fields['q'] = ' '.join(unicode_query)
        return models.MixedPaginatedList(
            self,
            update_qs(self.BASE_URL + '/database/search', fields),
            'results'
        )
