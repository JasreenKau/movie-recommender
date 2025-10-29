import os
import time
import pickle
import requests
import pandas as pd
import streamlit as st
from fuzzywuzzy import process
import gdown
import os, gdown, time, pickle, pandas as pd, streamlit as st

st.set_page_config(page_title="Movie Recommender", layout="wide")

# --- CONFIG & FILE DOWNLOAD ---
files_to_download = {
    "tmdb_5000_credits.csv": "https://drive.google.com/uc?id=1a8A4To_2911TsIRv0dQQytpH6fpjgCJB",
    "movie_dict.pkl": "https://drive.google.com/uc?id=155_HywJ8vF5zDueAVYyd6VsZrdbnV6xR",
    "similarity.pkl": "https://drive.google.com/uc?id=1PCbJaH8ZdjpThc4EtvkNQFbWe-71mKde"
}

# --- Download missing files ---
for filename, url in files_to_download.items():
    if not os.path.exists(filename):
        st.write(f"📥 Downloading **{filename}** from Google Drive...")
        try:
            gdown.download(url, filename, quiet=False)
        except Exception as e:
            st.error(f"❌ Failed to download {filename}: {e}")
            st.stop()

        # Wait a bit to ensure file is written
        wait_time = 0
        while not os.path.exists(filename) and wait_time < 10:
            time.sleep(1)
            wait_time += 1

        if not os.path.exists(filename):
            st.error(f"⚠️ File {filename} could not be found after download.")
            st.stop()

# --- Load data safely ---
try:
    with open("movie_dict.pkl", "rb") as f:
        movies_dict = pickle.load(f)
    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)

    movies = pd.DataFrame(movies_dict)

except Exception as e:
    st.error(f"❌ Failed to load data files: {e}")
    st.stop()

# LOAD TMDB API KEY
try:
    API_KEY = st.secrets["API_KEY"]
except Exception:
    API_KEY = "6a99c53243ce2282293c184a308d3ef2"  # fallback for local run

# HELPER FUNCTIONS

def fetch_movie_details(movie_id):
    """Fetch poster, rating, genres, and overview from TMDB."""
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url)
        data = response.json()
        poster = "https://image.tmdb.org/t/p/w500/" + data.get("poster_path", "")
        rating = data.get("vote_average", "N/A")
        genres = ", ".join([genre["name"] for genre in data.get("genres", [])])
        overview = data.get("overview", "No description available.")
        return poster, rating, genres, overview
    except Exception as e:
        st.warning(f"⚠️ Failed to fetch details for movie ID {movie_id}: {e}")
        return "", "N/A", "", "No details available."


def recommend(movie_name):
    """Recommend top 5 similar movies."""
    try:
        movie_index = movies[movies["title"] == movie_name].index[0]
    except IndexError:
        st.error("❌ Movie not found in dataset.")
        return []

    distances = similarity[movie_index]
    movie_indices = sorted(
        list(enumerate(distances)), reverse=True, key=lambda x: x[1]
    )[1:6]

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


def fuzzy_search(query, choices):
    """Fuzzy search for closest match."""
    match, score = process.extractOne(query, choices)
    return match


# LOAD DATA SAFELY

try:
    movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
    similarity = pickle.load(open("similarity.pkl", "rb"))
    movies = pd.DataFrame(movies_dict)
except Exception as e:
    st.error(f"❌ Failed to load data files: {e}")
    st.stop()

# STREAMLIT PAGE SETUP
st.markdown(
    """
    <style>
    body { color: white; }
    .movie-container {
        text-align: center;
        padding: 15px;
        transition: transform 0.3s ease;
        background-color: #1e1e1e;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin: 10px 0;
    }
    .movie-container:hover { transform: scale(1.03); }
    .movie-title { font-size: 18px; font-weight: bold; margin: 10px 0 4px; }
    .movie-meta { font-size: 14px; color: #CCCCCC; margin-bottom: 10px; }
    .movie-overview { font-size: 13px; color: #AAAAAA; text-align: left; padding: 5px; }
    img { border-radius: 10px; height: 350px; object-fit: cover; margin-bottom: 10px; }
    .footer { text-align: center; margin-top: 50px; font-size: 14px; color: #888; }
    </style>
    """,
    unsafe_allow_html=True
)

# MAIN TABS

tab1, tab2 = st.tabs(["🏠 Home", "ℹ️ About"])

# --- HOME TAB ---
with tab1:
    st.markdown("<h1 style='text-align: center;'>🎬 Movie Recommender System</h1>", unsafe_allow_html=True)

    selected_movie = st.selectbox(
        "Search for a movie:",
        sorted(movies["title"].tolist()),
        index=None,
        placeholder="Start typing a movie name..."
    )

    if selected_movie:
        if st.button("🔍 Recommend Based on This"):
            with st.spinner("Fetching recommendations..."):
                time.sleep(1)
                recommendations = recommend(selected_movie)

            if recommendations:
                cols = st.columns(5)
                for idx, col in enumerate(cols):
                    with col:
                        movie = recommendations[idx]
                        rating = round(float(movie["rating"]), 1) if movie["rating"] != "N/A" else "N/A"
                        st.markdown(f"""
                            <div class="movie-container">
                                <img src="{movie['poster']}" width="100%" />
                                <div class="movie-title">{movie['title']}</div>
                                <div class="movie-meta">⭐ {rating} | 🎭 {movie['genres']}</div>
                                <div class="movie-overview">{movie['overview'][:200]}...</div>
                            </div>
                        """, unsafe_allow_html=True)

# --- ABOUT TAB ---
with tab2:
    st.markdown("""
        ### ℹ️ About This App
        This movie recommender system suggests top 5 similar movies using **content-based filtering**.
        - Built with **Streamlit**, styled using **HTML/CSS**  
        - Uses **TheMovieDB API** for fetching movie details  
        - Incorporates **Fuzzy Search** for robust input handling  
        - Fully responsive, dark theme compatible  

        **Developed by:** *Jasreen Kaur* 🚀
    """)
