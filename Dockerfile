FROM python:3.12.1-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

ENV IN_DOCKER=1
COPY ./src .

CMD [ "python", "./main.py" ]
