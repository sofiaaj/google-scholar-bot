import pandas as pd
import math
import re
import pygsheets
import tweepy
import json
from simplegmail import Gmail


CREDENTIALS_FILE = "twitter_keys.json"
ERROR_PUBS = "error_pubs.csv"
AFFILIATE_INFO = "cpi_affiliates_publications.csv"
POTENTIAL_NEW_PUBS = "potential_new_pubs.csv"
GOOGLE_SHEET_NEW_PUBS = "1CiV3WkPRUkFcCfxmZI3xcQYx3ng3sjy8AfodqW_UbuU"
GOOGLE_SHEET_NEWSLETTER = "13-MUcSemcHh95m7dxEdY5yWP5mMzNpfbSXginEQyaek"
GOOGLE_SHEET_AFFILIATES = "194ej-IlYeSz6ztKYEPoHDXm4FJVThJDNR2XKwHm0qdE"


def send_mail_alert():
    with open('tweet_newsletter_pubs.txt', "r") as text_file:
        email = text_file.read()
    gmail = Gmail()
    params = {
      #"to": ["cvarner@stanford.edu","grusky@stanford.edu"],
      "to": "grusky@stanford.edu",
      "sender": "cpi.affiliate.scraper@gmail.com",
      "cc": ["sofiaaj@stanford.edu","lfsomers@stanford.edu"],
      "subject": "New research by CPI affiliates",
      "msg_html": email,
      "msg_plain": email,
      "signature": True  # use my account signature
    }
    message = gmail.send_message(**params)  

def add_to_newsletter_options(rel_pubs,date):
    print("Adding to newsletter options...")
    # Fetch newsletter
    # Remove all "done" rows
    # Append true_pubs
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_NEWSLETTER)
    gs = sh.sheet1
    gs.clear()
    gs.set_dataframe(rel_pubs,(1,1))
    sheet_title = 'Articles for Newsletter and Website ' + date
    sh.title=sheet_title
    if len(rel_pubs) > 0:
        send_mail_alert()


def process_relevant(df,date):
    rel_pubs = df[df['relevant'] != 'FALSE']
    rel_pubs.rename(columns = {'accurate':'laura_accurate_verified'}, inplace = True)
    rel_pubs.rename(columns = {'relevant':'laura_relevant_verified'}, inplace = True)
    rel_pubs['add_to_newsletter?'] = 'PENDING'
    add_to_newsletter_options(rel_pubs,date)


def get_google_sheet():
    gc = pygsheets.authorize()
    sh = gc.open_by_key(GOOGLE_SHEET_NEW_PUBS)
    gs = sh.sheet1
    df = gs.get_as_df()
    #If any rows have a status other than PENDING, TRUE, or FALSE, change to PENDING:
    gs.clear()
    date = re.search('\d{4}-\d{2}-\d{2}',str(sh)).group(0)
    return df,date

def main():
	with open(CREDENTIALS_FILE) as f:
		tc = json.load(f)
	df,date = get_google_sheet()
	process_relevant(df,date)

if __name__ == "__main__":
    main()