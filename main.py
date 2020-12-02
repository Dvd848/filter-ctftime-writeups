from flask import Flask, Response, render_template, url_for
from enum import Enum
from flask.logging import create_logger
from user import User, MAX_CTF_ENTRIES, MAX_ENTRY_NAME_LEN
from database import ENTRY_SEPARATOR
import filter
import requests
import os
import utils

class HttpStatus(Enum):
    HTTP_500_INTERNAL_SERVER_ERROR = 500

class PageIds(Enum):
    PAGE_INDEX      = "index"
    PAGE_LOGIN      = "login"
    PAGE_TOS        = "tos"
    PAGE_SETTINGS   = "settings"
    PAGE_FILTER     = "filter"

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

@app.template_global()
def get_global_constants():
    res = dict()

    res["COOKIE_MENU_TYPE"] = "menu_type"
    res["COOKIE_MENU_TYPE_LOGGED_IN"] = "logged_in"
    res.update(utils.enum_to_dict(PageIds))

    return res

@app.route('/')
def index_page():
    page = PageIds.PAGE_INDEX.value
    return render_template(f'{page}.html', page_id = page)

@app.route('/login')
def login_page():
    page = PageIds.PAGE_LOGIN.value
    return render_template(f'{page}.html', title = "Sign-up / Sign-in", page_id = page)

@app.route('/tos')
def tos_page():
    page = PageIds.PAGE_TOS.value
    return render_template(f'{page}.html', title = "Terms &amp; Conditions", page_id = page)

@app.route('/settings')
def settings_page():
    page = PageIds.PAGE_SETTINGS.value
    return render_template(f'{page}.html', title = "Settings", page_id = page)

@app.route('/filter')
def filter_page():
    page = PageIds.PAGE_FILTER.value
    constants = get_global_constants()
    constants.update(MAX_CTF_ENTRIES = MAX_CTF_ENTRIES, 
                     ENTRY_SEPARATOR = ENTRY_SEPARATOR,
                     MAX_ENTRY_NAME_LEN = MAX_ENTRY_NAME_LEN)
    return render_template(f'{page}.html', title = "Filter", page_id = page, constants = constants)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)