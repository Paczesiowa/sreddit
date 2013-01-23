import os
import unittest
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

from PyRSS2Gen import RSS2, RSSItem, Guid

import cached_feedparser
from cached_feedparser.pickle_history import PickleHistory


def make_rss_item(title='title', link='link',
                  description='description', pubDate=None):
    if pubDate is None:
        pubDate = datetime.now()
    return RSSItem(title=title, link=link, description=description,
                   guid=Guid(link), pubDate=pubDate)


def make_rss_feed(items, title='title', link='link',
                  description='description', lastBuildDate=None):
    if lastBuildDate is None:
        lastBuildDate = datetime.now()
    feed = RSS2(title='title', link='link', description='description',
                lastBuildDate=lastBuildDate, items=items)
    return feed


def _make_rss_feed_in_file(feed_file_path, *args, **kwargs):
    feed = make_rss_feed(*args, **kwargs)
    feed_file = open(feed_file_path, 'w')
    try:
        feed.write_xml(feed_file)
    finally:
        feed_file.close()


class PickleHistoryTest(unittest.TestCase):

    class EntryMock(object):
        def __init__(self, id_, published):
            self.id = id_
            self.published_parsed = published.timetuple()

    def setUp(self):
        tmp_file = NamedTemporaryFile(delete=False)
        self._history_file = tmp_file.name
        tmp_file.close()
        os.remove(self._history_file)

    def tearDown(self):
        try:
            os.remove(self._history_file)
        except:
            pass

    def test_basic_adding(self):
        history = PickleHistory(self._history_file)
        url = 'foo'
        entry1 = PickleHistoryTest.EntryMock(1, datetime.now())
        entry2 = PickleHistoryTest.EntryMock(2, datetime.now())

        self.assertFalse(history.contains(url, entry1))
        self.assertFalse(history.contains(url, entry2))

        history.add_entry(url, entry1)

        self.assertTrue(history.contains(url, entry1))
        self.assertFalse(history.contains(url, entry2))

        history.add_entry(url, entry2)

        self.assertTrue(history.contains(url, entry1))
        self.assertTrue(history.contains(url, entry2))

    def test_saving(self):
        history = PickleHistory(self._history_file)
        url = 'foo'
        entry1 = PickleHistoryTest.EntryMock(1, datetime.now())
        entry2 = PickleHistoryTest.EntryMock(2, datetime.now())

        history.add_entry(url, entry1)
        self.assertTrue(history.contains(url, entry1))
        self.assertFalse(history.contains(url, entry2))

        history.save()
        del history
        history = PickleHistory(self._history_file)

        self.assertTrue(history.contains(url, entry1))
        self.assertFalse(history.contains(url, entry2))

    def test_cleanup(self):
        history_args = {'file_path': self._history_file,
                        'entry_count': 2,
                        'days_to_keep': 30}
        history = PickleHistory(**history_args)
        url = 'foo'

        today = datetime.now()
        last_month = today - timedelta(weeks=4)
        two_months_ago = today - timedelta(weeks=8)

        entry1 = PickleHistoryTest.EntryMock(1, two_months_ago)
        entry2 = PickleHistoryTest.EntryMock(2, last_month)
        entry3 = PickleHistoryTest.EntryMock(3, today)

        history.add_entry(url, entry1)
        history.add_entry(url, entry2)
        self.assertTrue(history.contains(url, entry1))
        self.assertTrue(history.contains(url, entry2))
        self.assertFalse(history.contains(url, entry3))
        history.save()

        del history
        history = PickleHistory(**history_args)

        self.assertTrue(history.contains(url, entry1))
        self.assertTrue(history.contains(url, entry2))
        self.assertFalse(history.contains(url, entry3))

        history.add_entry(url, entry3)

        self.assertTrue(history.contains(url, entry1))
        self.assertTrue(history.contains(url, entry2))
        self.assertTrue(history.contains(url, entry3))

        history.save()

        del history
        history = PickleHistory(**history_args)

        self.assertFalse(history.contains(url, entry1))
        self.assertTrue(history.contains(url, entry2))
        self.assertTrue(history.contains(url, entry3))


class CachedFeedParserTest(unittest.TestCase):

    def setUp(self):
        tmp_file = NamedTemporaryFile(delete=False)
        self._feed_file = tmp_file.name
        tmp_file.close()

        tmp_file = NamedTemporaryFile(delete=False)
        self._history_file = tmp_file.name
        tmp_file.close()
        os.remove(self._history_file)

    def tearDown(self):
        os.remove(self._feed_file)
        try:
            os.remove(self._history_file)
        except:
            pass

    def _get_history(self):
        return PickleHistory(self._history_file)

    def test_basic_parsing(self):
        pubDate1 = datetime(2012, 1, 10)
        item1 = make_rss_item(title='title1', link='link1',
                              pubDate=pubDate1)
        pubDate2 = datetime(2012, 1, 12)
        item2 = make_rss_item(title='title2', link='link2',
                              pubDate=pubDate2)
        _make_rss_feed_in_file(self._feed_file, [item1, item2])

        parser = cached_feedparser.CachedFeedParser(self._get_history())
        entries = parser.parse_entries(self._feed_file)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].id, 'link1')
        self.assertEqual(entries[0].link, 'link1')
        self.assertEqual(entries[0].title, 'title1')
        self.assertEqual(datetime(*entries[0].published_parsed[:6]), pubDate1)
        self.assertEqual(entries[1].id, 'link2')
        self.assertEqual(entries[1].link, 'link2')
        self.assertEqual(entries[1].title, 'title2')
        self.assertEqual(datetime(*entries[1].published_parsed[:6]), pubDate2)

    def test_not_returning_old_entries_same_instance(self):
        pubDate1 = datetime(2012, 1, 10)
        item1 = make_rss_item(title='title1', link='link1',
                              pubDate=pubDate1)
        pubDate2 = datetime(2012, 1, 11)
        item2 = make_rss_item(title='title2', link='link2',
                              pubDate=pubDate2)
        pubDate3 = datetime(2012, 1, 12)
        item3 = make_rss_item(title='title3', link='link3',
                              pubDate=pubDate3)

        _make_rss_feed_in_file(self._feed_file, [item1, item2])

        parser = cached_feedparser.CachedFeedParser(self._get_history())

        entries = parser.parse_entries(self._feed_file)
        self.assertEqual(len(entries), 2)

        _make_rss_feed_in_file(self._feed_file, [item1, item2, item3])
        entries = parser.parse_entries(self._feed_file)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, 'link3')
        self.assertEqual(entries[0].link, 'link3')
        self.assertEqual(entries[0].title, 'title3')
        self.assertEqual(datetime(*entries[0].published_parsed[:6]), pubDate3)

    def test_not_returning_old_entries_new_instance(self):
        pubDate1 = datetime(2012, 1, 10)
        item1 = make_rss_item(title='title1', link='link1',
                              pubDate=pubDate1)
        pubDate2 = datetime(2012, 1, 11)
        item2 = make_rss_item(title='title2', link='link2',
                              pubDate=pubDate2)
        pubDate3 = datetime(2012, 1, 12)
        item3 = make_rss_item(title='title3', link='link3',
                              pubDate=pubDate3)

        _make_rss_feed_in_file(self._feed_file, [item1, item2])

        parser = cached_feedparser.CachedFeedParser(self._get_history())

        entries = parser.parse_entries(self._feed_file)
        self.assertEqual(len(entries), 2)

        _make_rss_feed_in_file(self._feed_file, [item1, item2, item3])

        parser = cached_feedparser.CachedFeedParser(self._get_history())

        entries = parser.parse_entries(self._feed_file)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, 'link3')
        self.assertEqual(entries[0].link, 'link3')
        self.assertEqual(entries[0].title, 'title3')
        self.assertEqual(datetime(*entries[0].published_parsed[:6]), pubDate3)
