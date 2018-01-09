#!/usr/bin/env python

import requests, time, logging, os, configparser
import csv

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

def annotations(api_url, uris=None, tags=None):
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
    _fields = ["id", "updated", "tags", "text", "uri", "target"]

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
    data = dict([ (key, row[key]) for key in ["id", "updated", "tags", "text", "uri"] ])

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

def read_csv(csv_path):
    if os.path.exists(csv_path):
        with open(csv_path, "r", newline="") as fh:
            return list(csv.DictReader(fh))
    else:
        return []

def save_csv(csv_path, data):
    fieldnames = ["id", "target", "tags", "ORID"]
    rows = read_csv(csv_path)
    index = dict([ (x["id"], i) for i, x in enumerate(rows) ])
    for x in data:
        if x.id in index:
            row = rows[index[x.id]]
            row["target"] = x.target
            row["tags"] = ", ".join(x.tags)
        else:
            rows.append({
                "id": x.id,
                "target": x.target,
                "tags": ", ".join(x.tags),
                "ORID": "",
                })
    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def pull_and_merge(api_url, csv_path, uris=None):
    data = [ extract_data(x) for x in annotations(api_url, uris=uris) ]
    save_csv(csv_path, data)

def main(config, logger, uris=None):
    server = config["DEFAULT"]["server"]
    api_url = config[server]["url"]
    pull_and_merge(api_url, "storage/annotations.csv", uris=uris)

if __name__ == "__main__":
    import sys
    uris = sys.argv[1:] if len(sys.argv) > 1 else [
        "https://udn.com/news/plus/9401/2892368",
        ]

    config_path = "sieve.conf"
    config = configparser.ConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        config["DEFAULT"] = { "server": "sense.tw" }
        config["sense.tw"] = { "url": "https://sense.tw" }
    logger = logging.getLogger("annotation_to_csv")
    logger.setLevel(config["DEFAULT"].get("loglevel") or logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    main(config, logger, uris=uris)
