import feedparser


class CachedFeedParser(object):

    def __init__(self, history):
        self._history = history

    def parse_entries(self, url, *args, **kwargs):
        feed = feedparser.parse(url, *args, **kwargs)
        entries = feed.entries
        new_entries = [entry for entry in entries
                       if self._is_new_entry(url, entry)]
        self._add_entries(url, new_entries)
        return new_entries

    def _is_new_entry(self, url, entry):
        return not self._history.contains(url, entry)

    def _add_entries(self, url, entries):
        for entry in entries:
            self._history.add_entry(url, entry)

        self._history.save()
