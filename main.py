from crawler import Crawler
import re
import json

target = raw_input("Press enter to begin...")

print "Updating database..."
target_list = open("list.txt")
targets = target_list.readlines()
for target in targets:
    print "Starting crawler for %s..." % target
    target = target.replace('\n', '')
    try: int(target)
    except: c = Crawler(target)
    r = Crawler(target)


