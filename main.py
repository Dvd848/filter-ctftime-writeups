from flask import Flask, Response
from logic import filter_writeups
import requests

app = Flask("ctftime-writeups")

@app.route("/writeups")
def writeups():
    try:
        headers = {
            'User-Agent': 'CTFTime Writeups Filter 1.0',
        }
        r = requests.get("https://ctftime.org/writeups/rss/", headers = headers)
        res = Response(
            response = filter_writeups(r.text, ["test"]),
            status = r.status_code,
            content_type = r.headers['content-type'],
        )
    except Exception:
        # TODO
        pass

@app.route('/')
def index():
    return "<h1>Hello World!</h1>"

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)