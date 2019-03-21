FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /elo
WORKDIR /elo
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["main.py"]
