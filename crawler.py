import urllib2
import pymongo
import re
import datetime
import pdb
import json
from alchemyapi import AlchemyAPI
from subprocess import Popen
import os
import httplib
import csv
import numpy as np

class Crawler():
    
    def findTicker(self, string):
        print "Finding ticker..."
        target = "".join(e for e in string if e.isalnum())
        url = "http://finance.yahoo.com/q?s=%s" % target
        headers =  {'User-Agent': 'Mozilla/5.0 (X11; Linux x8c`6_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                    'Accept-Encoding': 'none',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Connection': 'keep-alive'}
        request = urllib2.Request(url, headers=headers)
        page = urllib2.urlopen(url)
        redirect = page.url
        
        ticker_match = re.search(r'q\?s=(\w+)', redirect)
        if not ticker_match:
            return
            raise Exception('Could not find ticker_match!')
        else:
            ticker = ticker_match.group(1)
            print "Found Ticker match! %s" % ticker
            return ticker
        
    def searchCalls(self, ticker):
        print "Searching for calls..."
        url = "http://seekingalpha.com/symbol/%s/transcripts" % ticker
        headers =  {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                    'Accept-Encoding': 'none',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Connection': 'keep-alive'}
        request = urllib2.Request(url=url, headers=headers)
        try: page_raw = urllib2.urlopen(request).read()
        except:
            return
            raise Exception('Could not read page_raw!')
        transcript_urls_match = re.findall(r'<a href="([^<>]*?)" sasource="qp_transcripts">([^<>]*?)</a>', page_raw, flags=re.S|re.I|re.M)
        if not transcript_urls_match:
            return
            raise Exception('Could not find transcript_urls_match!')
        else:
            return transcript_urls_match
    
    def scrapeCall(self, url_segment, target):
        def GetFinancialRegression(ticker, date):
            print "Creating financial regression..."
            date_match = re.search(r'(\w+)\s(\d+),\s*(\d{4})', date, flags=re.S|re.I|re.M)
            
            if not date_match:
                raise Exception("Could not find date_match!")
            else:
                print "Established date match!"
                month = datetime.datetime.strptime(date_match.group(1), "%B").month
                day = date_match.group(2)
                year = date_match.group(3)
                
                if month >= 9:
                    start_month = month - 3
                    start_year = year
                    next_month = month - 9
                    next_year = int(year) + 1
                ##Go back to finish! elif month <= 3:
                else:
                    next_month = month + 2
                    next_year = year
            
            print "Creating URL..."
            historical_url = "http://ichart.yahoo.com/table.csv?s=%s&a=%s&b=%s&c=%s&d=%s&e=&%s&f=%s" % (ticker, month, day, year, next_month, day, next_year)
            try: historical_data = urllib2.urlopen(historical_url).read()
            except: return
            print "read page!"
            
            days = re.findall(r'\n([^\n]*?)\n', historical_data)
            
            if not days:
                raise Exception('Could not find days!')
            
            closing_prices = []
            percentage_changes = []
            average_percentage_change = 0
            
            for i in range(0, len(days)):
                closing_price_match = re.search(r',\d+,(\d+\.\d{2})', days[i])
                if not closing_price_match:
                    raise Exception('Could not find closing_price_match!')
                else:
                    closing_price = float(closing_price_match.group(1))
                    closing_prices.append(closing_price)
            return np.std(closing_prices)
            
        print "Scraping trancsript text..."
        
        url = "http://seekingalpha.com%s&page=single" % url_segment[0]
        title = url_segment[1]
        print "-----------------------------"
        print title
        print "-----------------------------"
        headers =  {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}
        request = urllib2.Request(url=url, headers=headers)
        try: page_raw = urllib2.urlopen(request).read()
        except:
            raise Exception('Could not open page_raw!')
        page_clean = page_raw.decode('UTF-8')
        page_clean = page_clean.replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '').replace('\n', '')
        
        print "Finding transcript_text_match..."
        transcript_text_match = re.search(r'<div id="article_body" itemprop="articleBody">(.*?)<div id="article_disclaimer" class="content_part hid">', page_raw, flags=re.S|re.I|re.M)
        if not transcript_text_match:
            breakpoint(page_raw)
            pdb.set_trace()
            raise Exception('Could not find transcript_text_match!')
        transcript_text = transcript_text_match.group(1)
        
        print "Finding Q&A match..."
        qa_match = re.search(r'<div id="article_qanda" class="content_part hid">(.*?)</div>', transcript_text, flags=re.S|re.I|re.M)
        if not qa_match:
            pdb.set_trace()
            raise Exception('Could not find qa_match!')
        else:
            qa_text = qa_match.group(1)
        
        print "finding call_date_match..."
        call_date_match = re.search(r'(\w+\s+\d+,\s+\d{4},?\s+\d+:\d\d\s+[AP]M\s[EPCG]M?T)', transcript_text, flags=re.S|re.I|re.M)
        if not call_date_match:
            return
            breakpoint(transcript_text)
            raise Exception('Could not find call_date_match!')
        call_date = call_date_match.group(1)
        
        print "Creating AlchemyAPI instance..."
        alchemyapi = AlchemyAPI()
        
        print "Sending AlchemyAPI request..."
        response = alchemyapi.sentiment(flavor='url', data=url)
        if response['status'] == 'OK':
            print "returned AlchemyAPI object!"
        else:
            print('Error in sentiment analysis call: ', response['statusInfo'])
        beta = GetFinancialRegression(target, call_date)
        print beta
        try: transcript = {'target': target,
                      'text': transcript_text,
                      'collection_date': datetime.datetime.now(),
                      'call_date': call_date,
                      'source': url,
                      'html': page_raw,
                      'transcript_text': transcript_text,
                      'title': title,
                      'qa_text': qa_text,
                      'sentiment': response['docSentiment'],
                      'beta': beta}
        except: return
        print "Returning transcript..."
        return transcript
    
    def __init__(self, target):
        client = pymongo.MongoClient()
        db = client.db
        counter = 0
        
        ticker = self.findTicker(target)
        transcript_urls = self.searchCalls(ticker)
        try:
            for transcript_url in transcript_urls:
                print "Checking if webcast..."
                if re.search(r'webcast', transcript_url[0]):
                    print "URL refers to webcast. Disregarding..."
                else:
                    print "Not a webcast."
                    url = "http://seekingalpha.com%s&page=single" % transcript_url[0]
                    #if not db.transcripts.find_one({'source': url, 'target': target}):
                    #    transcript = self.scrapeCall(transcript_url, target)
                    #    if transcript:
                    #        if not db.transcripts.find_one({'title': transcript['title'], 'call_date': transcript['call_date'], 'sentiment': transcript['sentiment']}):
                    #            db.transcripts.insert(transcript)
                    #            print "Successfully inserted %s @ %s" % (transcript['title'], datetime.datetime.now())
                    #        else:
                    #            print "%s already exists in database!" % transcript['title']
                    #print "______________________________________________________"
                    #print "                                                      "
                    #print "-------------------URL Completed----------------------"
                    #print "______________________________________________________"
                    transcript = self.scrapeCall(transcript_url, target)
                    if transcript:
                        db.transcripts.update({'target':target, 'call_date':transcript['call_date']}, transcript)
                    else:
                        print "ScrapeCall returned Nonetype!"
                    print "Updated transcript"
                    
        except: return
def breakpoint(output):
    text_file = open("output.html", "w")
    text_file.write(output)
    Popen(['gedit', 'output.html'])