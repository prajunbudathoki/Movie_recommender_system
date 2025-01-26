import pickle

# loading datasets file
dataset = pickle.load(open('D:\content-filtering\model\movies_dataset.pkl','rb'))
movies_df = pickle.load(open('D:\content-filtering\model\movies.pkl','rb'))
similarity = pickle.load(open('D:\content-filtering\model\similarity.pkl','rb'))

def recommend(movie_title):
    movie_index = next((i for i, title in enumerate(
        movies_df['title']) if title == movie_title), None)
    
    recommended_movies = []

    if movie_index is not None:
        distance = similarity[movie_index]
        movies_list = sorted(list(enumerate(distance)),
                             reverse=True, key=lambda x: x[1])[1:5]
        for i in movies_list:
            movie_data = {
                'title': movies_df.iloc[i[0]]['title'],
                'id': movies_df.iloc[i[0]]['id'],
                'genres': dataset.iloc[i[0]]['genres'],
                'crew': dataset.iloc[i[0]]['crew'],
                'runtime': dataset.iloc[i[0]]['runtime'],
                'release_year': dataset.iloc[i[0]]['release_year']
            }
            recommended_movies.append(movie_data)
            
    return recommended_movies


# movie_title = 'The Dark Knight Rises'
# recommended_movies = recommend(movie_title)
# print(recommended_movies)

