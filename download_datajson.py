#!/usr/bin/env python
'''
Downloads all historical data.json catalog files from a specified root URL
'''
__author__ = "David Portnoy"


import requests
from bs4 import BeautifulSoup
import json
import json_delta
import random
import time


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




# Function to help find relevant links 
import datetime
def valid_date(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        # raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        return False

print valid_date("20151212")



# find list of files

directory_url = 'http://data-staging.civicagency.org/archive/datajson'
suffix_url    = '49021.json'
target_folder = 'snapshots'
datajson_url_list = []
read_limit = 0


directory_response = requests.get(directory_url)
directory_soup = BeautifulSoup(directory_response.text)


for a_tag in directory_soup.find_all('a', href=True):
    a_text = a_tag.text.replace("/","")
    if valid_date(a_text): 
        #append tuple 
        datajson_url_list.append((directory_url +"/"+ a_text +"/"+ suffix_url,
                                  target_folder +"/"+ "HealthData.gov_" + a_text + "_data.json"
                                 ))

    
# Sorts list to start with most recent
datajson_url_list.sort(reverse=True)  




lines_read = 0

for index,target in enumerate(datajson_url_list[280:]):
    #print "Running download_file("+target[0],target[1]+")"
    #time.sleep(random.randint(1,5)) # Wait for a few seconds to not overload server

    saved = download_file(target[0],target[1])
    #print "==> saved, read_limit, index:", saved, read_limit, index

    if saved and read_limit:
        lines_read += 1
        if lines_read >= read_limit:
            break    


