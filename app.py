from flask import Flask, render_template, request, url_for
from urllib.parse import unquote
import pickle
from math import ceil
import re
import pandas as pd 
import numpy as np
import asyncio

from recommend import recommend

from algoliasearch.search.client import SearchClientSync
from api import fetch_poster, fetch_overview, fetch_trailers, fetch_recommend_posters
from api import ALGOLIA_APP_ID, ALGOLIA_API_KEY, ALGOLIA_INDEX_NAME


# load dataset file 
popular_df = pickle.load(open('model/movies_dataset.pkl', 'rb'))

app = Flask(__name__)

# setting up homepage
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    movies_data = popular_df[['id',
                              'title',
                              'genres',
                              'popularity',
                              'crew',
                              'release_year',
                              'runtime']]
    movies_data = movies_data.sort_values(by='popularity', ascending=False)

    # Pagination
    total_movies = len(movies_data)
    num_pages = ceil(total_movies / per_page)
    page = max(min(page, num_pages), 1)

    # Adjusted start_index and end_index for the requested page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    paginated_movies = movies_data.iloc[start_index:end_index]

    movie_ids = list(paginated_movies['id'].values)
    title = list(paginated_movies['title'].values)
    crew = list(paginated_movies['crew'].values)
    popularity = list(paginated_movies['popularity'].round(2))
    release_year = list(paginated_movies['release_year'].values)
    runtime = list(paginated_movies['runtime'].values)

    posters = fetch_poster(movie_ids)

    prev = '/?page=' + str(page - 1) if page > 1 else None
    next = '/?page=' + str(page + 1) if page < num_pages else None

    return render_template('home.html', movies=paginated_movies.to_dict(orient='records'),
                           title=title, crew=crew, popularity=popularity, release_year=release_year, runtime=runtime,
                           posters=posters,
                           num_pages=num_pages, current_page=page, prev=prev, next=next)

# Algolia Search

client = SearchClientSync(ALGOLIA_APP_ID, ALGOLIA_API_KEY)
index =  client.search_single_index(ALGOLIA_INDEX_NAME)
# index.save_object(body)

# Prepare and add records to the index
records = []

for _, row in popular_df.iterrows():
    record = {
        "objectID": str(row["id"]),  # Unique identifier for Algolia
        "title": row["title"],
        "popularity": row["popularity"],
        "genres": row["genres"],
        "overview": row["overview"],
        "keywords": row["keywords"],
        "cast": row["cast"],
        "crew": row["crew"],
        "production_companies": row["production_companies"],
        "runtime": row["runtime"],
        "release_year": row["release_year"],
    }
    records.append(record)

# Save objects to Algolia index
save_resp = index.save_objects(records)

# Wait for indexing to complete
client.wait_for_task(index_name=ALGOLIA_INDEX_NAME, task_id=save_resp.task_id)
print("Records successfully added to the index!")

# Search function
@app.route('/search')
def search():
    query = request.args.get('query')
    response_format = request.args.get('format', 'html')

    if not query:
        error_message = "Query parameter is required"
        if response_format == 'json':
            return jsonify({'error': error_message})
        else:
            return render_template('search.html', error=error_message)

    # Perform search using Algolia
    search_response = client.search({
        "requests": [
            {
                "indexName": index_name,
                "query": query
            }
        ]
    })

    hits = search_response['results'][0]['hits']

    # Extract movie IDs
    movie_ids = [hit['objectID'] for hit in hits]

    # Fetch posters for the movies
    posters = fetch_poster(movie_ids)

    # Attach poster URLs to results
    for hit, poster in zip(hits, posters):
        hit['poster_url'] = poster

    if response_format == 'json':
        return jsonify(hits)
    else:
        return render_template('search.html', hits=hits, query=query)


# Setting Movie Page
@app.route('/movie', methods=['GET'])
def movie():
    id = request.args.get('id')
    title = unquote(request.args.get('title'))
    genres = unquote(request.args.get('genres'))
    popularity = request.args.get('popularity')
    cast = request.args.get('cast')
    crew = unquote(request.args.get('crew'))
    production = request.args.get('production_comapnaies')
    runtime = request.args.get('runtime')
    release_year = request.args.get('release_year')

    # Fetch poster URLs, overview, trailer for the movie IDs
    # print(f"Fetching poster for movie with ID: {id}")
    posters = fetch_poster([id])
    # print (posters)
    overview = fetch_overview([id])
    trailer_link = fetch_trailers([id])
    # print(trailer_link)

    # Recommended movies and fetch poster URLs for the movie IDs that were recommended
    recommended_movies = recommend(title)
    recommended_posters = fetch_recommend_posters(recommended_movies)

    return render_template('movie.html', id=id,
                           title=title,
                           overview=overview[0] if overview else None,
                           genres=genres,
                           popularity=popularity,
                           cast=cast,
                           crew=crew,
                           production=production,
                           runtime=runtime,
                           release_year=release_year,
                           posters=posters,
                           trailer_link=trailer_link,
                           recommended_movies=recommended_movies,
                           recommended_posters=recommended_posters
                           )

if __name__ == '__main__':
    app.run(debug=True)