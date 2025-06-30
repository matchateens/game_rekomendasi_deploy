"""
Modul untuk K-Means Clustering dari game berdasarkan fitur-fiturnya
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder, MultiLabelBinarizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from .models import Game

class GameClusteringEngine:
    def __init__(self, n_clusters=4):
        self.n_clusters = n_clusters
        self.kmeans = None
        self.scaler = StandardScaler()
        self.encoder_esrb = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        self.mlb_genres = MultiLabelBinarizer()
        self.mlb_platforms = MultiLabelBinarizer()
        
    def prepare_features(self, games):
        """
        Prepare game features untuk clustering
        """
        # Convert ke DataFrame
        data = []
        for game in games:
            data.append({
                'Name': game.name,
                'Rating': game.rating or 0,
                'Genres': [genre.name for genre in game.genres.all()],
                'Platforms': [platform.name for platform in game.platforms.all()],
                'ESRB': game.esrb
            })
        
        df = pd.DataFrame(data)
        
        # Standardize Rating
        rating_scaled = self.scaler.fit_transform(df[['Rating']])
        rating_df = pd.DataFrame(rating_scaled, columns=['Rating'])
        
        # Encode ESRB
        esrb_encoded = self.encoder_esrb.fit_transform(df[['ESRB']])
        esrb_df = pd.DataFrame(
            esrb_encoded,
            columns=self.encoder_esrb.get_feature_names_out(['ESRB'])
        )
        
        # Encode Genres
        genres_encoded = self.mlb_genres.fit_transform(df['Genres'])
        genres_df = pd.DataFrame(
            genres_encoded,
            columns=[f"Genre_{g}" for g in self.mlb_genres.classes_]
        )
        
        # Encode Platforms
        platforms_encoded = self.mlb_platforms.fit_transform(df['Platforms'])
        platforms_df = pd.DataFrame(
            platforms_encoded,
            columns=[f"Platform_{p}" for p in self.mlb_platforms.classes_]
        )
        
        # Combine all features
        return pd.concat([rating_df, esrb_df, genres_df, platforms_df], axis=1)
    
    def fit(self, games):
        """
        Fit K-Means model dengan game features
        """
        # Prepare features
        features = self.prepare_features(games)
        
        # Fit KMeans
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.cluster_labels = self.kmeans.fit_predict(features)
        
        # Calculate silhouette score
        self.silhouette_avg = silhouette_score(features, self.cluster_labels)
        
        return self.cluster_labels
    
    def predict(self, games):
        """
        Predict cluster untuk game baru
        """
        if self.kmeans is None:
            raise ValueError("Model belum di-fit. Panggil fit() terlebih dahulu.")
        
        features = self.prepare_features(games)
        return self.kmeans.predict(features)
    
    def get_cluster_recommendations(self, game, num_recommendations=5):
        """
        Get rekomendasi game dari cluster yang sama
        """
        if self.kmeans is None:
            raise ValueError("Model belum di-fit. Panggil fit() terlebih dahulu.")
        
        # Predict cluster untuk game input
        game_cluster = self.predict([game])[0]
        
        # Get semua game
        all_games = Game.objects.all()
        
        # Predict clusters untuk semua game
        all_clusters = self.predict(all_games)
        
        # Filter game dalam cluster yang sama
        cluster_games = [
            g for g, c in zip(all_games, all_clusters)
            if c == game_cluster and g.id != game.id
        ]
        
        # Sort by rating dan return top N
        return sorted(cluster_games, key=lambda x: x.rating or 0, reverse=True)[:num_recommendations]
