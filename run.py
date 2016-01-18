from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import json
import urllib2
import data_json_counts

 
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
 
def getExchangeRates():
    rates = []
    response = urllib2.urlopen('http://api.fixer.io/latest')
    data = response.read()
    rdata = json.loads(data, parse_float=float)
 
    rates.append( rdata['rates']['USD'] )
    rates.append( rdata['rates']['GBP'] )
    rates.append( rdata['rates']['HKD'] )
    rates.append( rdata['rates']['AUD'] )
    return rates
 
@app.route("/")
def index():
    rates = getExchangeRates()
    return render_template('test.html',**locals())      







@app.route('/chart_ninja')
def chart_ninja():
	data = [('Sunday', 48), ('Monday', 27), ('Tuesday', 32), ('Wednesday', 42),
			('Thursday', 38), ('Friday', 45), ('Saturday', 52)]
	return render_template('chart_ninja.html', data=data)



@app.route("/data")
def data():
    csv_data = data_json_counts.update_csv_from_snapshots()
    #return render_template('dataset_count_by_source.html',**locals())

    '''
    csv_data = [
            ['Year', 'Sales', 'Expenses'],
            ['1/11/2015',  100,      400],
            ['1/12/2015',  120,      300],
            ['1/13/2015',  130,      100],
            ['1/14/2015',  1170,      460]
        ]
          
    '''          
    return render_template('dataset_count_by_source.html',csv_data=csv_data)
 
 



 
@app.route("/hello")
def hello():
    return "Hello World!"
 
 
if __name__ == "__main__":
    app.run(debug=True)