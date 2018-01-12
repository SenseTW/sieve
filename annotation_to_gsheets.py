#!/usr/bin/env python

import os, configparser, logging, time
import pendulum
from hypothesis import annotations, extract_data
import pygsheets

cred_path = "sheets.googleapis.com-python.json"

index_title = "Sense.tw 目錄"
index_cols = ["id", "title", "uri", "last_updated"]
gsheet_cols = ["id", "target", "text", "tags", "link"]

def get_index_sheet(gc, folder_id):
    try:
        return gc.open(index_title)
    except pygsheets.SpreadsheetNotFound:
        sh = gc.create(index_title, parent_id=folder_id)
        wks = sh.sheet1
        wks.insert_rows(0, number=1, values=index_cols)
        wks.sync()
        return sh

def get_sheets_index(gc, folder_id):
    sh = get_index_sheet(gc, folder_id)
    wks = sh.sheet1
    records = wks.get_all_records()
    return records

def index_lookup(index, uri, field=None):
    for i, entry in enumerate(index):
        if entry["uri"] == uri:
            if field is None:
                return i + 2
            else:
                return entry[field]
    return None

def get_updated_data(index, data):
    def check_updated(last_updated, data_updated):
        if last_updated is None:
            return True
        last = pendulum.parse(last_updated)
        new = pendulum.parse(data_updated)
        return last < new

    return [ d for d in data \
            if check_updated(index_lookup(index, d.uri, field="last_updated"), d.updated) ]

def get_data_by_uri(data_by_uri, data):
    if len(data) == 0:
        return data_by_uri
    head = data[0]
    if head.uri in data_by_uri:
        data_by_uri[head.uri].append(head)
        return get_data_by_uri(data_by_uri, data[1:])
    else:
        data_by_uri[head.uri] = [head]
        return get_data_by_uri(data_by_uri, data[1:])

def save_annotations_to_gsheet(wks, index, data):
    if len(data) == 0:
        return
    d = data[0]
    if d.id in index:
        i = index[d.id]
        wks.update_cell("B{i}".format(i=i), d.target)
        wks.update_cell("C{i}".format(i=i), d.text)
        wks.update_cell("D{i}".format(i=i), ", ".join(d.tags))
        wks.update_cell("E{i}".format(i=i), d.link)
    else:
        wks.append_table(values=[d.id, d.target, d.text, ", ".join(d.tags), d.link])
    time.sleep(2)
    return save_annotations_to_gsheet(wks, index, data[1:])

def save_uri_to_gsheet(gc, folder_id, index, uri, data):
    sheet_id = index_lookup(index, uri, field="id")
    if sheet_id is None:
        sh = gc.create(data[0].title, parent_id=folder_id)
        sh.sheet1.append_table(values=gsheet_cols)
        sh.sheet1.sync()
    else:
        sh = gc.open_by_key(sheet_id)
    wks = sh.sheet1
    annotation_index = dict([ (idx, i + 1) for i, idx in enumerate(wks.get_col(1)) ])
    save_annotations_to_gsheet(wks, annotation_index, data)
    wks.sync()
    return sh.id

def save_data_to_gsheet(updated, gc, folder_id, index, dataitems):
    if len(dataitems) == 0:
        return updated

    def get_last_updated(data):
        last = pendulum.parse(data[0].updated)
        for d in data:
            u = pendulum.parse(d.updated)
            if last < u:
                last = u
        return last

    uri, data = dataitems[0]
    sheet_id = save_uri_to_gsheet(gc, folder_id, index, uri, data)
    updated.append({
        "id": sheet_id,
        "title": data[0].title,
        "uri": uri,
        "last_updated": get_last_updated(data),
    })
    time.sleep(2)
    return save_data_to_gsheet(updated, gc, folder_id, index, dataitems[1:])

def save_index(sh, index, updated):
    if len(updated) == 0:
        return
    wks = sh.sheet1
    entry = updated[0]
    i = index_lookup(wks.get_all_records(), entry["uri"])
    if i is not None:
        wks.update_cell("D{i}".format(i=i), str(entry["last_updated"]))
    else:
        wks.append_table(values=[entry["id"], entry["title"], entry["uri"], str(entry["last_updated"])])
    return save_index(sh, index, updated[1:])

def gsheets_save(folder_id, data):
    if not os.path.exists(cred_path):
        gc = pygsheets.authorize("client_secret.json", outh_nonlocal=True)
    else:
        gc = pygsheets.authorize(cred_path)

    index = get_sheets_index(gc, folder_id)
    data_to_update = get_updated_data(index, data)
    data_by_uri = get_data_by_uri({}, data_to_update)
    updated = save_data_to_gsheet([], gc, folder_id, index, list(data_by_uri.items()))
    index_sheet = get_index_sheet(gc, folder_id)
    save_index(index_sheet, index, updated)
    index_sheet.sheet1.sync()


def main(config, logger):
    server = config["DEFAULT"]["server"]
    api_url = config[server]["url"]

    data = [ extract_data(x) for x in annotations(api_url) ]

    gsheets_save(config["gsheets"]["folder_id"], data)

if __name__ == "__main__":
    config_path = "sieve.conf"
    config = configparser.ConfigParser()
    config.read(config_path)
    logger = logging.getLogger("annotation_to_gsheets")
    logger.setLevel(config["DEFAULT"].get("loglevel") or logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    main(config, logger)
