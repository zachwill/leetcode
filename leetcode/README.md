# Leetcode

Scraping Leetcode questions


### Setup

```bash
# Create the local SQLite database
python models.py
```


### Usage

```bash
# Grab initial question list
scrapy crawl categories

# Scrape question data
scrapy crawl questions
```
