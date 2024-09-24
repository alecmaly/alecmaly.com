# Use a lightweight Python image based on Debian
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app


# Update package lists and install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends wget curl jq libicu72 cron sudo


# downloading hardcoded version as there is currently an issue installing ps on debian 12
RUN wget https://github.com/PowerShell/PowerShell/releases/download/v7.4.5/powershell_7.4.5-1.deb_amd64.deb && \
    dpkg -i powershell_7.4.5-1.deb_amd64.deb && \
    apt-get install -f && \
    rm powershell_7.4.5-1.deb_amd64.deb




RUN adduser --disabled-password --gecos '' myuser
# Give 'myuser' permission to run 'service cron start' without a password
RUN echo "myuser ALL=(ALL) NOPASSWD: /usr/sbin/service cron start" >> /etc/sudoers


RUN chown -R myuser:myuser /app
USER myuser

# Update cronjob to run the python script every day as myuser
RUN echo "0 0 * * * cd /app && ./0_runAll.sh" > /tmp/refresh_oss_vulns
RUN crontab /tmp/refresh_oss_vulns



# # Copy the requirements.txt file (if you have one) to install pip packages
COPY requirements.txt .

# # Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# # Copy additional scripts and entrypoint
COPY 0_runAll.sh .
COPY 1_collect-scopes.py .
COPY 3_getGithubRepoCommitDetails.ps1 .
COPY 4_converToHTML.ps1 .
COPY 6_extractLiveContracts.py .
COPY 7_lookupProxies.py .
COPY 8_updateContractsList.py .
COPY 9_addPatchDiffDetails.ps1 .
COPY 10_review.ps1 .
COPY 11_generateHTMLReview.ps1 .

# import old data
COPY contract_monitoring contract_monitoring 

COPY web3contractreport.html public/web3contractreport.html
COPY web3repoupdates.html public/web3repoupdates.html

COPY run_server.py .
CMD ["/bin/bash", "-c", "sudo service cron start & /usr/local/bin/python run_server.py"]
