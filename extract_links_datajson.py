# coding: utf-8
#!/usr/bin/env python
##=============================================================================
##  2016-06-14  Created by David Portnoy
##              Purpose:  Extract links from data.json files
##=============================================================================

from data_json_tools import data_json_tools as tools

import json
import requests
import dateutil.parser as dparser
MAX_DAYS_OLD = 10



SMW_BASE_URL = 'http://ddod.healthdata.gov/'
smw_url  = SMW_BASE_URL + 'api.php?action=query'
smw_url += '&generator=allpages'                 # Generator
smw_url += '&prop=links|extlinks|categories'     # Properties to show
smw_url += '&gaplimit=10000&ellimit=10000&cllimit=10000&pllimit=10000'  # Avoid limits by property type
smw_url += '&format=json&gapfilter=nonredirects&continue='  # Format and paging



PREFIX_URL_LIST = [
      ('open.fda.gov' ,'https://open.fda.gov/data.json')
     ,('data.cdc.gov' ,'https://data.cdc.gov/data.json')
     ,('data.cms.gov' ,'http://data.cms.gov/data.json' )
     ,('dnav.cms.gov' ,'http://dnav.cms.gov/Service/DataNavService.svc/json')
     #,('HealthData.gov','http://healthdata.gov/data.json')
     #,('Data.gov' ,    'http://data.gov/data.json')
     ]


def get_new_file_name(file_name_prefix, file_name_suffix='data.json'):
    
    DELIMITER = "_"
    TARGET_FOLDER = "snapshots"
    
    date_string = datetime.datetime.today().strftime('%Y-%m-%d')
    
    new_file_name =   TARGET_FOLDER    + "/"        \
                    + file_name_prefix + DELIMITER  \
                    + date_string      + DELIMITER  \
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




def save_datajson_to_file(datajson_text, file_path):
    
    with open(file_path, 'wb') as f:
        f.write(datajson_text)

    return True  # Success



def get_datajson_from_file(file_path):
    
    with open(file_path, 'rb') as f:
        datajson_text = f.read()

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

def get_datajson(prefix, url):
    
    file_list = data_json_tools.get_file_list(max_load=1, file_date_pattern=['*']
                , file_name_prefix=prefix
                , file_name_suffix='[_]data.json'
               )
    file_name = file_list[0]  # Latest only
    file_age = get_file_age(file_name)
    datajson_text = ""

    #=== If file is old or nonexistant, attempt to load from web 
    if not file_date or file_age > MAX_DAYS_OLD:

        datajson_text = get_datajson_from_web(url)

        if datajson_text:
            new_file_name = get_new_file_name(prefix)
            save_datajson_to_file(datajson_text, new_file_name)
            return datajson_text  # From web

        
    #=== If no prior file and problem with web 
    if not file_date:
        return False

    #=== Otherwise use a file
    datajson_text = get_datajson_from_file(file_name)
    return datajson_text  # From file
    
        
# Load HD.gov json
hdgov_datajson_text = get_datajson('HealthData.gov','http://healthdata.gov/data.json')


# Load source json files
for (prefix,url) in PREFIX_URL_LIST:
    datajson_text = get_datajson(prefix, url)
    print(len(datajson_text))
    
    ##
    ##  Parse text for list of URLs
    ##
    
    ##
    ##  Look for each URL in target (HD.gov)
    ##
    
    ##
    ##  Document counts
    ##
