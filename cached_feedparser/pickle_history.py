import errno
import pickle
from datetime import datetime


class PickleHistory(object):

    def __init__(self, file_path, entry_count=50, days_to_keep=30):
        '''
        Simple dictionary (pickled to a file).
        Entries are deleted from history, when there are more entries
        (per url/feed) than entry_count. Only entries older
        than days_to_keep are deleted.
        '''
        self._entry_count = entry_count
        self._days_to_keep = days_to_keep
        self._file_path = file_path
        try:
            with open(file_path) as f:
                self._history = pickle.load(f)
        except IOError as e:
            if e.errno == errno.ENOENT:
                self._history = {}
            else:
                raise
        self._clean_history()

    def _clean_history(self):
        today = datetime.now()
        for feed, feed_history in self._history.iteritems():
            if len(feed_history) > self._entry_count:
                new_feed_history = \
                    {id_: pub_date
                     for id_, pub_date in feed_history.iteritems()
                     if (today - pub_date).days <= self._days_to_keep}
                self._history[feed] = new_feed_history

    def contains(self, url, entry):
        feed_history = self._history.get(url)
        if feed_history is None:
            return False
        else:
            return entry.id in feed_history

    def add_entry(self, url, entry):
        feed_history = self._history.get(url)
        if feed_history is None:
            feed_history = {}
            self._history[url] = feed_history
        feed_history[entry.id] = datetime(*entry.published_parsed[:6])

    def save(self):
        with open(self._file_path, 'w') as f:
            pickle.dump(self._history, f)
