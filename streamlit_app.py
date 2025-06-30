import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MultiLabelBinarizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score
import pickle
import os

# Set page config
st.set_page_config(
    page_title="Game Recommender System",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 2rem;
    }
    .game-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    .metric-card {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the game dataset"""
    try:
        df = pd.read_csv('games.csv')
        return df
    except FileNotFoundError:
        st.error("File games.csv tidak ditemukan. Pastikan file ada di direktori yang sama.")
        return None

@st.cache_data
def preprocess_data(df):
    """Preprocess data for machine learning"""
    # Handle missing values
    df['Rating'] = df['Rating'].fillna(0)
    df['Genres'] = df['Genres'].fillna('Unknown')
    df['Platforms'] = df['Platforms'].fillna('Unknown')
    df['ESRB_Rating'] = df['ESRB_Rating'].fillna('Not Rated')
    
    # Convert string lists to actual lists
    df['Genres_List'] = df['Genres'].apply(lambda x: x.split(', ') if isinstance(x, str) else ['Unknown'])
    df['Platforms_List'] = df['Platforms'].apply(lambda x: x.split(', ') if isinstance(x, str) else ['Unknown'])
    
    return df

class GameRecommendationEngine:
    def __init__(self):
        self.scaler = StandardScaler()
        self.encoder_esrb = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.mlb_genres = MultiLabelBinarizer()
        self.mlb_platforms = MultiLabelBinarizer()
        self.kmeans = None
        self.similarity_matrix = None
        self.df_processed = None
        
    def prepare_features(self, df):
        """Prepare features for machine learning"""
        # Standardize Rating
        rating_scaled = self.scaler.fit_transform(df[['Rating']])
        rating_df = pd.DataFrame(rating_scaled, columns=['Rating'])
        
        # Encode ESRB
        esrb_encoded = self.encoder_esrb.fit_transform(df[['ESRB_Rating']])
        esrb_df = pd.DataFrame(
            esrb_encoded,
            columns=self.encoder_esrb.get_feature_names_out(['ESRB_Rating'])
        )
        
        # Encode Genres
        genres_encoded = self.mlb_genres.fit_transform(df['Genres_List'])
        genres_df = pd.DataFrame(
            genres_encoded,
            columns=[f"Genre_{g}" for g in self.mlb_genres.classes_]
        )
        
        # Encode Platforms
        platforms_encoded = self.mlb_platforms.fit_transform(df['Platforms_List'])
        platforms_df = pd.DataFrame(
            platforms_encoded,
            columns=[f"Platform_{p}" for p in self.mlb_platforms.classes_]
        )
        
        # Combine all features
        features = pd.concat([rating_df, esrb_df, genres_df, platforms_df], axis=1)
        return features
    
    def fit(self, df, n_clusters=4):
        """Fit the recommendation models"""
        self.df_processed = df.copy()
        
        # Prepare features
        features = self.prepare_features(df)
        
        # Fit K-Means
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = self.kmeans.fit_predict(features)
        
        # Calculate silhouette score
        silhouette_avg = silhouette_score(features, cluster_labels)
        
        # Calculate similarity matrix
        self.similarity_matrix = cosine_similarity(features)
        
        # Add cluster labels to dataframe
        self.df_processed['Cluster'] = cluster_labels
        
        return silhouette_avg, cluster_labels
    
    def get_content_based_recommendations(self, game_idx, top_n=5):
        """Get content-based recommendations"""
        if self.similarity_matrix is None:
            return []
        
        sim_scores = list(enumerate(self.similarity_matrix[game_idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:top_n+1]  # Exclude the game itself
        
        game_indices = [i[0] for i in sim_scores]
        return self.df_processed.iloc[game_indices]
    
    def get_cluster_based_recommendations(self, game_idx, top_n=5):
        """Get cluster-based recommendations"""
        if self.kmeans is None:
            return []
        
        game_cluster = self.df_processed.iloc[game_idx]['Cluster']
        cluster_games = self.df_processed[
            (self.df_processed['Cluster'] == game_cluster) & 
            (self.df_processed.index != game_idx)
        ]
        
        # Sort by rating and return top N
        return cluster_games.nlargest(top_n, 'Rating')
    
    def get_hybrid_recommendations(self, game_idx, top_n=5):
        """Get hybrid recommendations (content + cluster)"""
        content_recs = self.get_content_based_recommendations(game_idx, top_n)
        cluster_recs = self.get_cluster_based_recommendations(game_idx, top_n)
        
        # Combine and remove duplicates
        all_recs = pd.concat([content_recs, cluster_recs]).drop_duplicates()
        
        # Sort by rating and return top N
        return all_recs.nlargest(top_n, 'Rating')

def main():
    st.markdown('<h1 class="main-header">🎮 Game Recommender System</h1>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Preprocess data
    df = preprocess_data(df)
    
    # Sidebar
    st.sidebar.title("🎯 Recommendation Settings")
    
    # Initialize recommendation engine
    if 'engine' not in st.session_state:
        with st.spinner('Initializing recommendation engine...'):
            st.session_state.engine = GameRecommendationEngine()
            silhouette_score, cluster_labels = st.session_state.engine.fit(df)
            st.session_state.silhouette_score = silhouette_score
            st.session_state.cluster_labels = cluster_labels
    
    engine = st.session_state.engine
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Total Games</h3>
            <h2>{len(df)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🎯 Clusters</h3>
            <h2>{len(set(st.session_state.cluster_labels))}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📈 Silhouette Score</h3>
            <h2>{st.session_state.silhouette_score:.3f}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Game selection
    st.subheader("🎮 Select a Game for Recommendations")
    
    # Search functionality
    search_term = st.text_input("🔍 Search for a game:", placeholder="Type game name...")
    
    if search_term:
        filtered_games = df[df['Name'].str.contains(search_term, case=False, na=False)]
        if len(filtered_games) > 0:
            game_options = filtered_games['Name'].tolist()
        else:
            st.warning("No games found matching your search.")
            game_options = df['Name'].tolist()[:50]  # Show first 50 games
    else:
        game_options = df['Name'].tolist()[:50]  # Show first 50 games by default
    
    selected_game = st.selectbox("Choose a game:", game_options)
    
    if selected_game:
        game_idx = df[df['Name'] == selected_game].index[0]
        selected_game_data = df.iloc[game_idx]
        
        # Display selected game info
        st.subheader(f"📋 Selected Game: {selected_game}")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div class="game-card">
                <h4>Game Details</h4>
                <p><strong>Rating:</strong> {selected_game_data['Rating']:.1f}/5</p>
                <p><strong>ESRB:</strong> {selected_game_data['ESRB_Rating']}</p>
                <p><strong>Cluster:</strong> {st.session_state.cluster_labels[game_idx]}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="game-card">
                <h4>Genres & Platforms</h4>
                <p><strong>Genres:</strong> {selected_game_data['Genres']}</p>
                <p><strong>Platforms:</strong> {selected_game_data['Platforms']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recommendation type selection
        rec_type = st.sidebar.selectbox(
            "Recommendation Type:",
            ["Hybrid", "Content-Based", "Cluster-Based"]
        )
        
        num_recommendations = st.sidebar.slider(
            "Number of Recommendations:",
            min_value=3,
            max_value=10,
            value=5
        )
        
        # Generate recommendations
        if st.button("🚀 Get Recommendations", type="primary"):
            with st.spinner('Generating recommendations...'):
                if rec_type == "Content-Based":
                    recommendations = engine.get_content_based_recommendations(game_idx, num_recommendations)
                elif rec_type == "Cluster-Based":
                    recommendations = engine.get_cluster_based_recommendations(game_idx, num_recommendations)
                else:  # Hybrid
                    recommendations = engine.get_hybrid_recommendations(game_idx, num_recommendations)
                
                if len(recommendations) > 0:
                    st.subheader(f"🎯 {rec_type} Recommendations")
                    
                    for i, (_, game) in enumerate(recommendations.iterrows(), 1):
                        st.markdown(f"""
                        <div class="game-card">
                            <h4>{i}. {game['Name']}</h4>
                            <p><strong>Rating:</strong> {game['Rating']:.1f}/5 | 
                               <strong>ESRB:</strong> {game['ESRB_Rating']} | 
                               <strong>Cluster:</strong> {game['Cluster']}</p>
                            <p><strong>Genres:</strong> {game['Genres']}</p>
                            <p><strong>Platforms:</strong> {game['Platforms']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No recommendations found.")
    
    # Additional features in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Dataset Statistics")
    
    if st.sidebar.button("Show Dataset Info"):
        st.subheader("📊 Dataset Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Top Genres:**")
            all_genres = []
            for genres in df['Genres_List']:
                all_genres.extend(genres)
            genre_counts = pd.Series(all_genres).value_counts().head(10)
            st.bar_chart(genre_counts)
        
        with col2:
            st.write("**Rating Distribution:**")
            st.histogram_chart(df['Rating'].dropna(), bins=20)
        
        st.write("**Sample Data:**")
        st.dataframe(df[['Name', 'Rating', 'Genres', 'ESRB_Rating']].head(10))

if __name__ == "__main__":
    main()
