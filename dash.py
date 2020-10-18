import urllib.request
import json
import datetime
import logging
import flask
import time

# Initial setup
app = flask.Flask(__name__)
app.logger.setLevel(logging.INFO)
_MAX_DATA_AGE_SECONDS = 5 * 60
app._data = None
app._data_updated = 0

with open("config.json", "r") as fh:
    config = json.load(fh)
TIME_FMT = config['time_fmt']
TIME_FMT_SHORT = config['time_fmt_short']

# Constants
FAKE_DATA_FILE = 'testdata.json'
API_URL_FMT = 'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude={exclude}&appid={key}&units={units}'

TMPL = '''
<!doctype html>
<html lang="en">
    <title>Local Weather</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="30"/>
    <link rel="stylesheet" href="{css_url}">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <body class="{daynight}">
        <div class="main-container">
            <div class="left">
                <div class="time-now">
                    {time}
                </div>
                <div class="weather-container">
                    <div class="temp">
                        {temp}&deg; ({feels_like}&deg;)
                    </div>
                </div>
                <div class="weather-desc">
                    <div class="weather-desc-txt">{desc}</div>
                    <img src="https://openweathermap.org/img/wn/{w_icon}@2x.png" alt="Icon for {desc}">
                </div>
            </div>
            <div class="right">
                <div class="hourly-container">
                    {hourly}
                </div>
            </div>
        </div>
    </body>
</html>
'''


def get_data():
    func_start = time.time()

    url = API_URL_FMT.format(lat=config['lat'],
                             lon=config['lon'],
                             key=config['api_key'],
                             exclude='',
                             units=config['units'])
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
    as_of_dt = datetime.datetime.fromtimestamp(dt)
    state_now = datetime.datetime.now()
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


def format_page(state):
    hours_to_show = 8
    hourly = []
    for h in state['data']['hourly'][:hours_to_show]:
        dt = datetime.datetime.fromtimestamp(h['dt'])
        dt_str = dt.strftime(TIME_FMT_SHORT)
        weather_str = h['weather'][0]['description']
        weather_icon = h['weather'][0]['icon']
        url = "https://openweathermap.org/img/wn/{code}.png".format(
            code=weather_icon)
        temp = round(h['temp'])
        rain = 'rain' in h
        hourly.append(
            f"""<div class="hourly-txt{" rain" if rain else ""}">{dt_str}: {temp}&deg;</div>
            <div class="hourly-img"><img alt="{weather_str} icon" src="{url}"></div>
            """)

    return TMPL.format(
        css_url=flask.url_for('static', filename='main.css'),
        desc=state['desc'],
        time=state['now_str'],
        temp=state['temp'],
        feels_like=state['feels_like'],
        w_icon=state['w_icon'],
        updated=str(datetime.datetime.now()),
        hourly=''.join([f'<div class="hourly">{h}</div>' for h in hourly]),
        daynight=state['daynight'],
    )


@app.route('/')
def weather():
    """This is the main page. It shows the weather dashboard."""
    data_age = time.time() - app._data_updated
    app.logger.info(
        f"data_age = {data_age:.1f}, last updated {app._data_updated:.1f}")
    if app._data is None or data_age > _MAX_DATA_AGE_SECONDS:
        app.logger.info(f"updating data")
        app._data = get_data()
        app._data_updated = time.time()
    state = update_state(app._data)
    return format_page(state)


@app.route('/fake')
def fake():
    """This loads data from testdata.json.

    It's for testing, so you can tweak the code and reload often without
    worrying about hitting the weather API too much.
    """
    app.logger.warning(f'Using fake data from {FAKE_DATA_FILE}!')
    with open(FAKE_DATA_FILE, 'r') as fh:
        state = update_state(fh.read())
    return format_page(state)
