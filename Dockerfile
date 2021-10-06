FROM python:3-slim
COPY . /app
WORKDIR /app
RUN python3 -m venv venv
RUN /app/venv/bin/pip3 install --no-cache-dir -r /app/requirements.txt
CMD /app/venv/bin/waitress-serve --call dash:get_app
