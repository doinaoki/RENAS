FROM python:3.11

RUN apt-get update && apt-get install -y \
    maven \
    openjdk-17-jre
RUN pip install --upgrade pip

COPY requirements.txt ./work
RUN pip install --no-cache-dir -r requirements.txt
