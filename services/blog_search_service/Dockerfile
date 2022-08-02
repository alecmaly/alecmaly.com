from python:latest

WORKDIR /opt/app

COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

CMD [ "/bin/bash", "./run.sh" ]