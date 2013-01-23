import unittest

import feedparser

from cached_feedparser.tests import make_rss_item, make_rss_feed
from entry_json import entry_from_json, entry_to_json


class EntryJSONTest(unittest.TestCase):

    def test_idempotence(self):
        item = make_rss_item()
        feed_string = make_rss_feed([item]).to_xml()
        feed = feedparser.parse(feed_string)
        entry = feed.entries[0]
        self.maxDiff = None
        from ipdb import set_trace; set_trace()
        self.assertEqual(dict(entry), entry_from_json(entry_to_json(entry)))
