FROM python:3-slim
WORKDIR /app

COPY requirements.txt /app
RUN python3 -m venv venv
RUN ./venv/bin/pip3 install --no-cache-dir -r ./requirements.txt

COPY static /app/static/
COPY templates /app/templates/
COPY *.json /app/
COPY *.py /app/

CMD /app/venv/bin/waitress-serve --call run:get_app
