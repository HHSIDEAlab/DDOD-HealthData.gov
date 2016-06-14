# coding: utf-8
#!/usr/bin/env python
######################
##  2016-06-13  Created by David Portnoy
######################

import json
import requests


BASE_URL = 'http://ddod.healthdata.gov/'
smw_url  = BASE_URL + 'api.php?action=query'
smw_url += '&generator=allpages'                 # Generator
smw_url += '&prop=links|extlinks|categories'     # Properties to show
smw_url += '&gaplimit=10000&ellimit=10000&cllimit=10000&pllimit=10000'  # Avoid limits by property type
smw_url += '&format=json&gapfilter=nonredirects&continue='  # Format and paging


def get_api_result(source_url):
    rget = requests.get(source_url)
    rget_text = rget.text
    rget_json = json.loads(rget_text)
    
    return rget_json



def parse_smw_results(rget_json):
    ddod_smw_links = []
    
    if not 'query' in rget_json:          return
    if not 'pages' in rget_json['query']: return
    
    for pageid, page_value in rget_json['query']['pages'].items():
        
        #: Reset vars for next page 
        curr_pageid   = None
        curr_title    = None
        curr_categories = None
        curr_extlinks = None
        
        #: Assign vars for next page 
        for key, value in page_value.items():
            if   key == 'pageid'    : curr_pageid   = value
            elif key == 'title'     : curr_title    = value
            elif key == 'categories': curr_categories = value
            elif key == 'extlinks'  : curr_extlinks = value
            #else: print("==> Unknown key: "+str(key))
                
        #: Only proceed if this page is a Use Case
        if not "Use Case" in str(curr_categories):
            continue

        #: Remove nesting and prefixed from categories
        clean_categories_list = []
        for category in curr_categories:
            #: Append only useful categories
            if 'title' in category and not "Use Case" in category['title']:
                clean_category = category['title']  \
                    .replace("Category:", "")       \
                    .replace("HHS-","")
                clean_categories_list.append(clean_category)
        clean_categories_str = ",".join(clean_categories_list)
                
        if curr_extlinks:
            for extlink_dict in curr_extlinks:
                ddod_smw_links.append(
                    { 'pageid':curr_pageid
                     ,'title':curr_title
                     ,'categories':clean_categories_str
                     ,'extlinks':extlink_dict.get('*',None)
                    })
        else:
            ddod_smw_links.append(
                { 'pageid':curr_pageid
                 ,'title':curr_title
                 ,'categories':clean_categories_str
                 ,'extlinks':None
                })

    return ddod_smw_links



def save_list_to_csv(file_name, list_of_dicts):
    import csv
    with open(file_name, 'w') as outfile:
        fp = csv.DictWriter(outfile, list_of_dicts[0].keys())
        fp.writeheader()
        fp.writerows(list_of_dicts)    
    return
        


def save_list_to_df(list_of_dicts):
    import pandas as pd
    df = pd.DataFrame(data=list_of_dicts)
    
    return df



def save_list_to_db(table_name,list_of_dicts):
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://dportnoy:postgres@localhost:5432/ddod_hdgov')

    df = save_list_to_df(ddod_smw_links)
    df.to_sql(table_name, engine, if_exists='append')
    
    return



def load_data_json(file_name):
    with open (file_name, "r") as myfile:
        data_json=myfile.read()
    return data_json



def count_link_occurrences():
    
    #: Clean up encoding if needed
    if data_json.count("\\/"):
        data_json_clean = data_json.replace("\\/","/")
    else:
        data_json_clean = data_json
        
    for index,row in enumerate(ddod_smw_links):
        url = ddod_smw_links[index]['extlinks'].strip("/")  # Trim trailing slash
        url_count = data_json_clean.count(url)
        ddod_smw_links[index]['in_hdgov'] = url_count


        
def extract_counts_by_agency(ddod_smw_links):
    
    counts_by_agency = {}
    
    for row in ddod_smw_links:
        categories = row['categories']
        in_hdgov   = row['in_hdgov']
        
        if ".com" in row['extlinks'].replace('.', '/.').split('/'):  # Ignore .com TLD
            continue
    
        for category in categories.split(","):
            if not category.count("-") and len(category)>0:     # Agency doesn't have a dash
                agency = category
                
                if not agency in counts_by_agency:
                    counts_by_agency[agency] = {}
                    counts_by_agency[agency]['url_total'   ] = 0
                    counts_by_agency[agency]['url_in_hdgov'] = 0

                counts_by_agency[agency]['url_total'   ] += 1
                counts_by_agency[agency]['url_in_hdgov'] += 1 if in_hdgov > 1 else 0
            
    return counts_by_agency
            
        

rget_json = get_api_result(smw_url)
ddod_smw_links = parse_smw_results(rget_json)

print("Loaded "+ str(len(ddod_smw_links)) +" records")


# save_list_to_csv("ddod_smw_links.csv", ddod_smw_links)
# save_list_to_db("ddod_smw_links", ddod_smw_links)
# df = save_list_to_df(ddod_smw_links)

load_data_json("snapshots/HealthData.gov_2016-06-13_data.json")
count_link_occurrences()
counts_by_agency = extract_counts_by_agency(ddod_smw_links)        
