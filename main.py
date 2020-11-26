from flask import Flask, Response, render_template
from enum import Enum
from flask.logging import create_logger
import filter
import database
import requests

class HttpStatus(Enum):
    HTTP_500_INTERNAL_SERVER_ERROR = 500

app = Flask("ctftime-writeups")
logger = create_logger(app)
database.init()

@app.route("/writeups/<string:uid>")
def writeups(uid):
    try:
        if not database.is_valid_uid(uid):
            raise ValueError(f"Invalid UID: {uid}")

        headers = {
            'User-Agent': 'CTFTime Writeups Filter 1.0',
        }
        r = requests.get("https://ctftime.org/writeups/rss/", headers = headers)

        ctf_names = database.get_ctf_names(uid)
        content = filter.filter_writeups(r.text, ctf_names)

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
def index():
    return render_template('index.html', title='CTFTime Writeups')

@app.route('/login')
def login():
    return render_template('login.html', title='Login')

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)