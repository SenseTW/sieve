
**Sieve** collects data from various sources for training algorithims.  Currently it pulls data from [sense.tw](https://sense.tw).

## Configuration

1. Copy `sieve.conf.template` to `sieve.conf` and edit it.

## Usage

```
$ make all
$ pipenv shell
$ python fetch_annotation.py
```

## Google Drive

* An index of all tabular data sheets is saved in "Sense.tw Tabular Index" with columns: id, title, uri, last_updated.
* Each annotated link is saved to a sheet with title as the linked page title with columns: id, target, tags.
