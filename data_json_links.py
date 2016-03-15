#!/usr/bin/env python
# %%writefile data_json_links.py
######################
##  2016-02-20  Created by David Portnoy
######################


from data_json_tools import data_json_tools as tools
import pandas as pd
from datetime import datetime



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
    #print get_keys(dataset[0])
    return key_list




def get_dataset_urls(dataset):

    dataset_urls = []
    
    for distrib in dataset.get('distribution',[]):
        if 'downloadURL' in distrib:
            dataset_urls.append(distrib['downloadURL'])
            
    return dataset_urls




def get_dataset_url_dict(dataset, agency_lookup={}, index=0):
    
    if agency_lookup == {}: agency_lookup = tools.load_agency_lookup()

    dataset_id           = dataset.get('identifier','(Missing_identifier_'+str(index)+')')
    
    dataset_urls        = get_dataset_urls(dataset)
    
    dataset_bureau_code = dataset.get('bureauCode','[Other]')[0]  # Take only 1st element of bureau_code list 
    dataset_agency      = agency_lookup.get(dataset_bureau_code,'Other')


    
    dataset_url_dict = {}
    dataset_url_dict['id'       ] = dataset_id
    dataset_url_dict['agency'   ] = dataset_agency
    dataset_url_dict['url'      ] = dataset_urls
    
    return dataset_url_dict




def get_catalog_urls(json_catalog, agency_lookup ={} ):
    
    if agency_lookup == {}: agency_lookup = tools.load_agency_lookup()

    catalog_urls = []
    
    
    for index,dataset in enumerate(json_catalog):
        
        dataset_url_dict = get_dataset_url_dict(dataset, agency_lookup, index)
        
        catalog_urls.append(dataset_url_dict)
        
    return catalog_urls





def get_url_counts(dataset_list):
    
    url_counts = {}
    url_counts['Missing'] = 0
    
    for index,dataset in enumerate(dataset_list):

        #if index > 10: break  # Don't run all for debugging
            
        if not (u'distribution' in dataset): 
            url_counts['Missing'] = url_counts.get('Missing', 0) + 1
            continue  # Nothing to search

        for distrib in dataset[u'distribution']:

            url = distrib.get('downloadURL','Missing')

            url_counts[url] = url_counts.get(url, 0) + 1

            
    return url_counts



def get_dict_counts_by_date(file_name_list,csv_date_list,agency_lookup={}):

    dict_counts_by_date = {}

    #: Load missing dates
    for index, file_name in enumerate(reversed(file_name_list)):
        snapshot_file_date = parse_date(file_name)

        if snapshot_file_date not in csv_date_list:
            print("Loading missing date: "+file_name)

            dataset_list = load_file(file_name)
            dataset_list = support_old_schema(dataset_list)

            key_list = get_key_list(dataset_list)
            
            #agency_counts = get_agency_counts(key_list,agency_lookup)
            #dict_counts_by_date[snapshot_file_date]=agency_counts

            url_counts = get_url_counts(dataset_list)
            print("Saving URL counts: "+str(url_counts)+" for "+"snapshot_file_date")
            dict_counts_by_date[snapshot_file_date]=url_counts


            if index > 15: break  # Don't run all for debugging
            
    return dict_counts_by_date




def build_catalog_urls_list(file_list):
    
    agency_lookup = tools.load_agency_lookup()

    global url_df
    url_df = pd.DataFrame(columns=['date', 'id', 'agency', 'url', 'url_index', 'url_status'])
    row_index = 0

    
    for file_num,file_name in enumerate(file_list):
        
        json_catalog = tools.load_file_json(file_name)

        catalog_urls = get_catalog_urls(json_catalog, agency_lookup)
        
        date_str = tools.parse_date('HealthData.gov_2020-01-04_data.json')
        
        for dataset_urls in catalog_urls:
            for url_index,dataset_url in enumerate(dataset_urls['url']):
                
                url_df.loc[row_index] = [  datetime.strptime(date_str,'%Y-%m-%d') #  'date'
                                         , dataset_urls['id']
                                         , dataset_urls['agency']
                                         , dataset_url
                                         , url_index
                                         , '' # 'url_status'
                                        ]
                row_index += 1
            
    
    




# Returns result from most recent dates
def main(max_load=1):
    
    file_list         = tools.get_file_list(max_load)
    
    build_catalog_urls_list(file_list)

    