# Use a lightweight Python image based on Debian
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app


# Update package lists and install necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends wget curl jq libicu72 cron sudo


# downloading hardcoded version as there is currently an issue installing ps on debian 12
# RUN wget https://github.com/PowerShell/PowerShell/releases/download/v7.4.5/powershell_7.4.5-1.deb_amd64.deb && \
#     dpkg -i powershell_7.4.5-1.deb_amd64.deb && \
#     apt-get install -f && \
#     rm powershell_7.4.5-1.deb_amd64.deb



# Only works in Arm, even though running in Docker. If architecture of host changes, this must be changed as well.
RUN wget https://github.com/PowerShell/PowerShell/releases/download/v7.4.5/powershell-7.4.5-linux-arm64.tar.gz && \
    mkdir powershell && \
    tar -xvf powershell-7.4.5-linux-arm64.tar.gz -C powershell && \
    cd powershell && \
    chmod +x pwsh

ENV PATH="/app/powershell:${PATH}"


# # Copy the requirements.txt file (if you have one) to install pip packages
COPY requirements.txt .

# # Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# update cronjob to run python script every day, should be run out of /opt/app
RUN echo "0 0 * * * root cd /app && /bin/bash /app/0_runAll.sh" > /etc/cron.d/refresh_web3_vulns
RUN chmod 0644 /etc/cron.d/refresh_web3_vulns
# RUN crontab /etc/cron.d/refresh_web3_vulns   # ends up with duplicated job
# Create the log file to be able to run tail
RUN touch /var/log/cron.log
# RUN cron && tail -f /var/log/cron.log



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

RUN chmod +x /app/0_runAll.sh

VOLUME /app/contract_monitoring
VOLUME /app/public

COPY run_server.py .
# CMD ["/bin/bash", "-c", "/usr/sbin/service cron start && /usr/local/bin/python run_server.py"]
CMD ["/bin/bash", "-c", "/usr/sbin/service cron start && /usr/local/bin/python run_server.py"]
