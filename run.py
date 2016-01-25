from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import json
import data_json_counts  # Code to run data.json dataset counts

 
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
 


@app.route("/")
@app.route("/data")
def data():
    csv_data = data_json_counts.update_csv_from_snapshots()
    #return render_template('dataset_count_by_source.html',**locals())

    return render_template('dataset_count_by_source.html',csv_data=csv_data)
 
 

 
@app.route("/hello")
def hello():
    return "Hello World!"
 
 
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
    #app.run(host='54.84.25.124')  # Better not to hard code
    #app.run(host='0.0.0.0')
