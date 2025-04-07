from urllib.parse import quote

def update_qs(url, params):
    """A not-very-intelligent function to glom parameters onto a query string."""
    joined_qs = '&'.join('='.join((str(k), quote(str(v).encode('utf8'))))
                        for k, v in params.items())
    separator = '&' if '?' in url else '?'
    return url + separator + joined_qs
