from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello world!"

if app == "main":
    app.run()