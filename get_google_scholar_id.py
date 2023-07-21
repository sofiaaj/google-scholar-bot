from serpapi import GoogleSearch
import pandas as pd
import math
from scholarly import scholarly
import json
import string
import pygsheets
import random

CREDENTIALS_FILE = "scraper_keys.json"
AFFILIATE_INFO = "sra_members.csv"
SERP_API_KEY = ""
new_row = {}
new_row['author'] = []
new_row['google_scholar_ID'] = []
new_row['affiliation'] = []
new_row['emails'] = []

def get_search_params(query):
    params = {}
    params['engine'] = "google_scholar"
    params["api_key"] = SERP_API_KEY
    params["q"] = query    
    return(params)

def set_api_key():
    with open(CREDENTIALS_FILE) as f:
        tc = json.load(f)
    global SERP_API_KEY
    SERP_API_KEY = tc['serp_api_key']

    #try to get google scholar information using SerpAPI
def serp_search(name):
    print("Searching for... " + name)
    search = GoogleSearch(get_search_params(name))
    results = search.get_dict()
    profiles = results.get("profiles")
    values = []
    if profiles:
        authors = profiles.get('authors')
        if authors:
            author = authors[0]
            google_scholar_id = author.get('author_id')
            affiliation = author.get('affiliations')
            emails = author.get('email')
            author = name
            values = [author,google_scholar_id,affiliation,emails]
    return values

#We try to fill the remaining values using scholarly
def scholarly_search(author):
    search = scholarly.search_author(author)
    print("Searching for... " + author)
    try:
        curr = next(search)
        info = scholarly.fill(curr,sections=['publications'],sortby="year",publication_limit=1)
        scholar_id = info.get('scholar_id')
        email = info.get('email_domain')
        affil = info.get('affiliation')
        author = info.get('name')
    except StopIteration:
        print("No results for... " + author)
        scholar_id = "Missing"
        email = "Missing"
        affil = "Missing"
        author = author
    values = [author,scholar_id,affil,email]
    return values

def add_entry(values):
    value_names = ['author','google_scholar_ID','affiliation','emails']
    for i in range(0,len(values)):
        new_row[value_names[i]].append(values[i])

def main():
    # change based on needs. my original list of SRA affiliates already had some people with scholar IDs 
    # because they were also CPI affiliates (so we already had a record of them)
    set_api_key()
    df = pd.read_csv(AFFILIATE_INFO)
    complete = df[~df['google_scholar_ID'].isna()]
    df = df[df['google_scholar_ID'].isna()]
    for name in df['author'].tolist():
        values = serp_search(name)
        if len(values) == 0:
            values = scholarly_search(name)
        print(values)
        add_entry(values)
    affils = pd.DataFrame.from_dict(new_row)
    affils['google_scholar_ID'] = affils['google_scholar_ID'].apply(lambda x: f'"{x}"')
    affils['author_original'] = df['author'].tolist()
    affils['affiliation_original'] = df['affiliation'].tolist()
    affils.to_csv('sra_members_with_id.csv',index=False)

if __name__ == "__main__":
    main()