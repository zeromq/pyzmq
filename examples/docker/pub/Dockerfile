#pub
FROM python:3.7.1-slim

MAINTAINER Stef van der Struijk <stefstruijk+github@protonmail.ch>

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  gcc

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY main.py /app/main.py

# when using docker-compose, this command can be overwritten
# Change "yo.ur.i.p" to your machine IP (something similar to: "192.168.99.1") when using `docker run `
CMD ["python", "main.py", "--ip", "yo.ur.i.p"]
