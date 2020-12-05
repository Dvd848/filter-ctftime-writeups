from flask import Flask, Response, render_template, url_for, send_from_directory
from enum import Enum
from flask.logging import create_logger
from user import User, MAX_CTF_ENTRIES, MAX_ENTRY_NAME_LEN
from database import ENTRY_SEPARATOR, PATH_TO_CTF_NAMES, UID_PLACEHOLDER, PATH_TO_USER_DATA, KEY_USER_CTF_NAMES
from collections import namedtuple
from typing import Dict, List
import filter
import requests
import os
import utils

class HttpStatus(Enum):
    """HTTP Status Codes."""
    HTTP_500_INTERNAL_SERVER_ERROR = 500

class PageIds(utils.FlattenableEnum, Enum):
    """Enumeration of page IDs.

    Subclassing Enum directly works around a bug in pylint
    https://github.com/PyCQA/pylint/issues/533
    """
    INDEX      = "index"
    LOGIN      = "login"
    TOS        = "tos"
    SETTINGS   = "settings"
    FILTER     = "filter"

# Definitions related to a cookie used to decide whether to display a "logged in" menu or a "logged out" menu.
# Since this is simply used for the navigation menu, the cookie is not signed and can be manpulated by the user.
# The cookie should not be relied on for anything which requires authorization.
# TODO: Consider moving to Firebase's JWT 
COOKIE_MENU_TYPE = "menu_type" # Cookie name
COOKIE_MENU_TYPE_LOGGED_IN = "logged_in" # Value to represent that "logged in" menu should be shown

# A menu entry for the navigation menu
MenuItem = namedtuple("MenuItem", "href id caption")

def create_app():
    app = Flask("ctftime-writeups")

    logger = create_logger(app)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                'images/favicon/favicon.ico')

    @app.template_global()
    def url_for_cache(endpoint, **values):
        """A wrapper for the built-in url_for function, adding cache control.

        A wrapper for the built-in url_for function, which adds a "cache" parameter to the 
        resource path containing the last modification date of the resource.
        This is used to invalidate browser cache once the resource has changed.
        """
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
    def template_globals() -> dict:
        """Returns a dictionary of constants which should be available accross all templates."""

        # If one of the values in the dictionary isn't a string, it should be an object
        # which has an as_flat_dict() method that returns a dictionary of string->string values.
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
    def get_flat_constants(local_constants: Dict[str, str]) -> Dict[str, str]:
        """Constants which should be used by the current page.

        Returns a dictionary of constants that should be used by the current page.
        This includes the global constants in addition to constants relevant only for the 
        current page.
        Both keys and values in the dictionary must be strings.
        
        Args:
            local_constants:
                A dictionary of constants used only in the current page.
                They will be added to the constants dictionary returned by this function.

        Returns:
            A dictionary of constants to be used on the page, as strings, consisting of the global
            and local constants.
        """
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
    def get_menu(cookies: dict) -> List[MenuItem]:
        """Returns the menu items to be displayed in the navigation bar.

        Args:
            cookies:
                Flask's request.cookies dictionary.
        
        Returns:
            A list of MenuItems representing the navigation menu, based on whether 
            the menu should includes entries for logged in or logged out users.
        """
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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host = '0.0.0.0', threaded = True, port = 5000)