
**Sieve** collects data from various sources for training algorithims.  Currently it pulls data from [sense.tw](https://sense.tw).

## Configuration

1. Copy `sieve.conf.template` to `sieve.conf` and edit it.

## Installation

```
$ make all
# Create a Google Sheets credential `client_secret.json` by following <https://pygsheets.readthedocs.io/en/latest/authorizing.html>
$ pipenv run ./annotation_to_gsheets.py
# First time startup will create a credential `sheets.googleapis.com-python.json` with non-local OAuth authentication.
```

## Usage

```
$ pipenv run ./annotation_to_gsheets.py
```

The resulting data are collected in <https://drive.google.com/drive/folders/1lFemgEeleSVN7BwU7_2LzkjBLAgoFg-n?usp=sharing>.

## Google Drive

* An index of all tabular data sheets is saved in "Sense.tw Tabular Index" with columns: id, title, uri, last_updated.
* Each annotated link is saved to a sheet with title as the linked page title with columns: id, target, tags.
