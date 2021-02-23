from flask import Flask, render_template, request


app = Flask(__name__)

@app.route("/")
def favicon():
    return "Hello World"


if __name__ == "__main__":
    app.run()