import unittest
import aiohttp
import asyncio
import os
from http import HTTPStatus
from dotenv import load_dotenv
load_dotenv()


class TestEndpoints(unittest.TestCase):
    """Test cases for verifying different language endpoints."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        cls.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        cls.loop = asyncio.get_event_loop()
        cls.session = aiohttp.ClientSession(loop=cls.loop)

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        cls.loop.run_until_complete(cls.session.close())

    def test_verb_conjugation_endpoint_one(self):
        """ Tess the Reverso Conjugator's conjugation endpoint. """

        test_verb = "falar"
        url = f"https://conjugator.reverso.net/conjugation-portuguese-verb-{test_verb}.html"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_verb_conjugation_endpoint_two(self):
        """ Test the Cooljugator's conjugation endpoint. """

        test_verb = "åka"
        url = f"https://cooljugator.com/sv/{test_verb}"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_verb_conjugation_endpoint_three(self):
        """ Test the Mijnwoordenboek's conjugation endpoint. """

        test_verb = "praten"
        url = f"https://www.mijnwoordenboek.nl/werkwoord/{test_verb}"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_dictionary_endpoint(self):
        """ Test the Cambridge Dictionary's dictionary endpoint."""

        test_word = "hello"
        url = f"https://dictionary.cambridge.org/us/dictionary/english/{test_word}"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_dictionary_endpoint_two(self):
        """ Test the DicoLink's dictionary endpoint. """

        test_word = "bonjour"
        url = f"https://dicolink.p.rapidapi.com/mot/{test_word}/definitions"
        token = os.getenv("RAPID_API_TOKEN")
        if not token:
            self.skipTest("RAPID_API_TOKEN environment variable not set")
        headers = {**self.headers, "x-rapidapi-key": token,
                   "x-rapidapi-host": "dicolink.p.rapidapi.com"}
        response = self.loop.run_until_complete(self.session.get(url, headers=headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_declension_endpoint(self):
        """ Test the Declinator's declension endpoint. """

        test_word = "kot"
        url = f"https://www.api.declinator.com/api/v2/declinator/pl?unit={test_word}"
        token = os.getenv("DECLINATOR_API_TOKEN")
        if not token:
            self.skipTest("DECLINATOR_API_TOKEN environment variable not set")
        headers = {**self.headers, "Authorization": token}
        response = self.loop.run_until_complete(self.session.get(url, headers=headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_declension_endpoint_two(self):
        """ Test the Netzverb's declension endpoint. """

        test_word = "essen"
        root = "https://www.verbformen.com/declension/nouns"
        url = f"{root}/?w={test_word}"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)

    def test_declension_endpoint_three(self):
        """ Test the OpenRussian's declension endpoint. """

        test_word = "работать"
        url = f"https://en.openrussian.org/ru/{test_word}"
        response = self.loop.run_until_complete(self.session.get(url, headers=self.headers))
        self.assertEqual(response.status, HTTPStatus.OK)
