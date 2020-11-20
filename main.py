from flask import Flask, request
app = Flask("ctftime-writeups")

@app.route('/')
def index():
    return "<h1>Hello World!</h1>"

if __name__ == '__main__':
    app.run(host = '0.0.0.0', threaded = True, port = 5000)