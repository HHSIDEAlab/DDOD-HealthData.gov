# coding: utf-8
#!/usr/bin/env python
######################
##  2016-02-20  Created by David Portnoy
######################

import json_delta
import json
import yaml
import os
import glob      # Wildcard search
import sys       # for stdout
import datetime  # For timestamp


# Globals
debug = False



# Function to save file from web
def download_file(url, file_path):
    
    r = requests.get(url, stream=True)    # NOTE the stream=True parameter
        

    if r.status_code != 200:
        print("Problem with URL: "+url+"   Status code: "+str(r.status_code))
        return 0 # Fail
    else:
        if 'content-length' in r.headers: 
            print("URL: "+url+"   size: "+r.headers['content-length'])

    with open(file_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return 1  # Success




#=== Merges dictionaries, making keys occuring multiple times into lists
def merge_dict(dict_one, dict_two):
    merged_dict = {}
    if not dict_one:  return dict_two
    if not dict_two:  return dict_one

    unique_keys = list(set(list(dict_one.keys()) + list(dict_two.keys())))
    for key in unique_keys:
        if key in dict_one and key in dict_two:  # Make it a list then append
            #: Prevent nested lists
            if type(dict_one[key]) is not list: dict_one[key] = [dict_one[key]]
            if type(dict_two[key]) is not list: dict_two[key] = [dict_two[key]]
            merged_dict[key] = dict_one[key] + dict_two[key]
        else:
            merged_dict[key] = dict_one.get(key, dict_two.get(key, None))  # If not 1st then second
    return merged_dict




# Extract key values, regardless of hierarchy and group multiple key values as lists
def get_key_list(dataset, key_list):
    
    if type(dataset) is list:
        value_list = {}
        for item in dataset:
            value_list_item = get_key_list(item, key_list)
            value_list = merge_dict(value_list,value_list_item)
        return value_list
    
    elif type(dataset) is dict:
        value_list = {}
        for item_key,item_value in dataset.items():

            if item_key in key_list:
                value_list = merge_dict(value_list,{item_key:item_value})
            
            if type(item_value) in [list, dict]:
                value_list_deep = get_key_list(item_value, key_list)
                value_list = merge_dict(value_list,value_list_deep)
                

        return value_list
    else:
        return


    '''#=== Sample usage ===
    debug = False
    key_list = ['c']
    dataset = {'d':5,'a':1,'b':[{'c':7},[{'c':5},22],3],'c':3}
    value_list = get_key_list(dataset, key_list)
    #==> value_list = {'c': [7, 5, 3]}
    '''


def print_same_line(print_string):
    sys.stdout.write("\r" + str(print_string))
    sys.stdout.flush()
    

#: There are multiple versions of the schema
def make_json_data_struct_compatible(json_data_struct):
    if type(json_data_struct) is dict:
        json_data_struct = json_data_struct.get('dataset', None)
    return json_data_struct



def load_file_json(json_file_name):
    with open(json_file_name) as json_file:
        json_data_struct = json.load(json_file)
        json_data_struct = make_json_data_struct_compatible(json_data_struct)
    return json_data_struct



def parse_date(file_name):
    starting_point_of_date = "_20"
    date_pos_start = file_name.find(starting_point_of_date)+1
    return file_name[date_pos_start:date_pos_start+10]




def get_file_list(max_load=None
    , file_date_pattern=''
    , file_name_prefix='HealthData.gov'
    , file_name_suffix='[_]data.json'
    ):

    if not file_date_pattern:
        file_date_pattern='[0-9][0-9][0-9][0-9][-][0-9][0-9][-][0-9][0-9]'

    file_list_all = []

    if type(file_date_pattern) is not list: file_date_pattern = [file_date_pattern]
    for single_file_date_pattern in file_date_pattern:
        file_pattern   = "snapshots/"
        file_pattern  += file_name_prefix + single_file_date_pattern + file_name_suffix
        file_list_all += glob.glob(file_pattern)

    file_list_all = sorted(file_list_all, reverse=True)
    list_size     = len(file_list_all) if not max_load else max_load
    file_list     = file_list_all[:list_size]

    return file_list





def support_old_schema(dataset_list):
    if isinstance(dataset_list, dict):
        return dataset_list["dataset"]
    elif isinstance(dataset_list, list):
        return dataset_list
    else:
        return None




    

def load_file_list(file_list):
    json_data_list = []
    for index in range(len(file_list)):
        json_data_list.append(load_file_json(file_list[index]))
    return json_data_list




# recursively sort any lists it finds (and convert dictionaries
# to lists of (key, value) pairs so that they're orderable):
def ordered_json(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered_json(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered_json(x) for x in obj)
    else:
        return obj





def load_agency_lookup():

    with open('agency_lookup_columns.json') as data_file:    
        agency_lookup_columns = json.load(data_file)

    bureau_code_index = agency_lookup_columns['columns'].index('bureau_code')
    agency_abbrev_index = agency_lookup_columns['columns'].index('agency_abbrev')
 
    agency_lookup = {}
   
    for agency_record in agency_lookup_columns['data']:
        # TBD: May want to convert unicode using  .encode('ascii','ignore')
        
        agency_lookup[agency_record[bureau_code_index]] = str(agency_record[agency_abbrev_index])


    return agency_lookup





def get_agency_abbrev_list(agency_lookup):

    # Looks more complex than needed, but due to sorting by key
    bureau_code_list = []

    for bureau_code in agency_lookup.keys():
        bureau_code_list.append(bureau_code) 
    bureau_code_list.sort()

    agency_abbrev_list = []
    for bureau_code in bureau_code_list:
        agency_abbrev_list.append(agency_lookup[bureau_code])
 
    return agency_abbrev_list





def get_agency_abbrev(key_item,agency_lookup):

    agencies = key_item["bureauCode"]


    # Just in case it's not a list, make it one
    agencies = agencies if isinstance(agencies,list) else [agencies]

    for agency in agencies:
        #agency = agency.encode('ascii','ignore')
        agency_abbrev = agency_lookup.get(agency,"Other")
        
        # Occassionally "bureauCode"][0] == "009:00" is used for State/Local
        if agency == "009:00":
            
            publisher_name = key_item["publisher"]
            # Handle when publisher is not a dictionary
            if isinstance(publisher_name, dict): publisher_name = str(publisher_name)
           
            if "State of" in publisher_name:
                agency_abbrev = "State"
            elif "City of" in publisher_name:
                agency_abbrev = "City"

        agency_counts[agency_abbrev] = agency_counts.get(agency_abbrev, 0) + 1
       
            
    return agency_abbrev
        

    
