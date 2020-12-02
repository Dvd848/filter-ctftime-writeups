from flask import Flask, Response, render_template, url_for
from enum import Enum
from flask.logging import create_logger
from user import User, MAX_CTF_ENTRIES, MAX_ENTRY_NAME_LEN
from database import ENTRY_SEPARATOR
import filter
import requests
import os

class HttpStatus(Enum):
    HTTP_500_INTERNAL_SERVER_ERROR = 500

app = Flask("ctftime-writeups")
logger = create_logger(app)

@app.template_global()
def url_for_cache(endpoint, **values):
    try:
        if ("filename" in values):
            mod_date = str(os.path.getmtime(os.path.join(endpoint, values["filename"])))
            values["cache"] = mod_date
    except Exception:
        pass
    return url_for(endpoint, **values)

@app.route("/writeups/<string:uid>")
def writeups(uid):
    try:
        user = User(uid)

        headers = {
            'User-Agent': 'CTFTime Writeups Filter 1.0',
        }
        r = requests.get("https://ctftime.org/writeups/rss/", headers = headers)

        if (not r.headers['content-type'].startswith("application/rss+xml")):
            raise Exception("Invalid content type received from CTFTime: {}".format(r.headers['content-type']))

        content = filter.filter_writeups(r.text, user.ctf_list)

        res = Response(
            response = content,
            status = r.status_code,
            content_type = r.headers['content-type'],
        )
    except Exception as e:
        logger.error(e)
        res = Response(
            status = HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR.value
        )
    
    return res


@app.route('/')
def index_page():
    return render_template('index.html', page_id = "index")

@app.route('/login')
def login_page():
    return render_template('login.html', title = "Sign-up / Sign-in", page_id = "login")

@app.route('/tos')
def tos_page():
    return render_template('tos.html', title = "Terms &amp; Conditions", page_id = "tos")

@app.route('/settings')
def settings_page():
    return render_template('settings.html', title = "Settings", page_id = "settings")

@app.route('/filter')
def filter_page():
    return render_template('filter.html', title = "Filter", page_id = "filter",
                                          max_ctf_entries = MAX_CTF_ENTRIES, 
                                          entry_separator = ENTRY_SEPARATOR,
                                          max_entry_name_len = MAX_ENTRY_NAME_LEN)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)