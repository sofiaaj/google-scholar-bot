# Google Scholar Bot
This project uses [SerpAPI](https://serpapi.com/) to retrieve information on publications from Google Scholar. Our goal is to keep track of new articles published by CPI affiliates and SRA members. Because there are hundreds of affiliates and members, we created an automated system using Google Scholar to help us do this.

## Code and data files

* get_google_scholar_id.py: Tries to match scholar names with a Google Scholar ID.
* find_new_publications.py: Goes through every affiliate in our database, finds their latest publication available on Google Scholar, and compares it to our previously stored publication to determine if it’s new. The script then uploads potential new publications to a google sheet. Code takes one of two arguments, 'cpi' or 'sra' to determine which list of scholars to go through.
* match_members.R: For convenience, quick code that will take a new list of affiliates and match with an existing list. This avoids having to find a Google Scholar ID for the same person twice.

## Code overview

**Pre-processing**: The first step in the process was to obtain the Google Scholar ID of every CPI affiliate. This ID is useful because IDs are unique, names are not. Using the correct ID is much more likely to yield accurate search results. We used SerpAPI to do an organic search of each affiliate’s name and retrieve the corresponding ID. For those affiliates we couldn’t find an ID for, we do a second check using Scholarly. We were able to find a Scholar ID for 67\% of SRA members and 71\% of CPI affiliates. 

The second step is to create a database with the latest publication by each CPI affiliate. This data is essential because we will determine if a publication is “new” by comparing the latest title retrieved with the one in the database. We retrieve the latest publication for affiliates with a Google Scholar ID using Scholarly and fetch the rest using SerpAPI. 

After creating this database, we carried out a manual check to verify the results made sense. If, for example, we obtained a publication from an Electrical Engineering journal for an education researcher, we inspected the result to ensure we had the correct google scholar ID. 

**Fetch new publications**: Having conducted all pre-processing, we can begin to retrieve new publications for our scholar lists. This requires the following steps:
1. 	Because the list of new publications is always in the same sheet, we have to retrieve content from this sheet and store in a folder to save for future reference. Then, we clear the sheet to make room for new publications.
2.	Then, we open and read Google Sheet containing the scholar ID and latest publication of either CPI affiliates or SRA members.
3.	Run a script to fetch the latest publication for each affiliate on Google Scholar. 
4.	We compare the title obtained to the title in our file. If the titles don’t match, this becomes a “tentative” new publication which we append to the tentative_titles.csv file.
5.	For these tentative new publications, we fill in any missing data:
a. 	For each article, we get the following information: article title, publisher, and URL.
b.	Articles obtained using Scholarly don’t have an associated URL so we use SerpAPI to obtain it.
c.	Articles obtained using SerpAPI don’t have an associated journal/publisher. We have to use a different SerpAPI query to obtain it.
6.	Finally, we save the list of new publications to Google Drive and send an automated email to Laura with a link to it.
