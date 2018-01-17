FROM kennethreitz/pipenv

COPY . /app

RUN apt-get update && apt-get install -y cron
RUN make all
RUN cp /app/config/sieve-cron /etc/cron.d/sieve-cron
#RUN crontab /etc/cron.d/sieve-cron
RUN apt-get clean

CMD ["/app/docker-init.sh"]
