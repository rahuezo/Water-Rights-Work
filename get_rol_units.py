from bs4 import BeautifulSoup as BS
from selenium import webdriver as wd

import requests as req
import time
import csv
import urlparse
import re
import os
import multiprocessing as mp 


url = 'http://ciwqs.waterboards.ca.gov/ciwqs/ewrims/EWServlet?Page_From=EWWaterRightPublicSearch.jsp&Redirect_Page=EWWaterRightPublicSearchResults.jsp&Object_Expected=EwrimsSearchResult&Object_Created=EwrimsSearch&Object_Criteria=&Purpose=&subTypeCourtAdjSpec=&subTypeOtherSpec=&appNumber={sn}&permitNumber=&licenseNumber=&waterHolderName=&source=&hucNumber='
burl = 'http://ciwqs.waterboards.ca.gov/ciwqs/ewrims/'

# SUPPLEMENTAL STATEMENT OF WATER DIVERSION AND USE FORMS

rol_tag = ''

# PHANTOMJS_PATH = r'C:\Users\rahuezo\Documents\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin/phantomjs.exe'
PHANTOMJS_PATH = r'C:\Users\Rudy\Documents\PhantomJS\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'

REPORTS = 'rol_reports_to_unitify.csv'
RESULTS = 'rol_results_testing.csv'


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
    
    links = filter(lambda x: rol_tag in x.find_all('td')[1].text
                   and year in x.find_all('td')[0].text,
                   soup.select('table.data')[0].find_all('tr')[1:])
    
    return map(lambda x: burl + x.find_all('a')[0].get('href'), links)


def get_revelant_colnums(cols): 
    results = []
    for i, col in enumerate(cols): 
        if 'Amount directly diverted' in col.text: 
            results.append(i)
        elif 'Amount beneficially used' in col.text: 
            results.append(i)
    return results

def get_total_diver_used(sc): 
    soup = BS(sc, 'html.parser')
    table = filter(lambda x: 'Amount of Water Diverted and Used' in x.text, soup.find_all('table'))[0]
    header = filter(lambda x: 'Amount directly diverted' in x.text and 'Amount beneficially used' in x.text, table.select('tr'))[0]
    cols = get_revelant_colnums(header.select('th'))

    for row in table.select('tr'): 
        tds = row.select('td')

        if tds: 
            if 'Total' in tds[0].text: 
                total_row = map(lambda x: x.text, tds)
                break 
                
    return total_row[cols[0]], total_row[cols[1]]


def get_report_details(url):
    print "GET REPORT UNITS"
    driver = wd.PhantomJS(executable_path=PHANTOMJS_PATH)
    driver.get(url)
    
    sc = driver.page_source
    
    try: 
        total_diverted, total_used = get_total_diver_used(sc)
    except Exception as msg:
        print "An error occurred in get_total_diver_used()", msg
    
    print total_diverted, total_used
    
    sc = ' '.join(sc.split())
    driver.quit()
    result = re.findall(r'(\(Acre-Feet\)|\(Gallons\))', sc)
    
    if result:
        return [result[0].replace('(', '').replace(')', ''), total_diverted, total_used]
    return 'NA'
    
def get_units(spacket):
    year, snumber = spacket
    
    report_home = get_report_home(snumber)
    
    print report_home

    try: 
        links = get_all_reports(report_home, year)
        print links
        return [[year, snumber] + get_report_details(l) for l in links]
    except:
        return None
    

last_item = 0

snumbers = list(get_snumbers())[last_item:100]

t = time.time()

with open(RESULTS, 'ab') as outfile:
    writer = csv.writer(outfile, delimiter=',')

    if not os.path.exists(RESULTS): 
            writer.writerow(['Year', 'Statement Number', 'Units', 'Total Diverted', 'Total Used'])

    i = 0

    while i < len(snumbers):
        print "SSWDU Row {0}".format(i + last_item)

        try:
            rows = get_units(snumbers[i])
            
            print rows

            if rows is None:
                i += 1
                continue
            
            for row in rows: 
                writer.writerow(row)
            i += 1
        except Exception as e:
            print e
            continue
            
print "Finished ", round(time.time() - t, 2)
    
