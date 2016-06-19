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
     ,('ddod.healthdata.gov_gov_only_links',ERROR_URL)  # Rather than using smw_url, it should fail, so that the file from parse_ddod_smw_content is used
     ,('federated_sources',ERROR_URL) 
     #,('HealthData.gov','http://healthdata.gov/data.json')
     #,('Data.gov' ,    'http://data.gov/data.json')
     ]


# For parsing URLs
REXEX_URL  = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil)/)"""
REXEX_URL += r"""(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))"""
REXEX_URL += r"""+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])"""
REXEX_URL += r"""|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil)\b/?(?!@)))"""



# Links table generated 6/17/2016
links_table = [   
    # ("Source", "Value", "Target")
    ("Harvested Sources", 558, "dnav.cms.gov"),
    ("Harvested Sources", 951, "data.cms.gov"),
    ("Harvested Sources", 1451, "data.cdc.gov"),
    ("Harvested Sources", 139, "open.fda.gov"),
    ("ddod.healthdata.gov", 18, "Healthdata.gov"),
    ("dnav.cms.gov", 151, "Healthdata.gov"),
    ("data.cms.gov", 2, "Healthdata.gov"),
    ("data.cdc.gov", 1100, "Healthdata.gov"),
    ("open.fda.gov", 84, "Healthdata.gov"),
    ("Other Sources", 1855, "Healthdata.gov"),
    ("ddod.healthdata.gov", 144, "Inaccessible"),
    ("dnav.cms.gov", 407, "Inaccessible"),
    ("data.cms.gov", 949, "Inaccessible"),
    ("data.cdc.gov", 351, "Inaccessible"),
    ("open.fda.gov", 55, "Inaccessible"),
    ("ddod.healthdata.gov", 0, "Ignored"),
    ("dnav.cms.gov", 4, "Ignored"),
    ("data.cms.gov", 5, "Ignored"),
    ("data.cdc.gov", 6, "Ignored"),
    ("open.fda.gov", 1, "Ignored"),
    ("Healthdata.gov", 8, "Ignored")
     ]




def convert_links_table_to_stankey_dict(links_table):
    node_dict  = {}
    node_list  = []
    links_list = []
    dataset    = {}

    source_node_list = [row[0] for row in links_table]
    target_node_list = [row[2] for row in links_table]
    unique_node_set  = set(source_node_list + target_node_list)

    for (node_id, node_name) in enumerate(unique_node_set):
        node_dict[node_name] = node_id
        node_list.append({
                 'id'  : node_id
                ,'name': node_name
            })

    for (node_id, node_name) in enumerate(unique_node_set):
        node_dict[node_id] = node_name
        node_list.append({
                 'id'  : node_id
                ,'name': node_name
            })

    for (source_name, value, target_name) in links_table:
        links_list.append({
                 "source": node_dict[source_name]
                ,"target": node_dict[target_name]
                ,"value" : value           
            })        

    dataset['nodes'] = node_list
    dataset['links'] = links_list
    
    return dataset

    




def extract_clean_url_list(target_str):
    
    url_list = re.findall(REXEX_URL, target_str)
    url_list_clean = []
    
    for url in url_list:
        url = url.lower()
        
        # Fixes common problems
        url = url.split('\\')[0]  # Remove backslach
        url = url.strip('.')  # Trim trailing period
        url = url.strip('/')  # Trim trailing slash
        # Split on string
        # Split on space
        
        # TODO: Decide whether to remove http/https prefix
        
        if url not in url_list_clean:
            url_list_clean.append(url)
    
    return url_list_clean




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
            url_list = extract_clean_url_list(target_str)
            
            #if len(url_list) > 1 or (" " in target_str): print("INTERESTING TEXT ==> "+target_str)
            
            for url in url_list:
                if url in ignore_url_str:
                    url_harvest_counts[source_name]["Ignored"][url]    = url_harvest_counts[source_name]["Ignored"].get(url,0) + 1
                    url_ignored[url]              = url_ignored.get(url,{})
                    url_ignored[url][source_name] = url_ignored[url].get(source_name,0) +1
                    continue
                
                url_counts[url]              = url_counts.get(url,{})
                url_counts[url][source_name] = url_counts[url].get(source_name,0) +1

                if url in dest_str:
                    url_harvest_counts[source_name]["Found"][url]    = url_harvest_counts[source_name]["Found"].get(url,0) + 1
                    #print(url + " found")
                else:
                    url_harvest_counts[source_name]["NotFound"][url] = url_harvest_counts[source_name]["NotFound"].get(url,0) + 1
                    #print(url + " not found")
            
    else:
        return
    




def clean_up_datajson(dirty_obj, output=None):
    
    dirty_obj_type = 'dict' if type(dirty_obj) is dict else 'str'

    #: First convert to string to manipulate
    if dirty_obj_type == 'dict':
        dirty_obj_str = json.dumps(dirty_obj)
    else:
        dirty_obj_str = str(dirty_obj) 

    
    working_str = dirty_obj_str
    working_str = working_str.replace("\\/","/")
    working_str = working_str.lower()

    
    #: If different output type not specified, keep it same
    if not output:
        output = dirty_obj_type
        
    if output == 'dict':
        return json.loads(working_str)
    else:
        return working_str
    





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
        datajson_load = json.load(file)
        
    #: Make sure it's a dictionary
    datajson_dict = {}
    datajson_dict[file_path] = datajson_load

    return datajson_dict  # Success




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
            datajson_text = clean_up_datajson(datajson_text)
            new_file_name = save_datajson_to_new_file_name(datajson_text, prefix)
            datajson_loads = json.loads(datajson_text)
                
            # Ensure this is a dict
            datajson_dict = {}
            new_file_name[new_file_name] = datajson_loads
            
            return datajson_dict  # From web

        
    #=== If no prior file and problem with web 
    if not file_name:
        return False

    #=== Otherwise use a file
    datajson_dict = get_datajson_from_file(file_name)  # Guarantees dict
    datajson_dict = clean_up_datajson(datajson_dict)
    
    return datajson_dict  # From file
    


    
    
# Load HD.gov json
hdgov_datajson_dict = get_datajson_dict('HealthData.gov','http://healthdata.gov/data.json')
hdgov_datajson_str  = clean_up_datajson(hdgov_datajson_dict, output='str')




#: Set one time values
url_harvest_counts  = {}
url_harvest_counts  = {}
dest_str    = hdgov_datajson_str


ignore_url_json = get_datajson_from_file(IGNORE_URL_FILE_NAME)
ignore_url_str  = clean_up_datajson(ignore_url_json, output='str')


aggregate_source_dict = {}
url_counts  = {}
url_ignored = {}


#: Loop through sources
# Load source json files
for (prefix,url) in PREFIX_URL_LIST:
    datajson_dict = get_datajson_dict(prefix, url)
    
    source_name = prefix
    url_harvest_counts[source_name] = {}
    url_harvest_counts[source_name]['Found']    = {}
    url_harvest_counts[source_name]['NotFound'] = {}
    url_harvest_counts[source_name]['Ignored']  = {}
    
    parse_json(prefix, datajson_dict, dest_str)
    
    if not aggregate_source_dict:
        aggregate_source_dict = dict(datajson_dict)   # 1st value
    else:
        aggregate_source_dict = aggregate_source_dict.update(datajson_dict)
    

#=== Save federated sources to file for future use
aggregate_source_str = json.dumps(aggregate_source_str)
aggregate_source_str = clean_up_datajson(aggregate_source_str)

aggregate_source_file_name_prefix = 'federated_sources'
source_name = aggregate_source_file_name_prefix
save_datajson_to_new_file_name(
      aggregate_source_str
    , aggregate_source_file_name_prefix
    , file_name_suffix='data.json'
    )
parse_json(source_name, aggregate_source_dict, dest_str)
    


#=== Format results 
url_results = []
for key, value in url_harvest_counts.items():
    data_source    = key
    search_results = value
    num_found     = len(search_results['Found'])
    num_not_found = len(search_results['NotFound'])
    num_ignored   = len(search_results['Ignored'])
    url_results.append({ "Data_Source": data_source
                        ,"Total"      : num_found + num_not_found
                        ,"Found"      : num_found
                        ,"Not_Found"  : num_not_found
                        ,"Ignored"    : num_ignored
                       })

url_results_columns = ['Data_Source', 'Total',  'Found',  'Not_Found',  'Ignored']
df_url_harvest_counts = pd.DataFrame(data=url_results, columns=url_results_columns)
print(df_url_harvest_counts)
df_url_harvest_counts.to_csv('url_harvest_counts.csv', sep='\t')




#=== Obtain counts unique to target catalog
aggregate_source_file_name_prefix = 'healthdata.gov_only'
source_name                       = aggregate_source_file_name_prefix

url_harvest_counts[source_name] = {}
url_harvest_counts[source_name]['Found']    = {}
url_harvest_counts[source_name]['NotFound'] = {}
url_harvest_counts[source_name]['Ignored']  = {}
parse_json(
      aggregate_source_file_name_prefix
    , hdgov_datajson_dict
    , aggregate_source_str
    )

data_source    = 'healthdata.gov_only'
search_results = url_harvest_counts[data_source]
num_found     = len(search_results['Found'])
num_not_found = len(search_results['NotFound'])
num_ignored   = len(search_results['Ignored'])
num_total     = num_found + num_not_found # + num_ignored
url_results.append({ "Data_Source": data_source
                    ,"Total"      : num_found + num_not_found
                    ,"Found"      : num_found
                    ,"Not_Found"  : num_not_found
                    ,"Ignored"    : num_ignored
                   })
'''





data_dest      = 'HealthData.gov'
data_source    = 'federated_sources'
search_results = url_harvest_counts[data_source]
num_found     = len(search_results['Found'])
num_not_found = len(search_results['NotFound'])
num_ignored   = len(search_results['Ignored'])
num_total     = num_found + num_not_found # + num_ignored

'''
print("\n\n" + str(num_not_found)  + " of the " + str(num_total) + " dataset links in " + data_dest + " are not found on upstream sources")
'''
Example:
    {'Data_Source': 'healthdata.gov_only',
      'Found': 1350,
      'Ignored': 8,
      'Not_Found': 1858,
      'Total': 3208}

==> 3208 total items in HD.gov.  Of these 1350 are in federated sources.  The rest 1858 are unique to HD.gov
'''





#=== Save dataframes for analytics

df_url_counts = pd.DataFrame(data=url_counts).T.fillna(0)
df_url_counts.index.name = 'url'
df_url_counts.to_csv('url_counts_by_source.csv', sep='\t', encoding='utf-8')
#print(df_url_counts)


df_url_ignored = pd.DataFrame(data=url_ignored).T.fillna(0)
df_url_counts.index.name = 'url'
df_url_ignored.to_csv('url_ignored_by_source.csv', sep='\t')
#print(df_url_ignored)


dataset = convert_links_table_to_stankey_dict(links_table)

