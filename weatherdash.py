import urllib.request
import json
import datetime
import logging
import logging.config
import time

import pytz
import flask
import jinja2

# Initial setup and UGLY UGLY GLOBALS.
FAKE_DATA_FILE = 'testdata.json'
API_URL_FMT = 'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&appid={key}&units={units}'
_MAX_DATA_AGE_SECONDS = 5 * 60

class Dashboard:
    def __init__(self, app):
        self.app = app
        self.init_app()

        self._data = None
        self._data_updated = 0
        self.logger = app.logger
        with open("config.json", "r") as fh:
            self.config = json.load(fh)
        self._tz = pytz.timezone(self.config['tz'])

    def init_app(self):
        self.app.logger.setLevel(logging.INFO)
        self.app._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml']))

    def get_data(self):
        func_start = time.time()
        config = self.config

        url = API_URL_FMT.format(lat=config['lat'],
                                lon=config['lon'],
                                key=config['api_key'],
                                exclude='',
                                units=config['units'])
        self.logger.info(f'Remote request to {url}...')

        resp = urllib.request.urlopen(url)
        resp_str = resp.read().decode('utf-8')

        func_elapsed = time.time() - func_start
        self.logger.info(f"get_data took {func_elapsed:.2f}s")
        return resp_str


    def update_state(self, data_str):
        func_start = time.time()

        time_fmt = self.config['time_fmt']
        data = json.loads(data_str)
        dt = data['current']['dt']
        as_of_dt = datetime.datetime.fromtimestamp(dt, tz=self._tz)
        state_now = datetime.datetime.now(tz=self._tz)
        sunrise = data['current']['sunrise']
        sunset = data['current']['sunrise']
        daynight = 'day' if dt > sunrise and dt < sunset else 'night'
        state = {
            'data': data,
            'as_of': dt,  # unix timestamp
            'temp': round(data['current']['temp']),
            'feels_like': round(data['current']['temp']),
            'as_of_dt': as_of_dt,
            'as_of_str': as_of_dt.strftime(time_fmt),
            'now': state_now,
            'now_str': state_now.strftime(time_fmt),
            'w': None,
            'daynight': daynight,
        }
        if len(data['current']['weather']):
            w = data['current']['weather'][0]
            state['w'] = w
            state['desc'] = w['description']
            state['w_id'] = w['id']
            state['w_icon'] = w['icon']

        func_elapsed = time.time() - func_start
        self.logger.info(f"update_state took {func_elapsed:.2f}s")
        return state


    def format_page(self, state, template_name):
        time_fmt_short = self.config['time_fmt_short']
        hours_to_show = 8
        hourly = []
        for h in state['data']['hourly'][:hours_to_show]:
            dt = datetime.datetime.fromtimestamp(h['dt'], tz=self._tz)
            dt_str = dt.strftime(time_fmt_short)
            weather_str = h['weather'][0]['description']
            weather_icon = h['weather'][0]['icon']
            temp = round(h['temp'])
            hourly.append({
                'rain': 'rain' if 'rain' in h else '',
                'weather_str': weather_str,
                'weather_icon': weather_icon,
                'dt_str': dt_str,
                'temp': temp,
            })

        tmpl = self.app._env.get_template(template_name)
        return tmpl.render(
            css_url=flask.url_for('static', filename='main.css'),
            desc=state['desc'],
            time=state['now_str'],
            temp=state['temp'],
            feels_like=state['feels_like'],
            w_icon=state['w_icon'],
            updated=str(datetime.datetime.now(tz=self._tz)),
            hourly=hourly,
            daynight=state['daynight'],
        )


    def weather_impl(self, template_name):
        data_age = time.time() - self._data_updated
        self.logger.info(
            f"data_age = {data_age:.1f}, last updated {self._data_updated:.1f}")
        if self._data is None or data_age > _MAX_DATA_AGE_SECONDS:
            self.logger.info(f"updating data")
            self._data = self.get_data()
            self._data_updated = time.time()
        state = self.update_state(self._data)
        return self.format_page(state, template_name)


    def fake_handler(self):
        self.logger.warning(f'Using fake data from {FAKE_DATA_FILE}!')
        with open(FAKE_DATA_FILE, 'r') as fh:
            state = self.update_state(fh.read())
        return self.format_page(state, "tmpl.html")


def init_logging():
    logging.config.dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'main': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default',
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['main'],
        },
    })