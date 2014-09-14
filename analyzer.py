#!/usr/bin/env python

import numpy as np
import pylab as pl
from sklearn.svm import SVR
import pymongo
import pdb
import matplotlib.pyplot as plt
import urllib2
from alchemyapi import AlchemyAPI
import re

class Analyzer():
    
    
    db = pymongo.MongoClient().db
    dataset = db.transcripts.find()
    
    def f(x):
        """ function to approximate by polynomial interpolation"""
        return x * np.sin(x)
    
    
    x = []
    y = []
    x_plot =  []
    y_plot = []
    target = "ANGI"
    c=np.random.rand(3)
    
    for data in dataset:
        if data['target'] != target:
            x = []
            y = []
            target = data['target']
            c=np.random.rand(3)
        try:beta = float(data['beta'])
        except:
            db.transcripts.remove(data)
            print "------------REMOVED BAD TRANSCRIPTS ENTRY"
            pass
        try:score = float(data['sentiment']['score'])
        except:
            db.transcripts.remove(data)
            print "------------REMOVED BAD TRANSCRIPTS ENTRY"
            pass
        try:x.append(float(data['sentiment']['score'])), y.append(float(data['beta'])), x_plot.append([float(data['sentiment']['score'])]), y_plot.append(float(data['beta'])),
        except:
            db.transcripts.remove(data)
            print "_________________________REMOVED BAD TRANSCRIPT ENTRY"
            pass
        pl.scatter(x, y, label=target, c=c)
    
    pl.xlabel("Sentiment")
    pl.ylabel("Volatility")
    
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma=0.1)
    svr_lin = SVR(kernel='linear', C=1e3)
    svr_poly = SVR(kernel='poly', C=1e3, degree=2)
    y_rbf = svr_rbf.fit(x_plot, y_plot).predict(x_plot)
    y_lin = svr_lin.fit(x_plot, y_plot).predict(x_plot)
    y_poly = svr_poly.fit(x_plot, y_plot).predict(x_plot)
    
    pl.plot(x_plot, y_rbf, c='g', label='RBF model')
    pl.plot(x_plot, y_lin, c='r', label='Linear model')
    pl.plot(x_plot, y_poly, c='b', label='Polynomial model')
    pl.show()
    
    print "Initializing AlchemyAPI..."
    alchemyapi = AlchemyAPI()
    print "Initialized AlchemyAPI."
    
    ticker = raw_input('Please input a stock ticker: ')
    print "Creating URL"
    url = "http://seekingalpha.com/symbol/%s/transcripts" % ticker
    print "Creating headers..."
    headers =  {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}
    print "Creating request..."
    request = urllib2.Request(url=url, headers=headers)
    print "Opening page..."
    try: page_raw = urllib2.urlopen(request).read()
    except:
        raise Exception('Could not read page_raw!')
    print "Finding transcript match..."
    transcript_url_match = re.search(r'<a href="([^<>]*?)" sasource="qp_transcripts">([^<>]*?)</a>', page_raw, flags=re.S|re.I|re.M)
    if not transcript_url_match:
        raise Exception('Could not find transcript_url_match!')
    else:
        transcript_url = "http://seekingalpha.com%s&page=single" % transcript_url_match.group(1)
    print "creating alchemyapi response..."
    response = alchemyapi.sentiment(flavor='url', data=transcript_url)
    if response['status'] == 'OK':
        print "returned AlchemyAPI object!"
    else:
        print ('Error in sentiment analysis call: ', response['statusInfo'])
    sentiment = float(response['docSentiment']['score'])
    x = "%.2f" % round(sentiment,2)
    beta = svr_rbf.fit(x_plot, y_plot).predict([x])
    print "Predicted volatility: %s" % beta
    #url = raw_input("Please input a transcript URL: ")
    #print "Creating response object..."
    #response = alchemyapi.sentiment(flavor='url', data=url)
    #if response['status'] == 'OK':
    #        print "returned AlchemyAPI object!"
    #else:
    #    print('Error in sentiment analysis call: ', response['statusInfo'])
    #print "Finding sentiment..."
    #sentiment = float(response['docSentiment']['score'])
    #print "Found sentiment! Plotting point..."
    #pdb.set_trace()
    #x = "%.2f" % round(sentiment,2)
    #beta = svr_rbf.fit(x_plot, y_plot).predict([x])
    #print beta