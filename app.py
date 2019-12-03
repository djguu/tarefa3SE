from flask import Flask
from templates.csvExtract import *

app = Flask(__name__)


@app.route('/')
def home():
    return "<h1> Hello World </h1>"


app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True, port=8080)


