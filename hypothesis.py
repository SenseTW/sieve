
import time, requests

class AnnotationData:
    """
    Data object for data extracted from an annotation.
    """
    _fields = ["id", "updated", "tags", "text", "uri", "link", "target", "title", "user"]

    def __init__(self, **kwargs):
        for key in kwargs.keys():
            if key not in self._fields:
                raise TypeError("'%s' is not a field")
        self.__dict__.update(kwargs)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return repr(self.__dict__)

def extract_data(row):
    data = dict([ (key, row[key]) for key in ["id", "updated", "tags", "text", "uri", "user"] ])

    def extract_target(targets):
        if len(targets) == 0: return None

        def extract_exact(selectors):
            if len(selectors) == 0: return None
            if selectors[0]["type"] == "TextQuoteSelector":
                return selectors[0]["exact"]
            else:
                return extract_exact(selectors[1:])

        if "selector" not in targets[0]:
            return extract_target(targets[1:])
        exact = extract_exact(targets[0]["selector"])
        if exact is not None:
            return exact
        else:
            return extract_target(targets[1:])

    data["target"] = extract_target(row["target"])
    data["title"] = row["document"]["title"][0] if "title" in row["document"] else ""
    data["link"] = row["links"]["html"]
    return AnnotationData(**data)

def annotations(api_url, uris=None, tags=None):
    if uris is None: uris = [ None, ]
    if tags is None: tags = [ None, ]
    # 200 is hypothes.is API limit
    l = 200

    queries = [ query_parameters(u, t, l) for u in uris for t in tags ]
    rows, _ = fetch_rows(api_url, [], queries)

    return rows

def query_parameters(url, tag, limit):
    q = { "limit": limit, "offset": 0 }
    if url is not None:
        q["url"] = url
    if tag is not None:
        q["tag"] = tag
    return q

def fetch_rows(api_url, rows, queries, sleep_sec=1):
    if len(queries) == 0:
        return rows, []
    time.sleep(sleep_sec)
    query = queries[0]
    response = requests.get(api_url + "/search", params=query)
    data = response.json()
    total = data["total"]
    next_offset = query["offset"] + query["limit"]
    next_queries = queries[1:] if next_offset >= total \
            else queries[1:] + [{**query, **{ "offset": next_offset }}]
    return fetch_rows(api_url, rows + data["rows"], next_queries)
