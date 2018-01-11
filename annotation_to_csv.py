#!/usr/bin/env python

import logging, os, configparser
import csv
from hypothesis import extract_data, annotations

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
