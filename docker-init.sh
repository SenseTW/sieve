#!/bin/bash
cp /config/sheets.googleapis.com-python.json /app/sheets.googleapis.com-python.json
cp /config/sieve.conf /app/sieve.conf
env >> /etc/environment
crontab /etc/cron.d/sieve-cron
cron -f
