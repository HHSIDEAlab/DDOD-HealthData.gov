######################
##  2015-11-25  Created by David Portnoy
######################

# For APIs
import json
import requests

# For data manipulation
import pandas as pd
from numpy import random  # For random

# For charting
from bokeh.charts import Bar, output_file, reset_output, save, show
#from bokeh.plotting import output_file, reset_output, save, show
#from bokeh.plotting import figure
from bokeh.plotting import reset_output
from bokeh.palettes import brewer
from bokeh.sampledata.autompg import autompg as df
from bokeh.io import output_notebook  # For interactive within iPython notebook only

import getopt, sys  # For command line args



#--- Global constants ---
OPTS = [("h","help"), ("o:","output="), ("u","url="), ("v", "verbose")]


def usage():
    print("This script generates a graph from GitHub issues")
    print("  Params: ")
    print(str(OPTS).replace('), (','\n').replace(', ',' or ').strip('[]()'))


def process_params():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 
                                   "".join([opt[0] for opt in OPTS]),
                                    [opt[1] for opt in OPTS]
                                  )
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err) # will print something like "option -a not recognized"
        getopt.usage()
        sys.exit(2)
    #--- Clear params vars ---
    output_file = None
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output_file = a
        else:
            assert False, "unhandled option"
    # ...




def read_data():

    #sURL = 'https://api.github.com/events'
    issues_url = "https://api.github.com/repos/demand-driven-open-data/ddod-intake/issues?state=all&per_page=10000"
    issues_get = requests.get(issues_url)
    # print(issues_get.headers)


    # convert to JSON
    issues_string = issues_get.text
    issues_json = json.loads(issues_string)



    # Define constants
    LIST_LIMIT = 0  # For testing only
    IGNORE_LABEL = "Not Use Case"  # Ignore entries not use cases
    TABLE_COLUMNS = ['use_case_id','title','value_delivered','status']
    TABLE_COLUMNS_MAP = [{'use_case_id':'number'},
               {'title':'title'},
               {'value_delivered':'name'},
               {'status':'state'}]
    OWNER_LABEL = 'Owner:'
    STATE_LABEL = 'STATE:'
    VALUE_LABEL = 'VAL:'


    # Loop through items, building array of dictionaries
    issues_table = []

    for index, item in enumerate(issues_json):

        not_use_case = any(IGNORE_LABEL in ddd['name'] for ddd in item['labels'])
        if not_use_case:
            continue  # Don't add rows for this use case

        issue_row = {}
        issue_row.update({'use_case_id':item['number']})
        issue_row.update({'title':item['title']})
        issue_row.update({'status':item['state']})

# Create list of labels
        for label in item["labels"]:
            if VALUE_LABEL in label["name"]:

                issue_row.update({'value_delivered':
                          label["name"].replace(VALUE_LABEL,'')
                          .replace(':','-').strip()})
                
                if LIST_LIMIT: print('Appending: ',issue_row)
                issues_table.append(dict(issue_row))
            
        # Limit for testing
        if LIST_LIMIT:
            if index+1 >= LIST_LIMIT:
                break
        
    if LIST_LIMIT: print(issues_table)


    # Create dataframe for Bokeh
    issues_df = pd.DataFrame(data=issues_table, columns=TABLE_COLUMNS)


def output_chart():
    ISSUES_TITLE = "Number of Use Cases by Value delivered"
    ISSUES_FILE  = "value_delivered.html"
    INTERACTIVE_MODE = False


    issues_chart = Bar(issues_df, label='value_delivered', 
               values='status', agg='count', stack='status',
               title=ISSUES_TITLE, 
               xlabel="Value Delivered",ylabel="Number of Use Cases",
               legend='top_right',
               color=brewer["GnBu"][3]
              )


    #--- Configure output ---
    reset_output()

    if INTERACTIVE_MODE:
        output_notebook()   # Show inline
        show(issues_chart)
    else:
        # Static file
        output_file('value_delivered.html', title=ISSUES_TITLE, 
            autosave=True, mode='inline', 
            root_dir=None
               )   # Generate file
        save(issues_chart,filename=ISSUES_FILE)



def main():
    process_params()
    read_data()
    output_chart()


if __name__ == "__main__":
    main()

