# coding: utf-8
#!/usr/bin/env python
##=============================================================================
##  2016-06-14  Created by David Portnoy
##              Purpose:  Extract links from data.json files
##=============================================================================

from data_json_tools import data_json_tools

import json
import requests
import dateutil.parser as dparser
import pandas as pd
import re    # For parsing URLs
import datetime


MAX_DAYS_OLD = 0
FILE_NAME_DELIMITER = '_'
TARGET_FOLDER = "snapshots"
IGNORE_URL_FILE_NAME = 'ignore_urls.json'



SMW_BASE_URL = 'http://ddod.healthdata.gov/'
smw_url  = SMW_BASE_URL + 'api.php?action=query'
smw_url += '&generator=allpages'                 # Generator
smw_url += '&prop=links|extlinks|categories'     # Properties to show
smw_url += '&gaplimit=10000&ellimit=10000&cllimit=10000&pllimit=10000'  # Avoid limits by property type
smw_url += '&format=json&gapfilterredir=nonredirects&continue='  # Format and paging

ERROR_URL = 'http://httpbin.org/status/404'

PREFIX_URL_LIST = [
      ('open.fda.gov' ,'https://open.fda.gov/data.json')
     ,('data.cdc.gov' ,'https://data.cdc.gov/data.json')
     ,('data.cms.gov' ,'http://data.cms.gov/data.json' )
     ,('dnav.cms.gov' ,'http://dnav.cms.gov/Service/DataNavService.svc/json')
     ,('ddod.healthdata.gov',ERROR_URL)  # Rather than using smw_url, it should fail, so that the file from parse_ddod_smw_content is used
     ,('HealthData.gov','http://healthdata.gov/data.json')
     #,('Data.gov' ,    'http://data.gov/data.json')
     ]


# For parsing URLs
REXEX_URL  = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil)/)"""
REXEX_URL += r"""(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))"""
REXEX_URL += r"""+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])"""
REXEX_URL += r"""|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil)\b/?(?!@)))"""



#=== Recursively parse through data.json looking for URLs
def parse_json(source_name, source_obj, dest_str):
    
    if isinstance(source_obj, dict):
        for key, value in source_obj.items():
            parse_json(source_name, value, dest_str)
    
    if isinstance(source_obj, list):
        for value in source_obj:
            parse_json(source_name, value, dest_str)
    
    #: Strings may contain one or more URLs
    if isinstance(source_obj, str):
        target_str = source_obj.lower()
        if "http" in target_str:
            
            #: Sometimes there are multiple URLs in the text
            url_list = re.findall(REXEX_URL, target_str)
            
            #if len(url_list) > 1 or (" " in target_str): print("INTERESTING TEXT ==> "+target_str)
            
            for url in url_list:
                if url in ignore_url_str:
                    url_counts[source_name]["Ignored"][url]    = url_counts[source_name]["Ignored"].get(url,0) + 1
                    continue
                    
                if url in dest_str:
                    url_counts[source_name]["Found"][url]    = url_counts[source_name]["Found"].get(url,0) + 1
                    #print(url + " found")
                else:
                    url_counts[source_name]["NotFound"][url] = url_counts[source_name]["NotFound"].get(url,0) + 1
                    #print(url + " not found")
            
    else:
        return
    




def clean_up_dict(dirty_dict):

    working_str = json.dumps(dirty_dict)
    working_str = working_str.replace("\\/","/")
    working_str = working_str.lower()
    
    clean_dict = json.loads(working_str)
    return clean_dict




def get_new_file_name(file_name_prefix, file_name_suffix='data.json'):
    
    
    date_string = datetime.datetime.today().strftime('%Y-%m-%d')
    
    new_file_name =   TARGET_FOLDER    + "/"                  \
                    + file_name_prefix + FILE_NAME_DELIMITER  \
                    + date_string      + FILE_NAME_DELIMITER  \
                    + file_name_suffix
                
    return new_file_name





def get_datajson_from_web(url):
    
    r = requests.get(url)
        

    if r.status_code != 200:
        print("Problem with URL: "+url+"   Status code: "+str(r.status_code))
        return False # Fail
    else:
        if 'content-length' in r.headers: 
            print("URL: "+url+"   size: "+r.headers['content-length'])

    return r.text




def save_datajson_to_new_file_name(datajson_text, file_name_prefix, file_name_suffix='data.json'):
    
    date_string = datetime.datetime.today().strftime('%Y-%m-%d')
    
    new_file_name =   TARGET_FOLDER    + "/"                  \
                    + file_name_prefix + FILE_NAME_DELIMITER  \
                    + date_string      + FILE_NAME_DELIMITER  \
                    + file_name_suffix
                
    with open(new_file_name, 'w') as file:
        file.write(datajson_text)

    return new_file_name



def get_datajson_from_file(file_path):
    
    with open(file_path,encoding="ISO-8859-1") as file:
        datajson_text = json.load(file)

    return datajson_text  # Success




def get_file_age(file_name):

    try:
        file_date = dparser.parse(file_name,fuzzy=True)
        file_age  = (datetime.datetime.today() - file_date).days
        return file_age

    except ValueError:
        #raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return False



#: Determine whether to load from web or file

def get_datajson_dict(prefix, url):
    
    file_list = data_json_tools.get_file_list(
                  max_load          = 1
                , file_date_pattern = ''     # Use default date pattern
                , file_name_prefix  = prefix + '['+ FILE_NAME_DELIMITER +']'
                , file_name_suffix  =          '['+ FILE_NAME_DELIMITER + ']'+ '*.json'
               )
    if file_list:
        file_name = file_list[0]  # Latest only
        file_age = get_file_age(file_name)
        print("Most recent file: " + file_name)
    else:
        file_name = False
        file_age  = False
        print("Not found:" + prefix)

    #=== If file is old or nonexistant, attempt to load from web 
    if not file_name or file_age > MAX_DAYS_OLD:

        datajson_text = get_datajson_from_web(url)

        if datajson_text:
            new_file_name = save_datajson_to_new_file_name(datajson_text, prefix)
            datajson_dict = json.loads(datajson_text)
            return datajson_dict  # From web

        
    #=== If no prior file and problem with web 
    if not file_name:
        return False

    #=== Otherwise use a file
    datajson_dict = get_datajson_from_file(file_name)
    return datajson_dict  # From file
    

    
    
    
# Load HD.gov json
hdgov_datajson_dict = get_datajson_dict('HealthData.gov','http://healthdata.gov/data.json')
hdgov_datajson_dict = clean_up_dict(hdgov_datajson_dict)



#: Set one time values
url_counts = {}
dest_str    = json.dumps(hdgov_datajson_dict)

ignore_url_json = get_datajson_from_file(IGNORE_URL_FILE_NAME)
ignore_url_str  = json.dumps(ignore_url_json)


#: Loop through sources
# Load source json files
for (prefix,url) in PREFIX_URL_LIST:
    datajson_dict = get_datajson_dict(prefix, url)
    
    source_name = prefix
    url_counts[source_name] = {}
    url_counts[source_name]['Found']    = {}
    url_counts[source_name]['NotFound'] = {}
    url_counts[source_name]['Ignored']  = {}
    parse_json(prefix, datajson_dict, dest_str)
    


#=== Format results 
url_results = []
for key, value in url_counts.items():
    data_source    = key
    search_results = value
    num_found     = len(search_results['Found'])
    num_not_found = len(search_results['NotFound'])
    num_ignored   = len(search_results['Ignored'])
    url_results.append({ "Data Source": data_source
                        ,"Found"      : num_found
                        ,"Not Found"  : num_not_found
                        ,"Ignored"    : num_ignored
                       })
    
df = pd.DataFrame(data=url_results)
print(df)