FROM python:latest

WORKDIR /app

COPY requirements.txt .
COPY findBB.py .

RUN pip install -r requirements.txt

CMD [ "python", "./findBB.py", "-web"]
