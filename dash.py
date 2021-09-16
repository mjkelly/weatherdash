import urllib.request
import json
import datetime
import logging
import time

import pytz
import flask
import jinja2

# Initial setup and UGLY UGLY GLOBALS.
FAKE_DATA_FILE = 'testdata.json'
API_URL_FMT = 'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&appid={key}&units={units}'


def init_app():
    a = flask.Flask(__name__)
    a.logger.setLevel(logging.INFO)
    a._data = None
    a._data_updated = 0

    with open("config.json", "r") as fh:
        a._config = json.load(fh)

    a._env = jinja2.Environment(
        loader=jinja2.PackageLoader('dash', 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml']))

    return a


app = init_app()
_MAX_DATA_AGE_SECONDS = 5 * 60
TIME_FMT = app._config['time_fmt']
TZ_STR = app._config['tz']
TZ = pytz.timezone(TZ_STR)
TIME_FMT_SHORT = app._config['time_fmt_short']


def get_app():
    return app


def get_data():
    func_start = time.time()

    url = API_URL_FMT.format(lat=app._config['lat'],
                             lon=app._config['lon'],
                             key=app._config['api_key'],
                             exclude='',
                             units=app._config['units'])
    app.logger.info(f'Remote request to {url}...')

    resp = urllib.request.urlopen(url)
    resp_str = resp.read().decode('utf-8')

    func_elapsed = time.time() - func_start
    app.logger.info(f"get_data took {func_elapsed:.2f}s")
    return resp_str


def update_state(data_str):
    func_start = time.time()

    data = json.loads(data_str)
    dt = data['current']['dt']
    as_of_dt = datetime.datetime.fromtimestamp(dt, tz=TZ)
    state_now = datetime.datetime.now(tz=TZ)
    sunrise = data['current']['sunrise']
    sunset = data['current']['sunrise']
    daynight = 'day' if dt > sunrise and dt < sunset else 'night'
    state = {
        'data': data,
        'as_of': dt,  # unix timestamp
        'temp': round(data['current']['temp']),
        'feels_like': round(data['current']['temp']),
        'as_of_dt': as_of_dt,
        'as_of_str': as_of_dt.strftime(TIME_FMT),
        'now': state_now,
        'now_str': state_now.strftime(TIME_FMT),
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
    app.logger.info(f"update_state took {func_elapsed:.2f}s")
    return state


def format_page(state, template_name):
    hours_to_show = 8
    hourly = []
    for h in state['data']['hourly'][:hours_to_show]:
        dt = datetime.datetime.fromtimestamp(h['dt'], tz=TZ)
        dt_str = dt.strftime(TIME_FMT_SHORT)
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

    tmpl = app._env.get_template(template_name)
    return tmpl.render(
        css_url=flask.url_for('static', filename='main.css'),
        desc=state['desc'],
        time=state['now_str'],
        temp=state['temp'],
        feels_like=state['feels_like'],
        w_icon=state['w_icon'],
        updated=str(datetime.datetime.now(tz=TZ)),
        hourly=hourly,
        daynight=state['daynight'],
    )


def weather_impl(template_name):
    data_age = time.time() - app._data_updated
    app.logger.info(
        f"data_age = {data_age:.1f}, last updated {app._data_updated:.1f}")
    if app._data is None or data_age > _MAX_DATA_AGE_SECONDS:
        app.logger.info(f"updating data")
        app._data = get_data()
        app._data_updated = time.time()
    state = update_state(app._data)
    return format_page(state, template_name)


@app.route('/')
def weather():
    """This is the main page. It shows the weather dashboard."""
    return weather_impl("tmpl.html")


@app.route('/inner')
def weather_inner():
    """This is just the part of the main page inside <body>."""
    return weather_impl("inner.html")


@app.route('/reloader')
def reloader():
    """This is just the part of the main page inside <body>."""
    return weather_impl("reloader.html")


@app.route('/fake')
def fake():
    """This loads data from testdata.json.

    It's for testing, so you can tweak the code and reload often without
    worrying about hitting the weather API too much.
    """
    app.logger.warning(f'Using fake data from {FAKE_DATA_FILE}!')
    with open(FAKE_DATA_FILE, 'r') as fh:
        state = update_state(fh.read())
    return format_page(state, "tmpl.html")


if __name__ == '__main__':
    print(f"port = {PORT}")
    app.run(host='0.0.0.0', port=PORT)
>>>>>>> 0c338d8796af5df4f1977f98b48f966cb990c1f1
