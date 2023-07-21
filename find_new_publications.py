import pandas as pd
import math
import sys
import random
import datetime
from serpapi import GoogleSearch
import re
import json
import pygsheets
from simplegmail import Gmail
import signal
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

#ADD EMAIL NOTIFICATIONS

CREDENTIALS_FILE = "scraper_keys.json"
SERP_API_KEY = ""
GOOGLE_SHEET_NEWPUBS = ""
GOOGLE_SHEET_AFFILIATES = ""
GOOGLE_FOLDER_NEWSLETTER = ""
EMAIL_FILE = ""

pubs_df = {}
pubs_df['author'] = []
pubs_df['affiliation'] = []
pubs_df['google_scholar_ID'] = []
pubs_df['nid'] = []
pubs_df['link'] = []
pubs_df['title'] = []
pubs_df['pubdate'] = []
pubs_df['citation'] = []
pubs_df['result_id'] = []

def set_api_key():
    with open(CREDENTIALS_FILE) as f:
        tc = json.load(f)
    global SERP_API_KEY
    SERP_API_KEY = tc['serp_api_key']

def set_constants(type):
    if type == 'sra':
        GOOGLE_SHEET_NEWPUBS = "1MQ-JbJtLGvE8CE2_LDRua4MEcmiUlOxlcjojpNN2Q6Y"
        GOOGLE_SHEET_AFFILIATES = "1IB_fiYUTC6fWSP9K2P5fIj-Xpf2ArChTR8cip7K0hOQ"
        GOOGLE_FOLDER_NEWSLETTER = "1PQU8Y09v-FgbEVkZ_4XYI0rBLxHcDwUk"
        EMAIL_FILE = 'new_pubs_email_sra.txt'
        EMAIL_SUBJECT = "New research by SRA members"
    elif type == 'cpi':
        GOOGLE_SHEET_NEWPUBS = "1wKLIj3fjTHMpgQ1Lhv2U7a2Y3QV-GVU1-x1l6gTVfnw"
        GOOGLE_SHEET_AFFILIATES = "194ej-IlYeSz6ztKYEPoHDXm4FJVThJDNR2XKwHm0qdE"
        GOOGLE_FOLDER_NEWSLETTER = "1zuTIgIn3KH5JQWb04pKYlRs9nfgSqCTf"
        EMAIL_FILE = 'new_pubs_email_cpi.txt'
        EMAIL_SUBJECT = "New research by CPI affiliates"

def send_mail_alert():
    with open(EMAIL_FILE, "r") as text_file:
        email = text_file.read()
    gmail = Gmail()
    params = {
      "to": "lfsomers@stanford.edu",
      "sender": "cpi.affiliate.scraper@gmail.com",
      "cc": ["sofiaaj@stanford.edu"],
      "subject": EMAIL_SUBJECT,
      "msg_html": email,
      "msg_plain": email,
      "signature": True  # use my account signature
    }
    message = gmail.send_message(**params)  

def get_search_params(query="",search_type='no_scholar_id',author_id=""):
    params = {}
    if search_type == 'no_scholar_id' or search_type == "link":
        engine = "google_scholar"
    elif search_type == "citation":
        engine = "google_scholar_cite"
    elif search_type == "scholar_id":
        engine = "google_scholar_author"
    scisbd = 0 if(search_type=='citation' or search_type == 'link') else 2
    params['engine'] = engine
    params["api_key"] = 'dfb9491bc74734f626427361dd9c3b2478d96b5e360277075977aa59683097ca'
    params["scisbd"] = scisbd
    if search_type == 'scholar_id':
        params["sort"] = "pubdate"
        params["author_id"] = author_id
    else:
        params["q"] = query    
    return(params)

def get_row_values(row,values):
    toreturn = []
    for val in values:
        toreturn.append(row[val])
    return toreturn

def add_entry(searchtype,row,pub,title,link="Missing",result_id="Missing",pubdate="Missing",citation="Missing"):
    value_names = ['nid','author','affiliation','google_scholar_ID']
    values = get_row_values(row,value_names)
    if link == "Missing":
        link = pub.get('link')
    if pubdate == "Missing":
        pubdate = pub.get('year')
    if(searchtype == "serp_scholar"):
        if citation == "Missing":
            citation = pub.get('publication')
        if result_id == "Missing":
            result_id = pub.get('citation_id')
    else:
        result_id = pub.get('result_id')
    for i in range(0,len(values)):
        pubs_df[value_names[i]].append(values[i])         
    pubs_df['title'].append(title)
    pubs_df['pubdate'].append(pubdate)    
    pubs_df['citation'].append(citation)
    pubs_df['link'].append(link)
    pubs_df['result_id'].append(result_id)

def getlink(author,title):
    query = "author:\"" + author + "\" " + title
    search = GoogleSearch(get_search_params(query,search_type="link"))
    results = search.get_dict()
    pubs = results.get('organic_results')
    if pubs:
        curr = pubs[0]
        checktitle = curr.get('title')
        link = curr.get('link') 
        result_id = curr.get('result_id')
    else:
        link = "Missing"
        result_id = "Missing"
    return(link,result_id)

def get_affiliate_df():
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_AFFILIATES)
    gs = sh.sheet1
    affils = gs.get_as_df()
    return(affils)


def find_pubs_scholar_id(affils):
    df = affils[affils['google_scholar_ID'] != "Missing"]
    for index, row in df.iterrows():
        author = row['author']
        sch_id = row['google_scholar_ID']
        google_scholar_ID = sch_id.replace("\"","")
        old_title = row['title']      
        clean_old = re.sub(r'[^A-Za-z0-9 ]+', '', old_title.lower())
        print("Retrieving publications by... " + author)
        try:
            with time_limit(180):
                params = get_search_params(search_type="scholar_id",author_id=google_scholar_ID)
                search = GoogleSearch(params)
                results = search.get_dict()
                pubs = results.get('articles')
                if pubs:
                    curr = pubs[0]
                    title = curr.get('title')
                    publication = curr.get('publication')
                    clean_new = re.sub(r'[^A-Za-z0-9 ]+', '', title.lower())
                    if(clean_new != clean_old):
                        print("Updating database...")
                        print("Old title: ", old_title)
                        print("New title: ", title)
                        params["view_op"] = "view_citation"
                        citation_id = curr.get('citation_id')
                        params["citation_id"] = citation_id
                        search = GoogleSearch(params)
                        results = search.get_dict()
                        link = results.get('citation').get('link')
                        pubdate = results.get('citation').get('publication_date')
                        publication2 = results.get('citation').get('journal')
                        citation = publication2 if publication2 else publication
                        add_entry("serp_scholar",row,curr,title,link=link,result_id=citation_id,pubdate=pubdate,citation=citation)
        except TimeoutException as e:
            print("Timed out!")
                      
def find_pubs_no_scholar_id(affils):
    df = affils[affils['google_scholar_ID'] == "Missing"]  
    for index, row in df.iterrows():
        author = row['author']
        old_title = row['title']      
        clean_old = re.sub(r'[^A-Za-z0-9 ]+', '', old_title.lower())
        query = "author:\"" + author + "\""
        print("Searching for... " + author)
        try:
            with time_limit(90):
                search = GoogleSearch(get_search_params(query))
                results = search.get_dict()
                pubs = results.get('organic_results')
                if pubs:
                    curr = pubs[0]
                    title = curr.get('title')
                    clean_new = re.sub(r'[^A-Za-z0-9 ]+', '', title.lower())
                    if(clean_new != clean_old):
                        print("Updating database...")
                        print("Old title: ", old_title)
                        print("New title: ", title)
                        add_entry("serp",row,curr,title)
        except TimeoutException as e:
            print("Timed out!")

def get_citation(result_id):
    year = "Missing"
    citation = "Missing"
    search = GoogleSearch(get_search_params(search_type="citation",query=result_id))    
    results = search.get_dict()
    try:
        print(results['citations'][0])
        citation = results["citations"][0].get('snippet')
    except:
        citation = ""
    cite_pattern = '" (.+)'
    match = re.search(cite_pattern, citation)
    if match:
        citation = match.groups()[0]
    year_pattern = '\((\d+)\)'
    match = re.search(year_pattern, citation)
    if match:
        year = match.groups()[0]
        year = year + "/1/1"
    return(citation,year)


#For remaining matches, we fetch missing data (citation, link, etc). 
#Usually, missing data consists of the paper's URL for data obtained through scholarly. 
#Citation and year for data updated with SerpAPI. 
def fetch_missing_data(newpubs):
    for index, row in newpubs.iterrows():
        #If link is missing for SerpAPI searches, it just means there is no link
        if(row['link'] == "Missing" and row['nid'] != "Missing"):
            link, result_id = getlink(row['author'],row['title'])
            newpubs.loc[index,'link'] = link
            newpubs.loc[index,'result_id'] = result_id
        if((row['citation'] == "Missing" or row['citation'] == "") and row['result_id'] != "Missing"):
            citation, year = get_citation(row['result_id'])
            newpubs.loc[index,'citation'] = citation
            newpubs.loc[index,'pubdate'] = year
    return newpubs

def update_google_sheet(df):
    #We don't make a new potential matches document, we add to it so as to keep anything that might still be pending.
    update_affil_google_sheet(df)
    df = df.drop(['result_id','affiliation','google_scholar_ID'],axis=1)
    df['author'] = df.groupby(['title'])['author'].transform(lambda x: ', '.join(x))
    df['nid'] = df['nid'].astype(str)
    df['nid'] = df.groupby(['title'])['nid'].transform(lambda x: ', '.join(x))
    df.drop_duplicates(inplace=True)
    df['accurate'] = 'PENDING'
    df['relevant'] = 'PENDING'
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_NEWPUBS)
    gs = sh.sheet1
    gs.clear()
    gs.set_dataframe(df,(1,1))
    if len(df) > 0:
        send_mail_alert()


def update_affil_google_sheet(df):
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_AFFILIATES)
    gs = sh.sheet1
    affiliate_info = gs.get_as_df()
    df = df.reset_index(drop=True)
    df = df.drop(['result_id'],axis=1)
    remove_cpi_id = df['nid'].tolist()
    new_affil_info = affiliate_info[~affiliate_info.nid.isin(remove_cpi_id)]
    new_affil_info = new_affil_info.reset_index(drop=True)
    new_affil_info = new_affil_info.append(df)
    gs.clear()
    gs.set_dataframe(new_affil_info,(1,1))

def add_to_website(df,old_date):
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_RELATED_PUBLICATIONS)
    gs = sh.sheet1
    website = gs.get_as_df()
    gs.clear()
    website['nid'] = website['nid'].astype(str)
    df = df.drop(['accurate','relevant'],axis=1)
    df['nid'] = df['nid'].astype(str)
    # replace missing date with date article was fetched
    df.loc[df["pubdate"] == "Missing", "pubdate"] = str(datetime.date.today())
    df = pd.concat([website,df]).reset_index(drop=True)
    df['nid'] = df['nid'].apply(lambda x: x.split(','))
    df['author'] = df['author'].apply(lambda x: x.split(','))
    df['pubdate'] = pd.to_datetime(df['pubdate'])
    # sort so most recent articles are first. we'll only add the 3 most recent articles
    df = df.sort_values(by='pubdate',ascending=False)
    nids = {}
    for index, row in df.iterrows():
        nid = row['nid']
        for i in range(0,len(nid)):
            n = nid[i]
            author = row['author'][i]
            link,title,citation,pubdate = row.values[2:]
            publication = [n,author,link,title,citation,pubdate]
            if n not in nids:
                nids[n] = []
            if(len(nids[n]) < 3):
                nids[n].append(publication)
    data = [item for sublist in nids.values() for item in sublist]
    data = pd.DataFrame(data, columns = ['nid','author','link','title','citation','pubdate'])
    data.drop_duplicates(subset=['title','nid'], keep='last',inplace=True)
    data['author'] = data.groupby(['title'])['author'].transform(lambda x: ','.join(x))
    data['nid'] = data.groupby(['title'])['nid'].transform(lambda x: ','.join(x))
    data.drop_duplicates(inplace=True)
    gs.set_dataframe(data,(1,1))    


def arrange_sheets():
    # rename new sheet to current date
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_NEWPUBS)
    old_title = sh.title
    gs = sh.sheet1
    df = gs.get_as_df()
    gs.clear()
    new_title = datetime.date.today()
    sh.title=str(new_title)
    # move old data to new sheet
    sh = gc.create('temp',folder=GOOGLE_FOLDER_NEWSLETTER)
    gs = sh.sheet1
    gs.set_dataframe(df,(1,1))
    sh.title=old_title
    # add verified articles to website
    #website = df[df['relevant'] == 'TRUE']
    #add_to_website(website,old_title)


def main():
    set_api_key()
    year_pattern = '\((\d+)\)'
    # this moves sheet from previous run to a new note
    arrange_sheets()
    affils = get_affiliate_df()
    find_pubs_scholar_id(affils)
    find_pubs_no_scholar_id(affils)
    newpubs = pd.DataFrame.from_dict(pubs_df)
    newpubs = fetch_missing_data(newpubs)
    update_google_sheet(newpubs)

if __name__ == "__main__":
    args = sys.argv
    if(len(args) == 2 and args[1] in ['cpi','sra']):
        print('fetching ' + args[1] + ' publications...')
        set_constants(args[1])
        main()
    else:
        print('Please specify one of "cpi" or "sra"')