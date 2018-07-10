FROM python:3.6

WORKDIR /app

RUN pip install pytest
RUN pip install testfixtures

COPY requirements.txt /app/

RUN pip install -r requirements.txt