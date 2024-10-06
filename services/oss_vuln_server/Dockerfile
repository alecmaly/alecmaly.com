FROM python:latest

# Install cron
RUN apt-get update && apt-get install -y cron sudo

WORKDIR /opt/app


COPY requirements.txt .
COPY run_server.py .
COPY styles.css .
COPY purecss.min.css .
COPY main.js .
COPY mark.min.js .
COPY download_osv_data.py .
# old version of report before being updated
COPY report.html .
COPY data.js .

RUN pip install -r requirements.txt


# update cronjob to run python script every day, should be run out of /opt/app
RUN echo "* */6 * * * root cd /opt/app && /usr/local/bin/python /opt/app/download_osv_data.py --force" > /etc/cron.d/refresh_oss_vulns
RUN chmod 0644 /etc/cron.d/refresh_oss_vulns
# RUN crontab /etc/cron.d/refresh_oss_vulns   # ends up with duplicated cron job
# Create the log file to be able to run tail
RUN touch /var/log/cron.log
# RUN cron && tail -f /var/log/cron.log



RUN adduser --disabled-password --gecos '' myuser
# Give 'myuser' permission to run 'service cron start' without a password
RUN echo "myuser ALL=(ALL) NOPASSWD: /usr/sbin/service cron start" >> /etc/sudoers
RUN echo "myuser ALL=(ALL) NOPASSWD: /usr/local/bin/python /opt/app/download_osv_data.py --force" >> /etc/sudoers


USER myuser

EXPOSE 3001

# CMD [ "python", "./download_osv_data.py"]
# disable directory listing

CMD ["/bin/bash", "-c", "sudo service cron start && sudo /usr/local/bin/python /opt/app/download_osv_data.py --force & /usr/local/bin/python run_server.py"]