FROM python:latest
WORKDIR /opt
COPY requirements.txt /opt/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /opt/requirements.txt