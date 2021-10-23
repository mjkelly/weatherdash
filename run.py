import flask

import weatherdash

weatherdash.init_logging()
app = flask.Flask(__name__)
dash = weatherdash.Dashboard(app)

def get_app():
    return app


@app.route('/')
def weather():
    """This is the main page. It shows the weather dashboard."""
    return dash.weather_impl("tmpl.html")


@app.route('/reloader')
def reloader():
    """This page encloses a call to /inner, and serves a user-facing page."""
    return dash.weather_impl("reloader.html")


@app.route('/inner')
def weather_inner():
    """This is just the part of the main page inside <body>.
    
    Internal endnpoint for /reloader."""
    return dash.weather_impl("inner.html")


@app.route('/fake')
def fake():
    """This loads data from testdata.json.

    It's for testing, so you can tweak the code and reload often without
    worrying about hitting the weather API too much.
    """
    return dash.fake_handler()