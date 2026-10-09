# Movie Recommender

This Python program runs in the terminal and suggests up to five movies from TMDB. You choose a genre, optional styles and countries, a release-year range, and a rating range.

For each movie, it shows the title, rating, genres, production countries, release date, and overview when available. If you select styles, it also shows which ones match the movie's TMDB keywords.

## Install on Windows

Tested with Python 3.14.8 using a separate virtual environment: dependency installation, `pip check`, and all 24 simulated regression tests passed. Compatibility with other Python versions has not been verified. Install Python with the Windows Python launcher.

To clone the project, you need Git installed. Run:

```powershell
git clone https://github.com/MatheusMartins-Data/Movie-Recommender.git
cd Movie-Recommender
```

Alternatively, select **Code > Download ZIP** on GitHub, extract the ZIP, and open a terminal in the extracted folder.

From the project folder, create the virtual environment and install the dependencies:

```powershell
py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you already have a working `.venv`, skip the first command. These commands use its Python interpreter directly, so you do not need to activate it.

The program uses `requests` to call TMDB and `python-dotenv` to load the token from `.env`. Dependency versions are not pinned.

## Set up the TMDB token

Get an API Read Access Token from your TMDB account's API settings. Use the token itself, without the `Bearer ` prefix.

If you do not have a `.env` file, copy the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and replace the placeholder:

```dotenv
TMDB_TOKEN=your_tmdb_api_read_access_token_here
```

You can also set `TMDB_TOKEN` as an environment variable. An existing environment value takes priority over `.env`. If the token is missing or contains only spaces, the program stops before asking for your choices.

Keep your token private. The project's `.gitignore` excludes `.env`.

## Run

From the project folder, run:

```powershell
& .\.venv\Scripts\python.exe .\app.py
```

You need an internet connection and a valid TMDB token.

Choose menu options by number. Enter `0` when you finish selecting styles or countries. Invalid input repeats the question. Selected styles and countries are kept. A valid start year or minimum rating is kept while you correct the end year or maximum rating.

## How the search works

| Filter | What it does |
| --- | --- |
| Genre | Choose one main genre. Every recommendation must match it, including in Broad mode. |
| Styles / keywords | Choose up to five different styles. Each style is a TMDB keyword. Repeated choices are ignored. You can leave this filter empty. |
| Countries | Choose any number of countries. A movie can match any one of them. Leave this filter empty to search all countries. The search uses origin countries; the results display production countries. |
| Release years | Include both the start and end years. Years must be between 1888 and the current year. The start year cannot be after the end year. The search uses primary release dates. |
| Rating | Set a minimum and maximum TMDB average rating between 0 and 10. Both limits are included. The minimum cannot be higher than the maximum. Values such as `nan` and `inf` are rejected. |

The program does not filter or select movies by vote count. The selected rating range still applies. TMDB searches are ordered by popularity, from highest to lowest, and request movie information in English (`en-US`).

### Broad and Strict

With two or more styles, you choose a matching mode:

- **Broad:** a movie must match at least one selected style. The program searches for all selected styles together and also searches for each style separately. It first tries to pick one movie for each style. It then takes turns adding movies from each style's results and the combined search until it has up to five movies. Duplicate movies are removed. The main genre and all other filters stay the same. Styles with no results may remain unrepresented. Filters are never relaxed to fill five slots.
- **Strict:** a movie must match every selected style. The program shows up to five movies in the order returned by TMDB.

For example, selecting `slasher` and `vampire` in Broad mode allows movies with either keyword. Strict requires both keywords on the same movie.

With one style, that style is required and the program skips the mode question. With no styles, it applies no keyword filter.

In Broad mode, the program visits styles in the order you selected them. Changing that order can change both the movies chosen and their order. The final list may differ from TMDB's popularity order.

`Movies found` shows the total reported by the initial TMDB search. It is not the number of recommendations displayed. The program can show fewer than five movies. If there are no matches, it suggests using broader filters.

## Usage example

Illustrative only; this was not run against TMDB. Menu lists and selection confirmations are omitted. Bracketed values show where TMDB data would appear, not real movie data.

```text
Choose the genre number: 12
Choose the style/keyword number: 1
Choose the style/keyword number: 2
Choose the style/keyword number: 0
Choose the matching mode number: 1
Choose the origin country number: 0
What is the start year? 1980
What is the end year? 2020
What is the minimum rating? 6
What is the maximum rating? 9

Movies found: [total from the initial search]

=== RECOMMENDED MOVIES ===

1. [movie title]
   Rating: [TMDB average rating]
   Genres: [genres, including Horror]
   Production countries: [production countries]
   Matched styles: [Slasher, Vampire, or both]
   Release date: [Month DD, YYYY]
   Overview: [overview omitted]

--------------------------------------------------
```

## Tests

Run the tests from the project folder:

```powershell
& .\.venv\Scripts\python.exe .\test_app_regression.py
```

The suite contains 24 regression tests with simulated responses. It replaces HTTP requests, token loading, environment access, and user input before importing the application. It does not read `.env`, use real credentials, or contact TMDB.

The tests cover request errors, response validation, missing movie information, dates, rating and year limits, filters, Broad and Strict matching, duplicate choices, movie-details caching, empty results, and lists with fewer than five movies. They do not check whether TMDB is currently available or whether a real token works.

You can also check Python syntax without launching the program:

```powershell
& .\.venv\Scripts\python.exe -m py_compile app.py test_app_regression.py
```

## Limitations

- Only the first Discover page from each search is used. There is no search through later pages, so the program may show fewer than five movies even when more matches exist.
- Broad mode cannot guarantee a different movie for every style. Some styles may have no results, and movies may match more than one style.
- Genre, style, and country menus are defined in the code. Results and matched-style labels depend on TMDB's information and keyword coverage.
- Recommendations use the selected filters and popularity. The program does not use viewing history or save preferences.
- Each request has a 10-second timeout and is not retried automatically. Connection errors, unsuccessful responses, invalid JSON, or invalid required fields stop the program with an error message. A failed movie-details request also stops the program.
- Some movie information may be unavailable.
- Dependency versions are not pinned. Other Python versions have not been verified.
