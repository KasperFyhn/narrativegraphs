import unittest

from narrativegraphs.nlp.mapping.linguistic import StemmingMapper


class TestStemmingMapper(unittest.TestCase):
    def test_initialization(self):
        # No-brainer test on local environments where NLTK data has been downloaded
        # already, but CI will catch errors if the NLTK models are not auto-downloaded
        mapper = StemmingMapper()
        mapper.create_mapping(["test", "test test"])
