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




def get_file_list(max_load=None, file_date_pattern=''):

    if not file_date_pattern:
        file_date_pattern='[0-9][0-9][0-9][0-9][-][0-9][0-9][-][0-9][0-9]' 

    file_pattern = "snapshots/"
    file_pattern += "HealthData.gov[_]"+ file_date_pattern +"[_]data.json"
    file_list_all = sorted(glob.glob(file_pattern), reverse=True)
    list_size = len(file_list_all) if not max_load else max_load
    file_list = file_list_all[:list_size]
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
        

    
