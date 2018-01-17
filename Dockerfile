FROM kennethreitz/pipenv

COPY . /app

RUN apt-get update && apt-get install -y cron
RUN make all
COPY config/sieve-cron /etc/cron.d/sieve-cron
RUN crontab /etc/cron.d/sieve-cron

CMD ["cron", "-f"]
