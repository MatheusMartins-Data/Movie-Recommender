"""Offline regression suite. Run directly with the project's Python interpreter."""

import importlib.util
import io
import os
from pathlib import Path
import sys
import types
import unittest
from contextlib import ExitStack, redirect_stdout
from unittest.mock import Mock, patch


class RequestException(Exception):
    pass


class Timeout(RequestException):
    pass


def movie(movie_id=1, **changes):
    result = {"id": movie_id, "title": f"Movie {movie_id}",
              "vote_average": 7.5}
    result.update(changes)
    return result


def response(payload=None, status=200, json_error=None):
    result = Mock(status_code=status)
    if json_error is not None:
        result.json.side_effect = json_error
    else:
        result.json.return_value = payload
    return result


class AppRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Install harmless replacement modules BEFORE executing any app source.
        # No requests/dotenv dependency is imported, and no real token is read.
        cls.boundaries = ExitStack()
        cls.addClassCleanup(cls.boundaries.close)
        cls.http = types.ModuleType("requests")
        cls.http.get = Mock(side_effect=AssertionError("Unsimulated HTTP call"))
        cls.http.exceptions = types.SimpleNamespace(
            RequestException=RequestException, Timeout=Timeout)
        cls.dotenv = types.ModuleType("dotenv")
        cls.dotenv.load_dotenv = Mock(return_value=False)
        cls.boundaries.enter_context(patch.dict(
            sys.modules, {"requests": cls.http, "dotenv": cls.dotenv}))
        cls.boundaries.enter_context(patch.dict(os.environ, {}, clear=True))
        cls.boundaries.enter_context(patch(
            "os.getenv", return_value=None))
        cls.blocked_input = cls.boundaries.enter_context(patch(
            "builtins.input", side_effect=AssertionError("Unexpected prompt")))
        spec = importlib.util.spec_from_file_location(
            "movie_app_under_test", Path(__file__).with_name("app.py"))
        cls.app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.app)
        cls.blocked_input.assert_not_called()
        cls.http.get.assert_not_called()

    def setUp(self):
        self.http.get.reset_mock(return_value=True, side_effect=True)
        self.http.get.side_effect = AssertionError("Unsimulated HTTP call")
        self.output = io.StringIO()
        self.capture = redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def rejects(self, operation, message):
        self.output.seek(0)
        self.output.truncate()
        with self.assertRaises(SystemExit) as caught:
            operation()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn(message, self.output.getvalue())

    def discover(self, payload):
        self.http.get.side_effect = None
        self.http.get.return_value = response(payload)
        return self.app.search_movies({})

    def parameters(self, mode="broad", styles=None, countries=None):
        return self.app.build_parameters(
            "horror", ["slasher", "vampire"] if styles is None else styles,
            ["BR", "JP"] if countries is None else countries,
            1980, 2020, 6, 9, mode)

    def test_import_has_no_external_or_interactive_effects(self):
        self.assertEqual(self.app.tmdb_token, "")
        self.assertEqual(self.app.headers["Authorization"], "Bearer ")
        self.dotenv.load_dotenv.assert_called_once_with()
        self.blocked_input.assert_not_called()
        self.http.get.assert_not_called()

    def test_missing_and_blank_token_fail_before_prompt_or_http(self):
        for token in ("", "   ".strip()):
            with self.subTest(token=repr(token)), patch.object(self.app, "tmdb_token", token):
                self.rejects(self.app.main, "TMDB_TOKEN is missing or blank")
        self.http.get.assert_not_called()
        self.blocked_input.assert_not_called()

    def test_transport_failures_are_explicit(self):
        for error, message in ((Timeout(), "timed out"),
                               (RequestException(), "Could not connect")):
            with self.subTest(error=type(error).__name__):
                self.http.get.side_effect = error
                self.rejects(lambda: self.app.search_movies({}), message)

    def test_http_status_json_and_response_object_errors(self):
        cases = [(response({}, status=401), "Status code: 401"),
                 (response({}, status=500), "Status code: 500"),
                 (response(json_error=ValueError("bad JSON")), "invalid JSON")]
        cases.extend((response(value), "invalid response object")
                     for value in (None, [], "text", 3, True))
        for simulated, message in cases:
            with self.subTest(message=message):
                self.http.get.side_effect = None
                self.http.get.return_value = simulated
                self.rejects(lambda: self.app.search_movies({}), message)

    def test_discover_required_fields_missing(self):
        for field in ("id", "title", "vote_average"):
            with self.subTest(field=field):
                item = movie()
                del item[field]
                self.rejects(lambda: self.discover(
                    {"results": [item], "total_results": 1}), "invalid Discover results")

    def test_discover_required_fields_invalid(self):
        invalid = {
            "id": [None, True, False, 0, -1, 1.0, "1"],
            "title": [None, "", " \t\n", 4, True, []],
            "vote_average": [None, True, False, "7", [], -0.1, 10.1,
                             float("nan"), float("inf"), -float("inf"), 10**400],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=repr(value)):
                    self.rejects(lambda: self.discover({
                        "results": [movie(**{field: value})], "total_results": 1}),
                        "invalid Discover results")

    def test_discover_container_and_total_validation(self):
        cases = [{}, {"results": [], "total_results": True},
                 {"results": [], "total_results": -1},
                 {"results": [], "total_results": 1.0},
                 {"results": [], "total_results": "0"},
                 {"results": [], "total_results": None}]
        cases.extend({"results": value, "total_results": 0}
                     for value in (None, {}, "", [None], [True], [[]]))
        for payload in cases:
            with self.subTest(payload=payload):
                self.rejects(lambda: self.discover(payload), "invalid Discover results")

    def test_valid_discover_boundaries_and_empty_results(self):
        # Vote count is unused: absent and malformed values must be accepted.
        for item in [movie()] + [movie(vote_count=value) for value in
                                (None, True, False, -1, 1.5, "bad", [], {})]:
            with self.subTest(item=item):
                payload = {"results": [item], "total_results": 1}
                self.assertEqual(self.discover(payload), payload)
        for rating in (0, 0.0, 7, 7.5, 10, 10.0):
            with self.subTest(rating=rating):
                payload = {"results": [movie(title=" Valid ", vote_average=rating,
                                             vote_count=0)], "total_results": 1}
                self.assertEqual(self.discover(payload), payload)
        self.assertEqual(self.discover({"results": [], "total_results": 0}),
                         {"results": [], "total_results": 0})

    def test_filters_and_broad_strict_keyword_encoding(self):
        expected = {"with_genres": 27, "primary_release_date.gte": "1980-01-01",
                    "primary_release_date.lte": "2020-12-31",
                    "vote_average.gte": 6, "vote_average.lte": 9,
                    "sort_by": "popularity.desc",
                    "language": "en-US", "with_origin_country": "BR|JP"}
        for mode, keywords in (("broad", "12339|3133"), ("strict", "12339,3133")):
            with self.subTest(mode=mode):
                params = self.parameters(mode)
                self.assertNotIn("vote_count.gte", params)
                self.assertEqual(params, dict(expected, with_keywords=keywords))
                self.http.get.side_effect = None
                self.http.get.return_value = response({"results": [], "total_results": 0})
                self.app.search_movies(params)
                self.http.get.assert_called_with(
                    self.app.url, params=params, headers=self.app.headers, timeout=10)
        params = self.parameters(styles=[], countries=[])
        self.assertNotIn("with_keywords", params)
        self.assertNotIn("with_origin_country", params)

    def test_broad_balances_styles_deduplicates_and_preserves_filters(self):
        params = self.parameters()
        original = params.copy()
        pools = {"12339": [movie(1), movie(1), movie(2), movie(3)],
                 "3133": [movie(1), movie(4), movie(5)]}
        calls = []

        def simulated_get(url, *, params, headers, timeout):
            calls.append(params.copy())
            items = pools[params["with_keywords"]]
            return response({"results": items, "total_results": len(items)})

        self.http.get.side_effect = simulated_get
        selected = self.app.select_broad_movies(params, ["slasher", "vampire"],
                                                 [movie(1), movie(6), movie(7)])
        ids = [item["id"] for item in selected]
        self.assertEqual(ids[:2], [1, 4])
        self.assertEqual(len(ids), 5)
        self.assertEqual(len(set(ids)), 5)
        self.assertIn(6, ids)
        self.assertEqual(params, original)
        self.assertEqual(len(calls), 2)
        for sent in calls:
            self.assertNotIn("vote_count.gte", sent)
            self.assertEqual(sent["vote_average.gte"], 6)
            self.assertEqual(sent["vote_average.lte"], 9)
            self.assertEqual({k: v for k, v in sent.items() if k != "with_keywords"},
                             {k: v for k, v in original.items() if k != "with_keywords"})

    def test_broad_empty_and_fewer_than_five_unique_movies(self):
        for pools, candidates, expected in (
            ([[], []], [], []),
            ([[movie(1), movie(1)], [movie(1), movie(2)]],
             [movie(2), movie(3)], [1, 2, 3]),
        ):
            with self.subTest(expected=expected):
                self.http.get.side_effect = [response({"results": pool,
                    "total_results": len(pool)}) for pool in pools]
                selected = self.app.select_broad_movies(
                    self.parameters(), ["slasher", "vampire"], candidates)
                self.assertEqual([item["id"] for item in selected], expected)

    def test_details_id_validation_and_request(self):
        for payload in ({}, {"id": True}, {"id": "1"}, {"id": 2}, {"id": 1.0}):
            with self.subTest(payload=payload):
                self.http.get.side_effect = None
                self.http.get.return_value = response(payload)
                self.rejects(lambda: self.app.get_movie_details(1), "invalid movie details ID")
        self.http.get.return_value = response({"id": 1})
        self.assertEqual(self.app.get_movie_details(1), {"id": 1})
        self.http.get.assert_called_with(
            "https://api.themoviedb.org/3/movie/1",
            params={"language": "en-US", "append_to_response": "keywords"},
            headers=self.app.headers, timeout=10)

    def test_malformed_keywords_are_safe_and_valid_matches_survive(self):
        for keywords in (None, [], "bad", {}, {"keywords": None}, {"keywords": {}},
                         {"keywords": [None, {}, {"id": True}, {"id": "12339"}]}):
            with self.subTest(keywords=keywords):
                self.assertEqual(self.app.get_matched_styles(
                    {"keywords": keywords}, ["slasher"]), [])
        self.assertEqual(self.app.get_matched_styles({"keywords": {"keywords": [
            None, {"id": 12339}, {"id": 12339}, {"id": 3133}, {"id": -1}]}},
            ["slasher", "vampire"]), ["Slasher", "Vampire"])

    def test_optional_display_fields_fall_back_safely(self):
        for bad in (None, "bad", {}, [], [None], [{"name": None}], [{"name": " "}]):
            with self.subTest(value=bad):
                self.output.seek(0)
                self.output.truncate()
                self.app.display_movies([movie(release_date=bad)], ["slasher"],
                    {1: {"genres": bad, "production_countries": bad, "keywords": bad}})
                output = self.output.getvalue()
                for label in ("Genres", "Production countries", "Matched styles", "Release date", "Overview"):
                    self.assertIn(f"{label}: Not available.", output)

    def test_valid_display_date_metadata_and_details_cache(self):
        self.http.get.side_effect = None
        self.http.get.return_value = response({"id": 1,
            "genres": [{"name": " Horror "}],
            "production_countries": [None, {"name": " Brazil "}],
            "keywords": {"keywords": [{"id": 12339}]}})
        cache = {}
        item = movie(release_date="2000-02-29", overview="A story.")
        self.app.display_movies([item], ["slasher"], cache)
        self.app.display_movies([item], ["slasher"], cache)
        self.http.get.assert_called_once()
        self.assertNotIn("Vote count:", self.output.getvalue())
        for text in ("1. Movie 1", "Rating: 7.5", "Genres: Horror",
                     "Production countries: Brazil", "Matched styles: Slasher",
                     "Release date: February 29, 2000", "Overview: A story."):
            self.assertIn(text, self.output.getvalue())

    def test_invalid_calendar_dates_fall_back(self):
        for date in ("2023-02-29", "2020-13-01", "", 123, True):
            with self.subTest(date=date):
                self.output.seek(0)
                self.output.truncate()
                self.app.display_movies([movie(release_date=date)], [], {1: {}})
                self.assertIn("Release date: Not available.", self.output.getvalue())

    def test_display_empty_short_and_maximum_lists(self):
        self.app.display_movies([], [], {})
        self.assertIn("No movies matched", self.output.getvalue())
        for count in (2, 7):
            with self.subTest(count=count):
                self.output.seek(0)
                self.output.truncate()
                self.app.display_movies([movie(i) for i in range(1, count + 1)], [],
                                        {i: {} for i in range(1, count + 1)})
                self.assertEqual(self.output.getvalue().count("Rating:"), min(count, 5))
                self.assertNotIn("Vote count:", self.output.getvalue())
        self.http.get.assert_not_called()

    def test_rating_input_recovers_and_preserves_valid_minimum(self):
        cases = (
            (["bad", "nan", "-inf", "-1", "11", "0", "10"], (0.0, 10.0)),
            (["6", "bad", "inf", "nan", "-1", "11", "5", "8"], (6.0, 8.0)),
        )
        for inputs, expected in cases:
            with self.subTest(inputs=inputs), patch("builtins.input", side_effect=inputs) as prompt:
                self.assertEqual(self.app.choose_rating_range(), expected)
                self.assertEqual(prompt.call_count, len(inputs))
        self.assertIn("Ratings must be between 0 and 10", self.output.getvalue())
        self.assertIn("minimum rating cannot be greater", self.output.getvalue())
    def test_strict_flow_preserves_discover_order_without_style_searches(self):
        # Exercise orchestration with every interactive boundary replaced.
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.app, "tmdb_token", "offline-placeholder"))
            for name, value in (
                ("choose_genre", "horror"),
                ("choose_keyword", ["slasher", "vampire"]),
                ("choose_keyword_match_mode", "strict"),
                ("choose_country", ["BR", "JP"]),
                ("choose_year_range", (1980, 2020)),
                ("choose_rating_range", (6, 9)),
            ):
                stack.enter_context(patch.object(self.app, name, return_value=value))
            broad = stack.enter_context(patch.object(
                self.app, "select_broad_movies", side_effect=AssertionError("Unexpected Broad search")))
            self.http.get.side_effect = [
                response({"results": [movie(9), movie(2)], "total_results": 2}),
                response({"id": 9}), response({"id": 2})]
            self.app.main()
        broad.assert_not_called()
        output = self.output.getvalue()
        self.assertLess(output.index("1. Movie 9"), output.index("2. Movie 2"))
        self.assertIn("Movies found: 2", output)
        self.assertEqual(self.http.get.call_count, 3)
        self.assertEqual(self.http.get.call_args_list[0].kwargs["params"],
                         self.parameters("strict"))

    def test_duplicate_style_and_country_choices_are_not_repeated(self):
        with patch("builtins.input", side_effect=["1", "1", "2", "0"]):
            self.assertEqual(self.app.choose_keyword(), ["slasher", "vampire"])
        self.assertIn("already selected", self.output.getvalue())
        with patch("builtins.input", side_effect=["1", "1", "2", "0"]):
            self.assertEqual(self.app.choose_country(), ["AR", "AU"])

    def test_year_limits_and_reversed_ranges(self):
        with patch("builtins.input", side_effect=["1888", str(self.app.ano_atual)]):
            self.assertEqual(self.app.choose_year_range(), (1888, self.app.ano_atual))
        inputs = ["bad", "1887", str(self.app.ano_atual + 1), "2001",
                  "bad", "1887", str(self.app.ano_atual + 1), "2000", "2020"]
        with patch("builtins.input", side_effect=inputs) as prompt:
            self.assertEqual(self.app.choose_year_range(), (2001, 2020))
        self.assertEqual(prompt.call_count, len(inputs))
        self.assertEqual(prompt.call_args_list[-1].args, ("What is the end year? ",))
        self.assertIn("cannot be greater", self.output.getvalue())

    def test_genre_and_matching_mode_recover_from_invalid_input(self):
        cases = (
            (self.app.choose_genre, ["bad", "0", "999", "12"], "horror"),
            (self.app.choose_keyword_match_mode, ["bad", "0", "3", "1"], "broad"),
            (self.app.choose_keyword_match_mode, ["-1", "2"], "strict"),
        )
        for operation, inputs, expected in cases:
            with self.subTest(operation=operation.__name__), patch("builtins.input", side_effect=inputs) as prompt:
                self.assertEqual(operation(), expected)
                self.assertEqual(prompt.call_count, len(inputs))

    def test_style_and_country_recovery_keeps_selections(self):
        cases = (
            (self.app.choose_keyword, ["slasher", "vampire"]),
            (self.app.choose_country, ["AR", "AU"]),
        )
        for operation, expected in cases:
            inputs = ["1", "bad", "-1", "999", "1", "2", "0"]
            with self.subTest(operation=operation.__name__), patch("builtins.input", side_effect=inputs) as prompt:
                self.assertEqual(operation(), expected)
                self.assertEqual(prompt.call_count, len(inputs))

    def test_five_unique_styles_finish_without_another_prompt(self):
        inputs = ["1", "1", "bad", "2", "3", "4", "5"]
        with patch("builtins.input", side_effect=inputs) as prompt:
            self.assertEqual(self.app.choose_keyword(), list(self.app.subgeneros)[:5])
            self.assertEqual(prompt.call_count, len(inputs))
        self.assertIn("Maximum of 5", self.output.getvalue())

if __name__ == "__main__":
    unittest.main(verbosity=2)
