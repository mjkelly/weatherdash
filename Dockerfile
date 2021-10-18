FROM python:3-slim
WORKDIR /app

COPY requirements.txt /app
RUN python3 -m venv venv
RUN ./venv/bin/pip3 install --no-cache-dir -r ./requirements.txt

COPY static /app/static/
COPY templates /app/templates/
COPY config.json /app/
COPY dash.py /app/

CMD /app/venv/bin/waitress-serve --call dash:get_app
