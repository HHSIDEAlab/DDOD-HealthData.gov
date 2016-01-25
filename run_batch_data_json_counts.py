from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import data_json_counts  # Code to run data.json dataset counts

 
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


@app.route('/shutdown', methods=['POST'])
def shutdown_server():
    print( 'Server shutting down...')
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


 
@app.before_first_request
#@app.route("/")
#@app.route("/save_data_set_count_by_source")
def save_data():
    csv_data = data_json_counts.update_csv_from_snapshots()
    #return render_template('dataset_count_by_source.html',**locals())

    print( "render_template(dataset_count_by_source.html)...")
    html_template = render_template('dataset_count_by_source.html',csv_data=csv_data)

    #print( html_template)

    print( "Save HTML file...")
    with open("generated/data_json_counts.html", "w") as text_file:
       text_file.write(html_template)

    print( "shutdown_server()...")
    shutdown_server()
 


@app.route("/")
def home():
    return "Data saved and shutting down"

 
 
if __name__ == "__main__":
    print("running app.run...")
    app.run(debug=True, host='0.0.0.0', port=5001)
