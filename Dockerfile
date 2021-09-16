FROM ubuntu:20.04
COPY . /app
WORKDIR /app
RUN apt-get update
RUN apt-get install -y python3 python3-venv
RUN python3 -m venv venv
RUN /app/venv/bin/pip3 install -r /app/requirements.txt
CMD /app/venv/bin/waitress-serve --call dash:get_app
