FROM python:latest

WORKDIR /opt/app

COPY requirements.txt ./
COPY server.py ./

RUN pip install -r requirements.txt

CMD [ "python", "./server.py"]