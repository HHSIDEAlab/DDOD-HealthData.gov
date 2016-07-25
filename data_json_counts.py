#!/usr/bin/env python
# -*- coding: utf-8 -*-
######################
##  2016-02-20  Created by David Portnoy
######################

import os
import glob   # Wildcard search
import json
import os
import csv




def support_old_schema(dataset_list):
    if isinstance(dataset_list, dict):
        return dataset_list["dataset"]
    elif isinstance(dataset_list, list):
        return dataset_list
    else:
        return None

    
    
    


# Pull out the most important elements to tally on
def get_keys(dataset):
    keys = ["bureauCode", "programCode", "publisher", 
            "landingPage","modified",
            "Identifier", "downloadURL"]
    '''
    Characteristics of non-federal entries for DKAN
    → Publisher:Name is "State of" or "City of"
    → downloadURL has non-hhs domain
    → Identifier has non-hhs domain
    → Usually "bureauCode": ["009:00"  and "programCode": [ "009:000"
    '''
    key_values = []
    for i,key in enumerate(keys):
        if key in dataset:
            key_values.append(dataset[key])
        else:
            key_values.append(None)
    return dict(zip(keys, key_values))




# FIXME: Code not yet finished
# FIXME: Should call get_keys
# Create a dictionary of values for comparison

def get_key_list(dataset_list):
    key_list = []
    for index, dataset in enumerate(dataset_list):
        key_list.append(get_keys(dataset))
    #for # List of unique bureauCode values    
    
    totals = len(dataset_list)
    return key_list





def parse_date(file_name):
    starting_point_of_date = "_20"
    date_pos_start = file_name.find(starting_point_of_date)+1
    return file_name[date_pos_start:date_pos_start+10]

    

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



#: Convert to ordered list
def convert_dict_to_list(dict_counts_by_date,agency_lookup):
    

    # --- Be sure list of abbreviations is sorted by key ---
    agency_abbrev_list = get_agency_abbrev_list(agency_lookup)

    
    row_csv = []
    row_csv_list = []
    
    # --- Build header ---
    row_csv.append("Date")
    for agency_abbrev in agency_abbrev_list:
        row_csv.append(agency_abbrev)
    row_csv_list.append(row_csv)

    
    # --- Build row list in order ---
    for row_date,row_counts in dict_counts_by_date.items():
        row_csv = []
        row_csv.append(row_date)

        # Using this method because want to be sorted by bureau_code
        for agency_abbrev in agency_abbrev_list:
            row_csv.append(str(row_counts.get(agency_abbrev,0)))

        row_csv_list.append(row_csv)

    return row_csv_list


        
      




def save_list_to_csv(csv_data):

    print("Saving to CSV file")


    with open(CSV_FILE_NAME, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(csv_data)

    # Keep track of last update
    mtime = os.path.getmtime(CSV_FILE_NAME)
    
    return 

        
        
        
def get_agency_counts(key_list,agency_lookup):
    agency_counts = {}
    for index,key_item in enumerate(key_list):

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
           
        #if 0 < index < MAX_LOOP: break  # Don't run all for debugging

            
    return agency_counts
        
        

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




def get_file_name_list():
    file_pattern = "snapshots/"
    file_pattern += "HealthData.gov[_][0-9][0-9][0-9][0-9][-][0-9][0-9][-][0-9][0-9][_]data.json"
    file_name_list = glob.glob(file_pattern)
    
    return sorted(file_name_list)




def get_csv_date_list(csv_data):

    
    csv_date_list = []
    header = csv_data[0]
    date_pos = header.index('Date')
    
    for index, row in enumerate(csv_data[1:]):
        csv_date_list.append(row[date_pos])
    
    return csv_date_list


'''
------------------------------------------------
---  Reload the file only if it changed
------------------------------------------------
'''
def get_csv_data(csv_data = []):

    #: Remember values from last run
    global mtime
    try:
        mtime
    except NameError:
        mtime = 0


    #: Don't do anything, if no file to load
    if not os.path.exists(CSV_FILE_NAME) or os.path.getsize(CSV_FILE_NAME) == 0:
        return csv_data

        
    last_mtime = mtime
    mtime = os.path.getmtime(CSV_FILE_NAME)

    #: Reload if there's a newer file
    if mtime > last_mtime or len(csv_data)==0:
        print("Loading from CSV file")
        last_mtime = mtime

        csv_file = open(CSV_FILE_NAME)
        csv_reader = csv.reader(csv_file)

        csv_data = []
        for index, row in enumerate(csv_reader):
            csv_data.append(row)
            if 0 < index < MAX_LOOP: break  # Don't run all for debugging


    #: Sorted dates needed by some charting libraries
    csv_data = csv_data[0:1]+sorted(csv_data[1:])
    return csv_data




def load_file(file_name):
    with open(file_name) as json_file:
        json_data = json.load(json_file)
        return json_data




def get_missing_csv_data(csv_data,agency_lookup):

    dict_counts_by_date = {}


    if len(csv_data) > 0:
        csv_date_list = get_csv_date_list(csv_data)
    else:
        csv_date_list = []

    file_name_list = get_file_name_list()

    #: Load missing dates
    for index, file_name in enumerate(reversed(file_name_list)):
        snapshot_file_date = parse_date(file_name)

        if snapshot_file_date not in csv_date_list:
            print("Loading missing date: "+file_name)

            dataset_list = load_file(file_name)
            dataset_list = support_old_schema(dataset_list)

            key_list = get_key_list(dataset_list)
            agency_counts = get_agency_counts(key_list,agency_lookup)

            dict_counts_by_date[snapshot_file_date]=agency_counts

            if 0 < index < MAX_LOOP: break  # Don't run all for debugging

            
    if len(dict_counts_by_date) > 0:
        missing_csv_data = convert_dict_to_list(dict_counts_by_date,agency_lookup)
    else:
        missing_csv_data = []
            
    return missing_csv_data



        

def get_dict_counts_by_date(file_name_list,csv_date_list,agency_lookup):

    dict_counts_by_date = {}

    #: Load missing dates
    for index, file_name in enumerate(reversed(file_name_list)):
        snapshot_file_date = parse_date(file_name)

        if snapshot_file_date not in csv_date_list:
            print("Loading missing date: "+file_name)

            dataset_list = load_file(file_name)
            dataset_list = support_old_schema(dataset_list)

            key_list = get_key_list(dataset_list)
            agency_counts = get_agency_counts(key_list,agency_lookup)

            dict_counts_by_date[snapshot_file_date]=agency_counts

            #if index > 15: break  # Don't run all for debugging
            
    return dict_counts_by_date




def update_csv_from_snapshots():
    '''
    ------------------------------------------------
    ---  Load only dates missing                    
    ------------------------------------------------
    '''
    global MAX_LOOP
    MAX_LOOP = 0   # Don't limit loops for debug

    global CSV_FILE_NAME
    CSV_FILE_NAME = "generated/totals_by_agency.csv"

    #: Remember values from last run
    global csv_data
    try:
        csv_data
    except NameError:
        csv_data = []


    agency_lookup = load_agency_lookup()
    csv_data = get_csv_data(csv_data)
    csv_data_saved = csv_data

    missing_csv_data = get_missing_csv_data(csv_data,agency_lookup)


    
    if len(missing_csv_data) > 0:  # Indicates added missing data
        if mtime == 0:   # Indicates no prior CSV data
            #: Header + sorted dataset without header
            csv_data = missing_csv_data[0:1]+sorted(missing_csv_data[1:])
        else:
            #: Header + concatenated datasets without header

            csv_data = csv_data[0:1]+sorted(csv_data[1:]+missing_csv_data[1:])


    # Save only if data changed
    if csv_data_saved != csv_data:
        save_list_to_csv(csv_data)

    return csv_data

    
 

 def build_diff_report_urls(csv_from_snapshots):
    # example: http://peach.ddod.us/ddod_charts/difference_reports/dataset_diff_2016-06-19_2016-06-20.yaml

    DIFF_REPORT_BASE = 'http://peach.ddod.us/ddod_charts/'  # Absolute URL
    DIFF_REPORT_BASE = ''  # Relative URL
    DIFF_REPORT_FOLDER = 'difference_reports/'
    DIFF_REPORT_PREFIX = 'dataset_diff_'
    DIFF_REPORT_SEPARATOR = '_'
    DIFF_REPORT_EXTENSION = '.yaml'


    snapshot_dates = []
    for row in csv_data[1:]:
        snapshot_dates.append(row[0])
        #print(row[0])

    diff_report_urls = []    
    for i in range(len(snapshot_dates)-1):
        diff_date_before = snapshot_dates[i]
        diff_date_after  = snapshot_dates[i+1]
        diff_report_url = DIFF_REPORT_BASE        \
                        + DIFF_REPORT_FOLDER      \
                        + DIFF_REPORT_PREFIX      \
                        + diff_date_before        \
                        + DIFF_REPORT_SEPARATOR   \
                        + diff_date_after         \
                        + DIFF_REPORT_EXTENSION

        diff_report_urls.append(diff_report_url)
        
    return diff_report_urls
   
    
