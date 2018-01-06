#!/usr/bin/env python

import requests, pickle, time, logging, os, configparser

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
            else queries[1:] + [dict(query, **{ "offset": next_offset })]
    return fetch_rows(api_url, rows + data["rows"], next_queries)

def annotations(api_url,
        uris=None, tags=None, until=None, limit=None):
    """
    XXX `limit` and `until` are unimplemented.
    """
    if uris is None: uris = [ None, ]
    if tags is None: tags = [ None, ]
    # 200 is hypothes.is API limit
    l = 200

    queries = [ query_parameters(u, t, l) for u in uris for t in tags ]
    rows, _ = fetch_rows(api_url, [], queries)

    return rows

class AnnotationData:
    """
    Data object for data extracted from an annotation.
    """
    _fields = ["updated", "tags", "text", "uri", "target"]

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
    data = dict([ (key, row[key]) for key in ["updated", "tags", "text", "uri"] ])

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
    return AnnotationData(**data)

def save(api_url, storage_path, uris=None):
    rows = annotations(api_url, uris=uris)
    data = [ extract_data(row) for row in rows ]
    with open(storage_path, "wb") as fh:
        pickle.dump(data, fh)

def main(config, logger):
    server = config["DEFAULT"]["server"]
    api_url = config[server]["url"]
    save(api_url, "storage/annotations.pkl", uris=[
        "https://udn.com/news/plus/9401/2892368"
        ])

if __name__ == "__main__":
    config_path = "sieve.conf"
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        config["DEFAULT"] = { "server": "sense.tw" }
        config["sense.tw"] = { "url": "https://sense.tw" }
    logger = logging.getLogger("fetch_annotation")
    logger.setLevel(config["DEFAULT"].get("loglevel") or logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    main(config, logger)
