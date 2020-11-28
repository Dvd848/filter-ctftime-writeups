from flask import Flask, Response, render_template
from enum import Enum
from flask.logging import create_logger
from user import User, MAX_CTF_ENTRIES, MAX_ENTRY_NAME_LEN
from database import ENTRY_SEPARATOR
import filter
import requests

class HttpStatus(Enum):
    HTTP_500_INTERNAL_SERVER_ERROR = 500

app = Flask("ctftime-writeups")
logger = create_logger(app)

@app.route("/writeups/<string:uid>")
def writeups(uid):
    try:
        user = User(uid)

        headers = {
            'User-Agent': 'CTFTime Writeups Filter 1.0',
        }
        r = requests.get("https://ctftime.org/writeups/rss/", headers = headers)

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
    return render_template('index.html', title='Writeup Feed Filter')

@app.route('/filter')
def filter_page():
    return render_template('filter.html',   title='Writeup Feed Filter', 
                                            max_ctf_entries = MAX_CTF_ENTRIES, 
                                            entry_separator = ENTRY_SEPARATOR,
                                            max_entry_name_len = MAX_ENTRY_NAME_LEN)

@app.route('/login')
def login_page():
    return render_template('login.html', title='Login')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)