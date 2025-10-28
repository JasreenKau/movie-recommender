import streamlit as st
import pickle
import pandas as pd
import requests
from fuzzywuzzy import process
import time

# --- TMDB API Key ---
API_KEY = "6a99c53243ce2282293c184a308d3ef2"

# --- Fetch poster and movie details ---
def fetch_movie_details(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    response = requests.get(url)
    data = response.json()
    poster = "https://image.tmdb.org/t/p/w500/" + data.get('poster_path', "")
    rating = data.get('vote_average', 'N/A')
    genres = ", ".join([genre['name'] for genre in data.get('genres', [])])
    overview = data.get('overview', 'No description available.')
    return poster, rating, genres, overview

# --- Recommend movies ---
def recommend(movie_name):
    movie_index = movies[movies['title'] == movie_name].index[0]
    distances = similarity[movie_index]
    movie_indices = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommendations = []
    for i in movie_indices:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, rating, genres, overview = fetch_movie_details(movie_id)
        recommendations.append({
            "title": title,
            "poster": poster,
            "rating": rating,
            "genres": genres,
            "overview": overview
        })
    return recommendations

# --- Fuzzy search utility ---
def fuzzy_search(query, choices):
    match, score = process.extractOne(query, choices)
    return match

# --- Load Data ---
movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open("similarity.pkl", "rb"))

# --- Page Setup ---
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.markdown("""
    <style>
    body {
        color: white;
    }
    .movie-container {
        text-align: center;
        padding: 15px;
        transition: transform 0.3s ease;
        background-color: #1e1e1e;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin: 10px 0;
    }
    .movie-container:hover {
        transform: scale(1.03);
    }
    .movie-title {
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0 4px;
    }
    .movie-meta {
        font-size: 14px;
        color: #CCCCCC;
        margin-bottom: 10px;
    }
    .movie-overview {
        font-size: 13px;
        color: #AAAAAA;
        text-align: left;
        padding: 5px;
    }
    img {
        border-radius: 10px;
        height: 350px;
        object-fit: cover;
        margin-bottom: 10px;
    }
    .footer {
        text-align: center;
        margin-top: 50px;
        font-size: 14px;
        color: #888;
    }
    </style>
""", unsafe_allow_html=True)

# --- Tabs ---
tab1, tab2= st.tabs(["🎬 Home", "ℹ️ About"])

# --- Home Tab ---
with tab1:
    st.markdown("<h1 style='text-align: center;'>Movie Recommender System</h1>", unsafe_allow_html=True)

    selected_movie = st.selectbox(
        "Search for a movie:",
        sorted(movies['title'].tolist()),  # Autocomplete dropdown
        index=None,
        placeholder="Start typing a movie name..."
    )

    if selected_movie:
        if st.button("Recommend Based on This"):
            with st.spinner("Fetching recommendations..."):
                time.sleep(1)
                recommendations = recommend(selected_movie)

            cols = st.columns(5)
            for idx, col in enumerate(cols):
                with col:
                    movie = recommendations[idx]
                    rating = round(float(movie['rating']), 1) if movie['rating'] != 'N/A' else 'N/A'
                    st.markdown(f"""
                        <div class="movie-container">
                            <img src="{movie['poster']}" width="100%" />
                            <div class="movie-title">{movie['title']}</div>
                            <div class="movie-meta">⭐ {rating} | 🎭 {movie['genres']}</div>
                            <div class="movie-overview">{movie['overview'][:200]}...</div>
                        </div>
                    """, unsafe_allow_html=True)

# --- About Tab ---
with tab2:
    st.markdown("""
        ### About This App  
        This movie recommender system suggests top 5 similar movies using content-based filtering.  
        - Built with **Streamlit**, styled using **HTML/CSS**  
        - Uses **TheMovieDB API** for movie metadata  
        - Fuzzy search ensures robust input handling  
        - Fully responsive, dark/light mode compatible

        **Developed by:** Jasreen 🚀
    """)