from flask import Flask, Response, render_template, url_for
from enum import Enum
from flask.logging import create_logger
from user import User, MAX_CTF_ENTRIES, MAX_ENTRY_NAME_LEN
from database import ENTRY_SEPARATOR, PATH_TO_CTF_NAMES, UID_PLACEHOLDER, PATH_TO_USER_DATA, KEY_USER_CTF_NAMES
from collections import namedtuple
import filter
import requests
import os
import utils

class HttpStatus(Enum):
    HTTP_500_INTERNAL_SERVER_ERROR = 500

class PageIds(utils.FlattenableEnum, Enum):
    # Subclassing Enum directly works around a bug in pylint
    # https://github.com/PyCQA/pylint/issues/533
    INDEX      = "index"
    LOGIN      = "login"
    TOS        = "tos"
    SETTINGS   = "settings"
    FILTER     = "filter"

COOKIE_MENU_TYPE = "menu_type"
COOKIE_MENU_TYPE_LOGGED_IN = "logged_in"

MenuItem = namedtuple("MenuItem", "href id caption")

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

@app.context_processor
def template_globals():
    return dict(
        COOKIE_MENU_TYPE = COOKIE_MENU_TYPE,
        COOKIE_MENU_TYPE_LOGGED_IN = COOKIE_MENU_TYPE_LOGGED_IN,
        PATH_TO_CTF_NAMES = PATH_TO_CTF_NAMES,
        UID_PLACEHOLDER = UID_PLACEHOLDER,
        PATH_TO_USER_DATA = PATH_TO_USER_DATA,
        KEY_USER_CTF_NAMES = KEY_USER_CTF_NAMES,
        PageIds = PageIds
    )


@app.template_global()
def get_flat_constants(local_constants):
    res = dict()

    globals = template_globals()
    globals.update(local_constants)
    for key, value in globals.items():
        if hasattr(value, "as_flat_dict"):
            res.update(value.as_flat_dict())
        else:
            res[key] = value

    return res

@app.template_global()
def get_menu(cookies):
    res      = [MenuItem('/',                   PageIds.INDEX.value,    'Home')]

    if cookies.get(COOKIE_MENU_TYPE) == COOKIE_MENU_TYPE_LOGGED_IN:
        res += [MenuItem('/filter',             PageIds.FILTER.value,   'Filter'),
                MenuItem('/settings',           PageIds.SETTINGS.value, 'Settings'),
                MenuItem('javascript:void(0)',  'logout',               'Sign Out')]
    else:
        res += [MenuItem('/login',              PageIds.LOGIN.value,    'Sign In')]

    return res

@app.route('/')
def index_page():
    page = PageIds.INDEX.value
    return render_template(f'{page}.html', page_id = page)

@app.route('/login')
def login_page():
    page = PageIds.LOGIN.value
    return render_template(f'{page}.html', title = "Sign-up / Sign-in", page_id = page)

@app.route('/tos')
def tos_page():
    page = PageIds.TOS.value
    return render_template(f'{page}.html', title = "Terms &amp; Conditions", page_id = page)

@app.route('/settings')
def settings_page():
    page = PageIds.SETTINGS.value
    return render_template(f'{page}.html', title = "Settings", page_id = page)

@app.route('/filter')
def filter_page():
    page = PageIds.FILTER.value
    local_constants = dict( MAX_CTF_ENTRIES = MAX_CTF_ENTRIES, 
                            ENTRY_SEPARATOR = ENTRY_SEPARATOR,
                            MAX_ENTRY_NAME_LEN = MAX_ENTRY_NAME_LEN)
    return render_template(f'{page}.html', title = "Filter", page_id = page, local_constants = local_constants)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)