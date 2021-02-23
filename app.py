from flask import Flask, render_template, request

import pygsheets
client = pygsheets.authorize(service_file="google-credentials.json")
sheet = client.open("COVID19_japan")
wks = sheet[0]

app = Flask(__name__)

@app.route("/")
def favicon():
    
    # get the current data date from google spreadsheet cell I2
    
    current_data = wks.get_value("I2")
    print("CURRENT DATA IS " + current_data)
    return "Hello buidpack success" 


if __name__ == "__main__":
    app.run()