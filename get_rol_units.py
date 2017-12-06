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

rol_tag = 'Report of Licensee'

def get_snumbers(snumbers_f='rol_reports_to_unitify.csv'):
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


def get_report_units(url):
    driver = wd.PhantomJS(executable_path=r'C:\Users\rahuezo\Documents\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin/phantomjs.exe')
    driver.get(url)
    
    sc = ' '.join(driver.page_source.split())
    driver.quit()
    result = re.findall(r'(\(Acre-Feet\)|\(Gallons\))', sc)
    
    if result:
        return result[0].replace('(', '').replace(')', '')
    return 'NA'
    
def get_units(spacket):
    year, snumber = spacket
    
    report_home = get_report_home(snumber)

    try: 
        links = get_all_reports(report_home, year)        
        return [[year, snumber, get_report_units(l)] for l in links]
    except:
        return None
    

last_item = 2429

snumbers = list(get_snumbers())[last_item:]

t = time.time()

with open('rol_results.csv', 'ab') as outfile:
    writer = csv.writer(outfile, delimiter=',')

    if not os.path.exists('rol_results.csv'): 
            writer.writerow(['Year', 'Statement Number', 'Units'])

    i = 0

    while i < len(snumbers):
        print "ROL Row {0}".format(i + last_item)

        try:
            rows = get_units(snumbers[i])

            if rows is None:
                i += 1
                continue
            
            for row in rows: 
                writer.writerow(row)

            i += 1
        except Exception as e:
            print e
            continue

##    
##for i, snumber in enumerate(snumbers):
##    print "ROL Row {0}".format(i + last_item)
##    
##    with open('rol_results.csv', 'ab') as outfile:
##        writer = csv.writer(outfile, delimiter=',')
##        
##        if not os.path.exists('rol_results.csv'): 
##            writer.writerow(['Year', 'Statement Number', 'Units'])
##
##        rows = get_units(snumber)
##
##        if rows is None:
##            continue
##        
##        for row in rows: 
##            writer.writerow(row)
            
print "Finished ", round(time.time() - t, 2)
    
