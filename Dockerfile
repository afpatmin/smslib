FROM python:3.7

WORKDIR /home/app/
COPY . .
RUN pip install -r requirements.txt
RUN apt update && apt install zip
RUN git config pull.rebase false