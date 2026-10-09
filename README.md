# Movie Recommender

A Python command-line application that recommends up to five movies using TMDB Discover. Choose a genre, optional styles/keywords and countries, a release-year range, and a rating range. Recommendations include ratings, vote counts, genres, production countries, matched styles, release dates, and overviews when available.

## Windows installation

Install Python 3 with the Windows Python launcher available. Open PowerShell in the project folder, then create a virtual environment and install the dependencies:

```powershell
py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the project already has a working `.venv`, skip its creation. These commands use the environment's interpreter explicitly, so activation is optional.

The external dependencies are `requests` and `python-dotenv`. Other application imports (`os`, `math`, and `datetime`) belong to the Python standard library. Dependency versions are not pinned.

## TMDB token configuration

Obtain an API Read Access Token from your TMDB account's API settings. The application sends this token as a Bearer token; enter the token itself without a `Bearer ` prefix.

If you do not already have a `.env` file, create one from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and replace the placeholder:

```dotenv
TMDB_TOKEN=your_tmdb_api_read_access_token_here
```

Alternatively, set `TMDB_TOKEN` in your process environment. An existing environment value takes precedence over `.env`. Missing or whitespace-only tokens cause the application to stop before asking for selections. Keep real tokens private; `.env` is excluded by `.gitignore`.

## Run

From the project folder:

```powershell
& .\.venv\Scripts\python.exe .\app.py
```

Choose options by their displayed numbers. Enter `0` to finish selecting styles or countries. Normal application use requires an internet connection and a valid TMDB token.

## Filters and matching

| Filter | Behavior |
| --- | --- |
| Genre | Select one genre from the built-in list. |
| Styles / keywords | Select zero to five distinct keywords. Repeated selections are ignored. |
| Country | Select zero or more distinct countries. Multiple countries use OR matching; no selection leaves this filter unrestricted. The query filters origin countries; displayed countries come from production metadata. |
| Release years | Inclusive primary release dates, from January 1 of the start year through December 31 of the end year. Years must be between 1888 and the current year, in ascending order. |
| Rating | Inclusive TMDB average rating between 0 and 10. Both limits must be finite and the minimum cannot exceed the maximum. |
| Vote count | Always requires at least 100 votes. |
| Ordering and language | Discover searches request descending popularity and English (`en-US`) metadata. |

With two or more styles, choose a matching mode:

- **Broad:** requests movies matching at least one selected keyword. It also searches each keyword separately with the same genre, country, year, rating, and vote-count filters. Selection gives each style a turn, then fills remaining slots from the style pools and the general Broad results, removing duplicate movie IDs. The final list can differ from overall popularity order.
- **Strict:** requests movies matching every selected keyword and displays up to five results in Discover order.

With one keyword, that keyword is required and the mode prompt is skipped. With no keywords, there is no keyword filter. Broad and Strict only affect keyword matching; other filters remain in place.

In Broad mode, styles are visited in the order you selected them. Changing that order can change the recommendation order and which movies fill the five available slots. Only the first Discover page from each search is considered.

`Movies found` reports the total from the initial Discover response, not the number of recommendations displayed. Fewer than five recommendations are valid. Empty results produce a message suggesting broader criteria.

## Regression tests

Run the standalone unittest suite from the project folder:

```powershell
& .\.venv\Scripts\python.exe .\test_app_regression.py
```

The suite installs simulated dotenv, environment, HTTP, and input boundaries before importing `app.py`. It does not read `.env`, use real credentials, make HTTP requests, or require interactive input. It covers API failures, Discover field validation, malformed optional metadata, dates, rating and year boundaries, filter preservation, Broad/Strict behavior, duplicates, caching, empty results, and short recommendation lists.

The latest manual verification reported **21 tests passed**. These are offline regression tests; they do not verify current TMDB availability or real credentials.

An optional syntax check, which does not launch the application:

```powershell
& .\.venv\Scripts\python.exe -m py_compile app.py test_app_regression.py
```

## Known limitations

- Only the first Discover page of each search is used; the application does not paginate. It can show fewer than five movies even when more exist on later pages.
- Broad mode balances available keyword pools but cannot guarantee a separate movie for every style. Movies may match multiple styles, and pools may be empty or overlap.
- Genre, keyword, and country choices are built-in mappings. Results and matched-style labels depend on TMDB's metadata and keyword coverage.
- Recommendations are based on filters and popularity, without viewing history, saved preferences, or personalization.
- Invalid menu or range input generally ends the program; restart it to try again.
- Requests use a 10-second timeout with no automatic retries. Connection errors, non-200 responses, invalid JSON, and invalid required response fields stop the run with an error message.
- Optional metadata can be unavailable. A failed movie-details request stops the run rather than skipping that movie.
- Dependencies are unpinned, and no Python version compatibility matrix has been established.
