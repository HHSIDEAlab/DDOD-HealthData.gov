# coding: utf-8
#!/usr/bin/env python
# %%writefile data_json_links.py
######################
##  2016-02-20  Created by David Portnoy
######################


from data_json_tools import data_json_tools as tools
import pandas as pd
from datetime import datetime



global url_df
global catalog_date_urls





def get_dataset_urls(dataset):

    dataset_urls = []
    
    for distrib in dataset.get('distribution',[]):
        if 'downloadURL' in distrib:
            dataset_urls.append(distrib['downloadURL'])
            
    if len(dataset_urls) == 0:
        dataset_urls = ['Missing']
            
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





def build_catalog_urls_list(file_list):
    
    agency_lookup = tools.load_agency_lookup()

    global url_df
    url_df = pd.DataFrame(columns=['date', 'id', 'agency', 'url', 'url_index', 'url_status'])
    row_index = 0

    
    global catalog_date_urls
    catalog_date_urls = {}

    
    for file_name in file_list:
        
        json_catalog = tools.load_file_json(file_name)

        catalog_urls = get_catalog_urls(json_catalog, agency_lookup)
        
        file_date_str = tools.parse_date(file_name)
        file_date     = datetime.strptime(file_date_str,'%Y-%m-%d')
        
        catalog_date_urls[file_date_str] = catalog_urls   # Append file just processed
        
        
        for dataset_urls in catalog_urls:
            for url_index,dataset_url in enumerate(dataset_urls['url']):
                
                url_df.loc[row_index] = [  file_date
                                         , dataset_urls['id']
                                         , dataset_urls['agency']
                                         , dataset_url
                                         , url_index
                                         , '' # 'url_status'
                                        ]
                row_index += 1
            
    
    




# Returns result from most recent dates
def main(max_load=1, file_date_pattern=''):
    
    
    file_list  = tools.get_file_list(max_load, file_date_pattern)
    
    build_catalog_urls_list(file_list)


    
# Example
# main(max_load=1, file_date_pattern=['201[0-9]-[0-1][1-9]-01'])  # 1st date of every month
