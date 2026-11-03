#sub
FROM python:3.7.1-slim

MAINTAINER Stef van der Struijk <stefstruijk+github@protonmail.ch>

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  gcc

WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY main.py /app/main.py

# allow other containers/PCs to connect; maybe not necessary
EXPOSE 5551

# when using docker-compose, this command can be overwritten
CMD ["python", "main.py", "--ip", "0.0.0.0"]
