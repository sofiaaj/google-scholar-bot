import pandas as pd
import math
import re
import pygsheets
import datetime
import tweepy
import json

CREDENTIALS_FILE = "twitter_keys.json"
GOOGLE_SHEET_TWEET_NEWSLETTER = "13-MUcSemcHh95m7dxEdY5yWP5mMzNpfbSXginEQyaek"
GOOGLE_FOLDER_NEWSLETTER = "1zuTIgIn3KH5JQWb04pKYlRs9nfgSqCTf"
GOOGLE_SHEET_RELATED_PUBLICATIONS = "1lF_90tjsFMUTpjnhP-BwZ7wBPMQQUVRVr8WbpZMGdXk"

def create_tweet(tweet,tc):
	consumer_key = tc['twitter_consumer_key']
	consumer_secret = tc['twitter_consumer_secret']
	access_token_key = tc['twitter_access_token_key']
	access_token_secret = tc['twitter_access_token_secret']
	auth=tweepy.OAuthHandler(consumer_key,consumer_secret)
	auth.set_access_token(access_token_key,access_token_secret)
	api=tweepy.API(auth)
	try:
		resp = api.update_status(tweet)
		print("The following was tweeted: ")
		print(tweet)
	except:
		print("An error occured")


def process_tweet(df,tc):
	to_tweet = df[df['tweet?'] == 'TRUE']
	tweets = to_tweet['tweet_draft'].tolist()
	for t in tweets:
		create_tweet(t,tc)

def get_newsletter_tweet_sheet():
	gc = pygsheets.authorize()
	sh = gc.open_by_key(GOOGLE_SHEET_TWEET_NEWSLETTER)
	gs = sh.sheet1
	df = gs.get_as_df()
	gs.clear()
	return(df)


def add_to_newsletter(df):
    gc = pygsheets.authorize()
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday(), weeks=1)
    sheet_title = str(monday)
    # move curr_newsletter to new document with date as name
    # clear curr_newsletter
    sh = gc.create('temp',folder=GOOGLE_FOLDER_NEWSLETTER)
    gs = sh.sheet1
    df = df.rename(columns={'add_to_newsletter':'david_add_to_newsletter'})
    gs.set_dataframe(df,(1,1))
    sh.title=sheet_title

def add_to_website(df):
	gc = pygsheets.authorize()
	sh = gc.open_by_key(GOOGLE_SHEET_RELATED_PUBLICATIONS)
	gs = sh.sheet1
	website = gs.get_as_df()
	gs.clear()
	website['nid'] = website['nid'].astype(str)
	df = df.drop(['laura_accurate_verified','laura_relevant_verified','add_to_newsletter?'],axis=1)
	df['nid'] = df['nid'].astype(str)
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

def main():
	with open(CREDENTIALS_FILE) as f:
		tc = json.load(f)
	df = get_newsletter_tweet_sheet()
	nl = df[df['add_to_newsletter?'] != 'FALSE']
	ws = df[df['add_to_newsletter?'] == 'TRUE']
	add_to_newsletter(nl)
	add_to_website(ws)

if __name__ == "__main__":
	main()