from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Działa Flask na Azure!"

if app == "main":
    app.run()