# coding: UTF-8

# google spreadsheets link
# https://docs.google.com/spreadsheets/d/1JapJBtQz1ex8Wwyfw9SGkJ6CleplS7QrmT7SXMn3RJs/edit#gid=0


# # runtime: python37
# handlers:
# - url: /.*
#   secure: always
#   script: auto


from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from pandas import DataFrame

import tabula
test = tabula.environment_info()
print("TEST")
print(test)

import pygsheets
client = pygsheets.authorize(service_file="credentials.json")
sheet = client.open("COVID19_japan")
wks = sheet[0]

import pdfplumber
from io import BytesIO

import datetime
import json
json_open = open('prefecture_list.json', 'r', encoding='utf-8_sig')
prefecture_json = json.load(json_open)

def parsePrefectureName(key, items):
    values = [x['en'] for x in items if 'name' in x and 'en' in x and x['name'] == key]
    return values[0] if values else None

app = Flask(__name__)

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')

@app.route("/tracker", methods=["GET", "POST"])
def get_pdflink():

    errors = []

    # get the current data date from google spreadsheet cell I2
    current_data = wks.get_value("I2")
    print("CURRENT DATA IS " + current_data)

    # get the date of update from the latest PDF on the website
    target_url = "https://www.mhlw.go.jp/stf/covid-19/kokunainohasseijoukyou.html#h2_1"
    r = requests.get(target_url)

    soup = BeautifulSoup(r.content, 'lxml')

    search = soup.find_all(text=re.compile("各都道府県の検査陽性者の状況"))
    
    print(search)

    get_tag = soup.find("a", text=re.compile("^各都道府県の検査陽性者の状況"))
    
    if get_tag is not None:

        pdf_link = get_tag.get("href")

        print(pdf_link)

        if not pdf_link.startswith('https://'):
            pdf_link = 'https://www.mhlw.go.jp' + pdf_link
        else:
            print("pdf_link captured")
        
        print(pdf_link)
        
    else:
        print("The PDF file is currently not available on the website")
        errors.append(
            "The PDF file is currently not available on the website"
        )

    rq = requests.get(pdf_link)
    
    pdf = pdfplumber.open(BytesIO(rq.content))

    pdf_text = pdf.pages[0]
    line_with_date = pdf_text.extract_words()
    published_date = line_with_date[1]

    print(published_date["text"])
    print(type(published_date["text"])) #string
    date = published_date["text"]
    latest_pdf_date = datetime.datetime.strptime(date, '%Y/%m/%d')
    # 2020-12-22
    latest_pdf_date_data = latest_pdf_date.strftime("%d %B, %Y")
    print(latest_pdf_date_data)
    

    if request.method == "POST":
       return show_data(pdf_link, latest_pdf_date_data)
               

    return render_template("public/upload_pdf.html", current_data = current_data, latest_pdf_date_data = latest_pdf_date_data, errors=errors)
   

def show_data(pdf_link,latest_pdf_date_data):

    df_list = tabula.read_pdf(
        pdf_link, pages='all', lattice=True, multiple_tables=True)

    print(df_list[0])
    
    target_df = DataFrame(df_list[0])
    print(target_df)

    column = target_df.columns.values
    print("PRINTING")
    print(column)
    name = target_df.columns
    print(name)


    # target_df = target_df.drop([0])
    
    # removing unnecessary column
    target_df = target_df[['都道府県名','陽性者数','PCR検査\r実施人数※1','入院治療等を\r要する者(人)\rうち重症※6','退院又は療養解除\rとなった者の数\r(人)','死亡(累積)\r(人)', 'Unnamed: 0']]
    print(target_df.columns)

    # rename column names in English
    target_df.rename(columns={'都道府県名':'Prefecture - JPN',
                            '陽性者数':'Confirmed',
                            'PCR検査\r実施人数※1':'Tested',
                            '入院治療等を\r要する者(人)\rうち重症※6':'Active',
                            '退院又は療養解除\rとなった者の数\r(人)':'Critical Condition',
                            '死亡(累積)\r(人)':'Recovered', 
                            'Unnamed: 0': 'Deaths'}, inplace=True)
    print(target_df.columns)

    print(target_df.dtypes)

    # remove unwanted characters 
    # remove = re.compile('^※')

    target_df['Prefecture - JPN'] = target_df['Prefecture - JPN'].str.strip('※123456789 ()')
    target_df['Prefecture - JPN'] = target_df['Prefecture - JPN'].str.replace(' ', '')

    # test = '青森'
    # print(type(prefecture_json))
    # print(parsePrefectureName(test, prefecture_json))

    lst = []
    for x in target_df['Prefecture - JPN']:
        # print(x)
        # return x
        if x == "その他":
            # print("OTHER")
            EN = "Other"
        elif x == "合計":
            # print("TOTAL")
            EN = "Total"
        else:
            # print(parsePrefectureName(x, prefecture_json))
            EN = parsePrefectureName(x, prefecture_json)
        lst.append(EN)

    
    # print(lst)
    target_df.insert(1, 'Prefecture - ENG', lst)
    print("Prefecture ENG COLUMN ADDED")
    
    # remove commas
    target_df['Confirmed'] = target_df['Confirmed'].str.replace(',', '')

    # convert data type from string to integer
    target_df['Confirmed'] = pd.to_numeric(target_df['Confirmed'])

    # Remove unnecessary row
    target_df = target_df[1:]

    test_df = target_df[0:4]
    print(test_df)

    # Exporting the data
    # DataFrame is exported and updates Google Sheets under morikaglobal account
    print("First worksheet accessed")
    wks.update_value("I2", latest_pdf_date_data)
    wks.set_dataframe(target_df, (1,1))

    print("The worksheet has now been updated with the latest data")

    current_data = wks.get_value("I2")
    print("CURRENT DATA IS " + current_data)
    # return (current_data)

    return render_template("public/data_updated.html", current_data = current_data)



if __name__ == "__main__":
    app.run()
