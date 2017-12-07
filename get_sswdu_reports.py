from bs4 import BeautifulSoup as BS
from selenium import webdriver as wd
import requests as req
import re

PHANTOMJS_PATH = r'C:\Users\Rudy\Documents\PhantomJS\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'

def clean_text(s):
    return ' '.join(' '.join(re.findall(r'[ -~]+', s)).split())

def get_form_type_and_year(sc): 
    form_type = re.findall(r'(SUPPLEMENTAL STATEMENT OF WATER DIVERSION AND USE FOR [0-9]{4})', clean_text(sc))[0] 
    year = re.findall(r'([0-9]{4})', form_type)[0]
    return [form_type, year]

def get_statement_number(sc):
    # results = re.findall(r'<br /> Statement Number: (.*?) <br />', clean_text(sc))
    results = re.findall(r'<br> Statement Number: (.*?) <br>', clean_text(sc))
    
    # print results
    
    
    return results[0]

def get_water_under_and_diverted(sc): 
    soup = BS(sc, 'html.parser')
    table = filter(lambda x: 'Water is used under' in x.text, soup.select('table'))[0]
    used_under = clean_text(table.select('tr')[0].select('td')[-1].text)
    year_diverted = clean_text(table.select('tr')[-1].select('td')[-1].text)
    return [used_under if used_under else 'na', year_diverted if year_diverted else 'na']

def is_header(row): 
        return 'Amount directly diverted' in row.text and 'Amount beneficially used' in row.text
    
def is_last_row(row): 
    return 'Total' in row.text

def get_rows_start_end(table): 
    start = end = 0 

    for i, row in enumerate(table.select('tr')): 
        if is_header(row): 
            start = i + 1
        if is_last_row(row): 
            end = i + 1
            break 
    return start, end

def get_revelant_col_nums(cols): 
    results = []
    for i, col in enumerate(cols): 
        if 'Amount directly diverted' in col.text: 
            results.append(i)
        elif 'Amount beneficially used' in col.text: 
            results.append(i)
    return results

def get_amount_diverted_and_used_dets(sc):     
    soup = BS(sc, 'html.parser')
    table = filter(lambda x: 'Amount of Water Diverted and Used' in x.text or 'Amount directly diverted' in x.text, soup.select('table'))[0]
    diverted, used = [], []    
    start, end = get_rows_start_end(table)
    relevant_cols = get_revelant_col_nums(table.select('tr')[start - 1].select('th'))
    
    for row in table.select('tr')[start:end]:
        cols = row.select('td')
        diverted.append(clean_text(cols[relevant_cols[0]].text))
        used.append(cols[relevant_cols[1]].text)
        
    return diverted + used

def get_water_transfers_info(sc): 
    soup = BS(sc, 'html.parser')
    try: 
        table = filter(lambda x: 'Water Transfers' in x.text, soup.select('table'))[0]
        transfered = clean_text(filter(lambda x: 'Water transfered' in x.text, table.select('tr'))[0].select('td')[1].text)
        transfered_qty = clean_text(filter(lambda x: 'Quantity transfered' in x.text, table.select('tr'))[0].select('td')[1].text)
        transfered_qty = transfered_qty if len(transfered_qty) > 0 else '0'
        return [transfered, transfered_qty]
    except:
        return ['na', 'na']
    
def get_water_supply_contract(sc): 
    soup = BS(sc, 'html.parser')
    try: 
        table = filter(lambda x: 'Water Supply Contracts' in x.text, soup.select('table'))[0]
        contract = clean_text(filter(lambda x: 'Water supply contract' in x.text, table.select('tr'))[0].select('td')[1].text)
        contract_source = clean_text(filter(lambda x: 'Source from which contract' in x.text, table.select('tr'))[0].select('td')[1].text)
        authorized_amt = clean_text(filter(lambda x: 'authorized to be diverted in' in x.text, table.select('tr'))[0].select('td')[1].text)
        
        contract_source = contract_source if len(contract_source) > 0 else 'na'
        authorized_amt = authorized_amt if len(authorized_amt) > 0 else '0'
        
        return [contract, contract_source, authorized_amt]
    except:
        return ['na', 'na', 'na']
    
def get_purpose_of_use(sc): 
    soup = BS(sc, 'html.parser')
    table = filter(lambda x: 'Purpose of Use' in x.text, soup.select('table'))[0]
    
    purpose_of_use = '; '.join([clean_text(row.text) for row in table.select('tr')[1:]])
    return purpose_of_use
    
def get_conjuctive_water_use(sc): 
    soup = BS(sc, 'html.parser')
    table = filter(lambda x: 'Surface Water and Groundwater' in x.text, soup.select('table'))[0]
    
    results = []
    
    for row in table.select('tr'):         
        if 'in lieu of surface water' in row.text:            
            cols = row.select('td')
            for i in xrange(len(cols)): 
                if 'in lieu of surface water' in cols[i].text: 
                    results.append(clean_text(cols[i + 1].text))
    
    if not len(results)  > 0:
        results.append('na')
        
    for row in table.select('tr'):         
        if 'Amount of groundwater used' in row.text: 
            cols = row.select('td')
            for i in xrange(len(cols)): 
                if 'Amount of groundwater used' in cols[i].text: 
                    amt = clean_text(cols[i + 1].text)
                    amt = amt if len(amt) > 0 else '0'
                    results.append(amt)
    if not len(results)  > 1:
        results.append('na')
        
    return results
        
def get_units(sc): 
    results = re.findall(r'(\(Acre-Feet\)|\(Gallons\))', clean_text(sc))[0].replace('(', '').replace(')', '')
    return results if results else 'NA'
    
def get_row(url):
    # print
    # print url
    # print
    
    driver = wd.PhantomJS(executable_path=PHANTOMJS_PATH)
    driver.get(url)
    sc = driver.page_source
    driver.quit()
    
    # print "FORM TYPE"
    row = get_form_type_and_year(sc)
    # print "STATEMENT NUMBER"
    row.append(get_statement_number(sc))
    # print "Water under diverted"
    row += get_water_under_and_diverted(sc)
    # print "AMT DIVERTED AND USED"
    row += get_amount_diverted_and_used_dets(sc)
    # print "WATER TRANSFERS"
    row += get_water_transfers_info(sc)
    # print "CONTRACT"
    row += get_water_supply_contract(sc)
    # print "POU"
    row.append(get_purpose_of_use(sc))
    # print "Conjuctive water"
    row += get_conjuctive_water_use(sc)
    row.append(get_units(sc))
    
    return row