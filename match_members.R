library(dplyr)
library(data.table)
library(stringr)
library(stringdist)

cpi = fread('cpi_authors.csv') %>% 
  select(-nid) %>% 
  rename(cpi_affiliation = affiliation,
         cpi_author = author) %>%
  mutate(cpi_author = tolower(str_replace_all(cpi_author,"[[:punct:]]","")))

sra = fread('sra_members.csv') %>%
  mutate(author = paste(first,last,sep=" "),
         author = tolower(str_replace_all(author,"[[:punct:]]",""))) %>%
  select(-email,-last,-first)

find_most_similar <- function(str, reference_list) {
  distances <- stringdist::stringdistmatrix(str, reference_list, method = "jaccard")
  closest_indices <- apply(distances, 1, which.min)
  return(reference_list[closest_indices])
}

# Find the most similar string in list2 for each string in list1
closest_strings <- find_most_similar(sra$author, cpi$cpi_author)

matched = data.frame(author=sra$author,cpi_author=closest_strings) %>%
  mutate(difference = stringdist(author,cpi_author)) %>%
  filter(difference < 3) %>%
  select(-difference)

sra_done = merge(sra,matched,by='author') %>%
  merge(.,cpi,by='cpi_author') %>%
  select(-cpi_author,-cpi_affiliation)

sra_not_done = sra %>% filter(!author %in% sra_done$author)

bind_rows(sra_done,sra_not_done) %>% fwrite(.,'sra_members_with_scholar_id.csv')