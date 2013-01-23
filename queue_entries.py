#!/usr/bin/env python
import sys
import yaml

import beanstalkc

from cached_feedparser import CachedFeedParser
from cached_feedparser.pickle_history import PickleHistory


def main():
    try:
        cfg_file = sys.argv[1]
    except IndexError:
        print ' '.join(['usage:', sys.argv[0], 'CONFIG_FILE_PATH'])
        sys.exit(1)
    else:
        history = PickleHistory('feed_history.dat')
        feed_parser = CachedFeedParser(history)
        beanstalk = beanstalkc.Connection()

        feeds = []
        with open(cfg_file) as f:
            feeds = f.readlines()

        for feed in feeds:
            print 'Processing ' + feed
            entries = feed_parser.parse_entries(feed)
            print 'Found ' + str(len(entries)) + ' new entries'
            for entry in entries:
                beanstalk.put(yaml.dump(entry))

if __name__ == '__main__':
    main()
