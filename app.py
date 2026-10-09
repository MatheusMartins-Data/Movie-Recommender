import os
import math
import requests
from dotenv import load_dotenv
from datetime import datetime

MIN_MOVIE_YEAR = 1888
MAX_RECOMMENDATIONS = 5

ano_atual = datetime.now().year

load_dotenv()

tmdb_token = (os.getenv("TMDB_TOKEN") or "").strip()

generos = {
   "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "science fiction": 878,
    "history": 36,
    "horror": 27,
    "mystery": 9648,
    "music": 10402,
    "romance": 10749,
    "thriller": 53,
    "war": 10752,
    "western": 37
}

subgeneros = {
    # Horror
    "slasher": 12339,
    "vampire": 3133,
    "zombie": 12377,
    "found footage": 163053,
    "serial killer": 10714,
    "body horror": 283085,

    # Crime / Thriller
    "detective": 703,
    "heist": 10051,
    "bank robbery": 15363,
    "mafia": 10391,
    "police": 6149,
    "undercover": 1568,
    "mobster": 11578,
    "organized crime": 10291,
    "shootout": 10950,
    "escape from prison": 9777,

    # Action / Martial Arts
    "martial arts": 779,
    "karate": 3436,
    "ninja": 10278,
    "samurai": 1462,
    "mercenary": 3070,

    # Science Fiction
    "alien": 9951,
    "robot": 14544,
    "artificial intelligence": 310,
    "cyberpunk": 12190,
    "time travel": 4379,
    "dystopia": 4565,
    "post-apocalyptic": 4458,
    "cyborg": 679,
    "cloning": 11628,
    "genetics": 6017,
    "nuclear weapons": 160381,

    # Fantasy
    "wizard": 177912,
    "magic": 2343,
    "monster": 1299,
    "shape shifter": 162532,
    "mythology": 2035,
    "greek mythology": 2036,

    # Adventure / Historical
    "ancient greece": 162861,
    "godzilla": 7671,
    "giant monster": 11100,
    "kaiju": 161791,

    # Story themes
    "revenge": 9748,
    "kidnapping": 1930,
    "redemption": 11436,
    "dream": 1566,
    "friendship": 9713,
    "female hero": 160137,

    # General film elements
    "violence": 14819,
    "car chase": 15483,
    # Horror / Supernatural
    "exorcism": 2626,
    "demonic possession": 161261,
    "witchcraft": 40931,
    "found footage horror": 342857,
    "graveyard": 166512,

    # Crime / Thriller
    "hitman": 2708,
    "murder investigation": 161982,
    "informant": 14856,
    "dark web": 257224,
    "outlaw": 9503,
    "execution": 13129,
    "mistaken identity": 10325,

    # Science Fiction
    "spaceship": 252937,
    "alien abduction": 12553,
    "alien possession": 163386,

    # Action / Martial Arts
    "martial arts training": 156162,
    "mixed martial arts (mma)": 9917,

    # Fantasy / Surreal
    "dream world": 186789,
    "cult conspiracy": 210585,

    # Drama / Political
    "political thriller": 209817,
    "dark secret": 193282,

}

paises = {
     "Argentina": "AR",
    "Australia": "AU",
    "Austria": "AT",
    "Belgium": "BE",
    "Brazil": "BR",
    "Canada": "CA",
    "Chile": "CL",
    "China": "CN",
    "Colombia": "CO",
    "Czech Republic": "CZ",
    "Denmark": "DK",
    "Egypt": "EG",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Greece": "GR",
    "Hong Kong": "HK",
    "Hungary": "HU",
    "Iceland": "IS",
    "India": "IN",
    "Indonesia": "ID",
    "Iran": "IR",
    "Ireland": "IE",
    "Israel": "IL",
    "Italy": "IT",
    "Japan": "JP",
    "Mexico": "MX",
    "Netherlands": "NL",
    "New Zealand": "NZ",
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Russia": "RU",
    "South Africa": "ZA",
    "South Korea": "KR",
    "Soviet Union": "SU",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "Taiwan": "TW",
    "Thailand": "TH",
    "Turkey": "TR",
    "United Kingdom": "GB",
    "United States": "US"
}

def show_header():
    print()
    print("=== MOVIE RECOMMENDER ===")
    print()

def choose_genre():
    print("Genres available:")

    lista_generos = list(generos.keys())

    for numero, genero in enumerate(lista_generos, start=1):
        print(f"{numero} - {genero.title()}")

    print()

    while True:
        try:
            escolha_genero = int(input("Choose the genre number: "))
        except ValueError:
            print("Please enter a number.")
            continue

        if escolha_genero < 1 or escolha_genero > len(lista_generos):
            print("Invalid option.")
            continue
        break

    genero_escolhido = lista_generos[escolha_genero - 1]

    print()
    print(f"Genre selected: {genero_escolhido.title()}")
    print()

    return genero_escolhido

def choose_keyword():
    print("Styles / Keywords available:")

    lista_subgeneros = list(subgeneros.keys())
    subgeneros_escolhidos = []

    print("0 - Done")

    for numero, subgenero in enumerate(lista_subgeneros, start=1):
        print(f"{numero} - {subgenero.title()}")

    print()

    while len(subgeneros_escolhidos) < 5:
        try:
            escolha_subgenero = int(input("Choose the style/keyword number: "))
        except ValueError:
            print("Please enter a number.")
            continue

        if escolha_subgenero < 0 or escolha_subgenero > len(lista_subgeneros):
            print("Invalid option.")
            continue

        if escolha_subgenero == 0:
            break

        subgenero_escolhido = lista_subgeneros[escolha_subgenero - 1]

        if subgenero_escolhido not in subgeneros_escolhidos:
            subgeneros_escolhidos.append(subgenero_escolhido)
            print(f"Style / Keyword selected: {subgenero_escolhido.title()}")
        else:
            print("This style / keyword is already selected.")

        print()

    print()

    if len(subgeneros_escolhidos) == 5:
        print("Maximum of 5 styles / keywords selected.")

    if subgeneros_escolhidos:
        nomes_selecionados = [
            subgenero.title() for subgenero in subgeneros_escolhidos
        ]
        print(f"Styles / Keywords selected: {', '.join(nomes_selecionados)}")
    else:
        print("No style / keyword selected.")

    print()

    return subgeneros_escolhidos

def choose_keyword_match_mode():
    print("How closely should movies match your selected styles?")
    print()
    print("1 - Broad (match at least one)")
    print("2 - Strict (match all)")
    print()

    while True:
        try:
            escolha = int(input("Choose the matching mode number: "))
        except ValueError:
            print("Please enter a number.")
            continue

        if escolha not in (1, 2):
            print("Invalid option.")
            continue
        break

    print()

    if escolha == 1:
        return "broad"

    return "strict"

def choose_country():
    print("Countries available:")

    lista_paises = list(paises.keys())
    paises_escolhidos = []

    print("0 - Done")

    for numero, pais_nome in enumerate(lista_paises, start=1):
        print(f"{numero} - {pais_nome}")

    print()

    while True:
        try:
            escolha_pais = int(input("Choose the country number: "))
        except ValueError:
            print("Please enter a number.")
            continue

        if escolha_pais < 0 or escolha_pais > len(lista_paises):
            print("Invalid option.")
            continue

        if escolha_pais == 0:
            break

        pais_nome = lista_paises[escolha_pais - 1]
        pais_codigo = paises[pais_nome]

        if pais_codigo not in paises_escolhidos:
            paises_escolhidos.append(pais_codigo)
            print(f"Country selected: {pais_nome}")
        else:
            print("This country is already selected.")

        print()

    print()

    if paises_escolhidos:
        nomes_selecionados = [
            nome for nome, codigo in paises.items()
            if codigo in paises_escolhidos
        ]
        print(f"Countries selected: {', '.join(nomes_selecionados)}")
    else:
        print("Country: Any")

    print()

    return paises_escolhidos

def choose_year_range():
    while True:
        try:
            ano_inicial = int(input("What is the start year? "))
        except ValueError:
            print("Please enter a valid year.")
            continue
        if not MIN_MOVIE_YEAR <= ano_inicial <= ano_atual:
            print(f"Please enter a year between {MIN_MOVIE_YEAR} and {ano_atual}.")
            continue
        break

    while True:
        try:
            ano_final = int(input("What is the end year? "))
        except ValueError:
            print("Please enter a valid year.")
            continue
        if not MIN_MOVIE_YEAR <= ano_final <= ano_atual:
            print(f"Please enter a year between {MIN_MOVIE_YEAR} and {ano_atual}.")
            continue
        if ano_inicial > ano_final:
            print("The start year cannot be greater than the end year.")
            continue
        return ano_inicial, ano_final


def choose_rating_range():
    while True:
        try:
            nota_minima = float(input("What is the minimum rating? "))
        except ValueError:
            print("Please enter a valid rating.")
            continue
        if not math.isfinite(nota_minima) or not 0 <= nota_minima <= 10:
            print("Ratings must be between 0 and 10.")
            continue
        break

    while True:
        try:
            nota_maxima = float(input("What is the maximum rating? "))
        except ValueError:
            print("Please enter a valid rating.")
            continue
        if not math.isfinite(nota_maxima) or not 0 <= nota_maxima <= 10:
            print("Ratings must be between 0 and 10.")
            continue
        if nota_minima > nota_maxima:
            print("The minimum rating cannot be greater than the maximum rating.")
            continue
        return nota_minima, nota_maxima

def build_parameters(
    genero_escolhido,
    subgeneros_escolhidos,
    paises_escolhidos,
    ano_inicial,
    ano_final,
    nota_minima,
    nota_maxima,
    keyword_match_mode
):
    parametros = {
        "with_genres": generos[genero_escolhido],
        "primary_release_date.gte": f"{ano_inicial}-01-01",
        "primary_release_date.lte": f"{ano_final}-12-31",
        "vote_average.gte": nota_minima,
        "vote_average.lte": nota_maxima,
        "vote_count.gte": 100,
        "sort_by": "popularity.desc",
        "language": "en-US"
    }

    if paises_escolhidos:
        parametros["with_origin_country"] = "|".join(paises_escolhidos)

    if subgeneros_escolhidos:
        keyword_ids = [
            str(subgeneros[subgenero])
            for subgenero in subgeneros_escolhidos
        ]
        separador = "|" if keyword_match_mode == "broad" else ","
        parametros["with_keywords"] = separador.join(keyword_ids)

    return parametros

def request_tmdb_json(request_url, parametros):
    try:
        response = requests.get(
            request_url,
            params=parametros,
            headers=headers,
            timeout=10
        )
    except requests.exceptions.Timeout:
        print("TMDB request timed out. Please try again.")
        raise SystemExit(1)
    except requests.exceptions.RequestException:
        print("Could not connect to TMDB. Please check your internet connection and try again.")
        raise SystemExit(1)

    if response.status_code != 200:
        print(f"TMDB request failed. Status code: {response.status_code}")
        raise SystemExit(1)

    try:
        dados = response.json()
    except ValueError:
        print("TMDB returned invalid JSON.")
        raise SystemExit(1)

    if not isinstance(dados, dict):
        print("TMDB returned an invalid response object.")
        raise SystemExit(1)

    return dados

def search_movies(parametros):
    dados = request_tmdb_json(url, parametros)
    results = dados.get("results")
    total_results = dados.get("total_results")

    if (
        not isinstance(results, list)
        or not all(
            isinstance(movie, dict)
            and type(movie.get("id")) is int
            and movie["id"] > 0
            and isinstance(movie.get("title"), str)
            and movie["title"].strip()
            and type(movie.get("vote_average")) in (int, float)
            and 0 <= movie["vote_average"] <= 10
            and math.isfinite(movie["vote_average"])
            and type(movie.get("vote_count")) is int
            and movie["vote_count"] >= 0
            for movie in results
        )
        or type(total_results) is not int
        or total_results < 0
    ):
        print("TMDB returned invalid Discover results.")
        raise SystemExit(1)

    return dados

def get_movie_details(movie_id):
    details_url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    details = request_tmdb_json(
        details_url,
        {
            "language": "en-US",
            "append_to_response": "keywords"
        }
    )

    if type(details.get("id")) is not int or details["id"] != movie_id:
        print("TMDB returned an invalid movie details ID.")
        raise SystemExit(1)

    return details

def get_matched_styles(details, subgeneros_escolhidos):
    keyword_data = details.get("keywords")
    movie_keywords = (
        keyword_data.get("keywords", [])
        if isinstance(keyword_data, dict) else []
    )
    if not isinstance(movie_keywords, list):
        movie_keywords = []

    movie_keyword_ids = {
        keyword["id"] for keyword in movie_keywords
        if isinstance(keyword, dict)
        and type(keyword.get("id")) is int
        and keyword["id"] > 0
    }

    matched_styles = [
        subgenero.title()
        for subgenero in subgeneros_escolhidos
        if subgeneros[subgenero] in movie_keyword_ids
    ]

    return matched_styles

def select_broad_movies(parametros, subgeneros_escolhidos, candidates):
    # Each pool keeps Discover's popularity order and all existing filters.
    style_pools = []
    for subgenero in subgeneros_escolhidos:
        style_parameters = parametros.copy()
        style_parameters["with_keywords"] = str(subgeneros[subgenero])
        dados = search_movies(style_parameters)
        style_pools.append(dados["results"])

    selected_movies = []
    selected_ids = set()

    # Give each style one turn before filling any remaining slots.
    for pool in style_pools:
        for filme in pool:
            if filme["id"] not in selected_ids:
                selected_movies.append(filme)
                selected_ids.add(filme["id"])
                break
        if len(selected_movies) == MAX_RECOMMENDATIONS:
            return selected_movies

    # Revisit the pools in rounds, including the general Broad search.
    while len(selected_movies) < MAX_RECOMMENDATIONS:
        added_movie = False
        for pool in style_pools + [candidates]:
            for filme in pool:
                if filme["id"] not in selected_ids:
                    selected_movies.append(filme)
                    selected_ids.add(filme["id"])
                    added_movie = True
                    break
            if len(selected_movies) == MAX_RECOMMENDATIONS:
                return selected_movies
        if not added_movie:
            break

    return selected_movies


def display_movies(filmes, subgeneros_escolhidos, details_by_id):
    if filmes:
        print("=== RECOMMENDED MOVIES ===")
        print()

        for numero, filme in enumerate(filmes[:5], start=1):
            print(f"{numero}. {filme['title']}")
            print(f"   Rating: {filme['vote_average']}")
            print(f"   Vote count: {filme['vote_count']}")

            movie_id = filme["id"]

            if movie_id not in details_by_id:
                details_by_id[movie_id] = get_movie_details(movie_id)

            details = details_by_id[movie_id]

            movie_genres = details.get("genres")

            if (
                isinstance(movie_genres, list)
                and movie_genres
                and all(
                    isinstance(genre, dict)
                    and isinstance(genre.get("name"), str)
                    and genre["name"].strip()
                    for genre in movie_genres
                )
            ):
                genre_names = [
                    genre["name"].strip() for genre in movie_genres
                ]
                print(f"   Genres: {', '.join(genre_names)}")
            else:
                print("   Genres: Not available.")

            production_countries = details.get("production_countries", [])

            country_names = []
            if isinstance(production_countries, list):
                country_names = [
                    country["name"].strip()
                    for country in production_countries
                    if isinstance(country, dict)
                    and isinstance(country.get("name"), str)
                    and country["name"].strip()
                ]

            if country_names:
                print(f"   Country: {', '.join(country_names)}")
            else:
                print("   Country: Not available.")

            if subgeneros_escolhidos:
                matched_styles = get_matched_styles(
                    details,
                    subgeneros_escolhidos
                )

                if matched_styles:
                    print(f"   Matched styles: {', '.join(matched_styles)}")
                else:
                    print("   Matched styles: Not available.")

            release_date = filme.get("release_date")

            try:
                parsed_date = datetime.strptime(release_date, "%Y-%m-%d")
            except (TypeError, ValueError):
                print("   Release date: Not available.")
            else:
                month_names = (
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                )
                print(
                    f"   Release date: {month_names[parsed_date.month - 1]} "
                    f"{parsed_date.day:02d}, {parsed_date.year:04d}"
                )

            overview = filme.get("overview")

            if overview:
                print(f"   Overview: {overview}")
            else:
                print("   Overview: Not available.")

            print()
            print("-" * 50)

    else:
        print("No movies matched all of your selected criteria.")
        print("Try broadening the year or rating range, choosing another country,")
        print("or using fewer styles / keywords.")

url = "https://api.themoviedb.org/3/discover/movie"

headers = {
    "Authorization": f"Bearer {tmdb_token}",
    "accept": "application/json"
}


def main():
    if not tmdb_token:
        print("TMDB_TOKEN is missing or blank. Set it in your environment or .env file.")
        raise SystemExit(1)

    show_header()
    print()

    genero_escolhido = choose_genre()

    subgeneros_escolhidos = choose_keyword()

    keyword_match_mode = "strict"

    if len(subgeneros_escolhidos) >= 2:
        keyword_match_mode = choose_keyword_match_mode()

    paises_escolhidos = choose_country()

    ano_inicial, ano_final = choose_year_range()

    nota_minima, nota_maxima = choose_rating_range()


    parametros = build_parameters(
        genero_escolhido,
        subgeneros_escolhidos,
        paises_escolhidos,
        ano_inicial,
        ano_final,
        nota_minima,
        nota_maxima,
        keyword_match_mode=keyword_match_mode
    )

    dados = search_movies(parametros)

    candidates = dados["results"]
    details_by_id = {}

    if keyword_match_mode == "broad" and len(subgeneros_escolhidos) >= 2:
        filmes = select_broad_movies(
            parametros,
            subgeneros_escolhidos,
            candidates
        )
    else:
        filmes = candidates

    print()
    print(f"Movies found: {dados['total_results']}")
    print()

    if not filmes:
        print("No movies matched all of your selected criteria.")
        print("Try broadening the year or rating range, choosing another country,")
        print("or using fewer styles / keywords.")
    else:
        display_movies(
            filmes,
            subgeneros_escolhidos,
            details_by_id
        )


if __name__ == "__main__":
    main()
