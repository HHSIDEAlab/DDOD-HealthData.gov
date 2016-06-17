# coding: utf-8
#!/usr/bin/env python
######################
##  2016-06-13  Created by David Portnoy
######################

import json
import requests
import copy     # To deepcopy dictionary
import datetime


TARGET_FOLDER = "snapshots"
PREFIX        = 'ddod.healthdata.gov'
FILE_NAME_DELIMITER = '_'


SMW_BASE_URL = 'http://ddod.healthdata.gov/'
smw_url  = SMW_BASE_URL + 'api.php?action=query'
smw_url += '&generator=allpages'                 # Generator
smw_url += '&prop=links|extlinks|categories'     # Properties to show
smw_url += '&gaplimit=10000&ellimit=10000&cllimit=10000&pllimit=10000'  # Avoid limits by property type
smw_url += '&format=json&gapfilterredir=nonredirects&continue='  # Format and paging




def save_datajson_to_new_file_name(datajson_text, file_name_prefix, file_name_suffix='data.json'):
    
    date_string = datetime.datetime.today().strftime('%Y-%m-%d')
    
    new_file_name =   TARGET_FOLDER    + "/"                  \
                    + file_name_prefix + FILE_NAME_DELIMITER  \
                    + date_string      + FILE_NAME_DELIMITER  \
                    + file_name_suffix
                
    with open(new_file_name, 'w') as file:
        file.write(datajson_text)

    return new_file_name






def get_api_result(source_url):
    rget = requests.get(source_url)
    rget_text = rget.text
    rget_json = json.loads(rget_text)
    
    return rget_json



def parse_smw_results(rget_json, url_filter=None):
    
    rget_json_use_cases = copy.deepcopy(rget_json)  # Extract just the use case entries for saving
    ddod_smw_links      = []
    
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
            rget_json_use_cases['query']['pages'].pop(pageid,None)  # Remove irrelevant pages to save for later
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
                extlink_dict_str = extlink_dict.get('*','')   # '*' is actualy the key for some reason
                if not extlink_dict_str: continue   # No url to add
                if url_filter and extlink_dict_str.find(url_filter) < 0: continue  # Filter not found
                    
                ddod_smw_links.append(
                    { 'pageid':curr_pageid
                     ,'title':curr_title
                     ,'categories':clean_categories_str
                     ,'extlinks':extlink_dict_str
                    })
        else:
            ddod_smw_links.append(
                { 'pageid':curr_pageid
                 ,'title':curr_title
                 ,'categories':clean_categories_str
                 ,'extlinks':None
                })

    return (ddod_smw_links, rget_json_use_cases)



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

#: Just get the .gov URLs
url_filter_dotgov  = '.gov'
file_prefix_dotgov = PREFIX+"_gov_only_links"
(ddod_smw_links, rget_json_use_cases) = parse_smw_results(rget_json, url_filter_dotgov)

print("Loaded "+ str(len(ddod_smw_links)) +" records")

ddod_smw_links_text = json.dumps(ddod_smw_links)
save_datajson_to_new_file_name(ddod_smw_links_text, file_prefix_dotgov)

# Save generic file with all fields
datajson_text = json.dumps(rget_json_use_cases)
save_datajson_to_new_file_name(datajson_text, PREFIX)


# save_list_to_csv("ddod_smw_links.csv", ddod_smw_links)
# save_list_to_db("ddod_smw_links", ddod_smw_links)
# df = save_list_to_df(ddod_smw_links)

load_data_json("snapshots/HealthData.gov_2016-06-13_data.json")
count_link_occurrences()
counts_by_agency = extract_counts_by_agency(ddod_smw_links)        
