# This file is useless when hosting local

from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "Bot is online"


def run():
    app.run(host='0.0.0.0', port=8080)


def open_web():
    t = Thread(target=run)
    t.start()
