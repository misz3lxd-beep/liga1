from flask import Flask

liga1 = Flask(__name__)

@liga1.route("/")
def home():
    return "Działa Flask na Azure!"

if liga1 == "main":
    liga1.run()