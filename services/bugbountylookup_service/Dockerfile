FROM python:latest

# Create user
RUN useradd -ms /bin/bash app
USER app

WORKDIR /app

COPY requirements.txt .
COPY findBB.py .

RUN pip install -r requirements.txt

CMD [ "python", "./findBB.py", "-web"]
