FROM python:3.7
RUN apt-get update && apt-get -y install cron vim
RUN pip install mysql-connector-python
RUN pip install speedtest-cli
WORKDIR /app
COPY crontab /etc/cron.d/crontab
COPY main.py /app/main.py
COPY mysql.cfg /app/mysql.cfg
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

# run crond as main process of container
CMD ["cron", "-f"]