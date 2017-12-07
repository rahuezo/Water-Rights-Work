from bs4 import BeautifulSoup as BS
from selenium import webdriver as wd

import requests as req
import time
import csv
import urlparse
import re
import os
import multiprocessing as mp

from get_sswdu_reports import get_row

import random

url = 'http://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Page_From=EWWaterRightPublicSearch.jsp&Redirect_Page=EWWaterRightPublicSearchResults.jsp&Object_Expected=EwrimsSearchResult&Object_Created=EwrimsSearch&Object_Criteria=&Purpose=&subTypeCourtAdjSpec=&subTypeOtherSpec=&appNumber={sn}&permitNumber=&licenseNumber=&waterHolderName=&source=&hucNumber='
burl = 'http://ciwqs.waterboards.ca.gov/ciwqs/ewrims/'

# SUPPLEMENTAL STATEMENT OF WATER DIVERSION AND USE FORMS

sswdu_tag = 'Supplemental Statement of Water Diversion and Use'

# PHANTOMJS_PATH = r'C:\Users\rahuezo\Documents\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin/phantomjs.exe'
PHANTOMJS_PATH = r'C:\Users\Rudy\Documents\PhantomJS\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'

REPORTS = 'sswdu_reports_to_unitify.csv'
RESULTS = 'sswdu_results_testing.csv'

HEADER = ['Form Type', 'Year of Data', 'Statement Number', 'Water Under', 'Year Diversion Commenced', 'Jan. Diverted', 'Feb. Diverted', 'Mar. Diverted', 'Apr. Diverted', 'May. Diverted', 'Jun. Diverted', 'Jul. Diverted', 'Aug. Diverted', 'Sep. Diverted', 'Oct. Diverted', 'Nov. Diverted', 'Dec. Diverted', 'Total Diverted', 'Jan. Used', 'Feb. Used', 'Mar. Used', 'Apr. Used', 'May. Used', 'Jun. Used', 'Jul. Used', 'Aug. Used', 'Sep. Used', 'Oct. Used', 'Nov. Used', 'Dec. Used', 'Total Used', 'Water Transfered', 'Quantity Transfered', 'Water Supply Contract', 'Source from which Contract was Diverted', 'Amount Authorized to be Diverted in 20XX', 'Purpose of Use', 'Are You Using Groundwater in Lieu of Surface Water?', 'Amount of Groundwater Used?', 'Units']

def get_snumbers(snumbers_f=REPORTS):
    with open(snumbers_f, 'rb') as f:
        reader = csv.reader(f, delimiter=',')
        
        for row in reader:
            yield row
            

def get_report_home(snumber):
    sc = req.get(url.format(sn=snumber)).content
    
    soup = BS(sc, 'html.parser')
    
    result = filter(lambda x: 'Reports' in x.text, soup.find_all('a'))
    
    if result:
        return burl + result[0].get('href')
    return None

def get_all_reports(url, year):
    sc = req.get(url).content
    soup = BS(sc, 'html.parser')
    
    links = filter(lambda x: sswdu_tag in x.find_all('td')[1].text
                   and year in x.find_all('td')[0].text,
                   soup.select('table.data')[0].find_all('tr')[1:])
    
    return map(lambda x: burl + x.find_all('a')[0].get('href'), links)

def get_report_details(url):
    print "GET REPORT UNITS"
    driver = wd.PhantomJS(executable_path=PHANTOMJS_PATH)
    driver.get(url)
    
    sc = driver.page_source
    
    driver.quit()
    
    if result:
        return [result[0].replace('(', '').replace(')', ''), total_diverted, total_used]
    return 'NA'

def get_rows(spacket):
    year, snumber = spacket
    
    report_home = get_report_home(snumber)
    
    links = get_all_reports(report_home, year)
    
    for link in links:
        print link
        yield get_row(link)
        
    # return [get_row(l) for l in links]
    # except Exception as msg:
    #     print msg
    #     return None
    
last_item = 100

snumbers = list(get_snumbers())[last_item:105]

t = time.time()

with open(RESULTS, 'wb') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    writer.writerow(HEADER)

    i = 0

    while i < len(snumbers):
        print "SSWDU Row {0}".format(i + last_item)

        rows = get_rows(snumbers[i])
        
        for row in rows:
            writer.writerow(row)
        i += 1

print "Finished ", round(time.time() - t, 2)
    
