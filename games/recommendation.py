# games/recommendation.py

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import json
import logging

from .models import (
    Game, UserGameRating, UserGameInteraction, UserPreference,
    GameSimilarity, RecommendationCache, Genre, Platform, Publisher, Tag
)

logger = logging.getLogger(__name__)

class HybridRecommendationEngine:
    """
    Hybrid Recommendation Engine yang menggabungkan:
    1. Content-Based Filtering
    2. Collaborative Filtering
    3. Popularity-Based Recommendations
    """
    
    def __init__(self):
        self.content_weight = 0.4
        self.collaborative_weight = 0.4
        self.popularity_weight = 0.2
        self.min_interactions = 5  # Minimum interactions untuk collaborative filtering
        
    def get_recommendations(self, user, num_recommendations=10, recommendation_type='hybrid'):
        """
        Main method untuk mendapatkan rekomendasi
        """
        try:
            # Check cache first
            cached_recommendations = self._get_cached_recommendations(user, recommendation_type)
            if cached_recommendations:
                return cached_recommendations
            
            if recommendation_type == 'content':
                recommendations = self._content_based_recommendations(user, num_recommendations)
            elif recommendation_type == 'collaborative':
                recommendations = self._collaborative_recommendations(user, num_recommendations)
            elif recommendation_type == 'popular':
                recommendations = self._popularity_based_recommendations(user, num_recommendations)
            else:  # hybrid
                recommendations = self._hybrid_recommendations(user, num_recommendations)
            
            # Cache the results
            self._cache_recommendations(user, recommendation_type, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user.id}: {str(e)}")
            # Fallback to popular games
            return self._popularity_based_recommendations(user, num_recommendations)
    
    def _content_based_recommendations(self, user, num_recommendations):
        """
        Content-Based Filtering berdasarkan game features
        """
        # Get user's rated games untuk menentukan preferences
        user_ratings = UserGameRating.objects.filter(user=user).select_related('game')
        
        if not user_ratings.exists():
            # New user - return popular games in preferred genres (if any interactions exist)
            return self._get_popular_games_for_new_user(user, num_recommendations)
        
        # Calculate user preferences dari rated games
        user_preferences = self._calculate_user_content_preferences(user_ratings)
        
        # Get all games yang belum di-rate user
        rated_game_ids = user_ratings.values_list('game_id', flat=True)
        candidate_games = Game.objects.exclude(id__in=rated_game_ids)
        
        # Calculate content similarity scores
        game_scores = []
        for game in candidate_games:
            score = self._calculate_content_similarity(game, user_preferences)
            game_scores.append((game, score))
        
        # Sort by score dan return top N
        game_scores.sort(key=lambda x: x[1], reverse=True)
        return [game for game, score in game_scores[:num_recommendations]]
    
    def _collaborative_recommendations(self, user, num_recommendations):
        """
        Collaborative Filtering menggunakan user-item matrix
        """
        # Check if user has enough interactions
        user_ratings_count = UserGameRating.objects.filter(user=user).count()
        
        if user_ratings_count < self.min_interactions:
            # Not enough data for collaborative filtering
            return self._content_based_recommendations(user, num_recommendations)
        
        # Create user-item matrix
        ratings_df = self._create_user_item_matrix()
        
        if ratings_df.empty or user.id not in ratings_df.index:
            return self._content_based_recommendations(user, num_recommendations)
        
        # Find similar users
        similar_users = self._find_similar_users(user, ratings_df)
        
        # Get recommendations based on similar users
        recommendations = self._get_collaborative_recommendations(user, similar_users, ratings_df)
        
        return recommendations[:num_recommendations]
    
    def _hybrid_recommendations(self, user, num_recommendations):
        """
        Hybrid approach yang menggabungkan content-based dan collaborative
        """
        # Get recommendations dari masing-masing method
        content_recs = self._content_based_recommendations(user, num_recommendations * 2)
        collaborative_recs = self._collaborative_recommendations(user, num_recommendations * 2)
        popular_recs = self._popularity_based_recommendations(user, num_recommendations)
        
        # Combine dan weight the recommendations
        game_scores = {}
        
        # Content-based scores
        for i, game in enumerate(content_recs):
            score = (len(content_recs) - i) / len(content_recs) * self.content_weight
            game_scores[game.id] = game_scores.get(game.id, 0) + score
        
        # Collaborative scores
        for i, game in enumerate(collaborative_recs):
            score = (len(collaborative_recs) - i) / len(collaborative_recs) * self.collaborative_weight
            game_scores[game.id] = game_scores.get(game.id, 0) + score
        
        # Popularity scores
        for i, game in enumerate(popular_recs):
            score = (len(popular_recs) - i) / len(popular_recs) * self.popularity_weight
            game_scores[game.id] = game_scores.get(game.id, 0) + score
        
        # Sort by combined score
        sorted_games = sorted(game_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get Game objects
        game_ids = [game_id for game_id, score in sorted_games[:num_recommendations]]
        games = Game.objects.filter(id__in=game_ids)
        
        # Maintain order
        games_dict = {game.id: game for game in games}
        ordered_games = [games_dict[game_id] for game_id in game_ids if game_id in games_dict]
        
        return ordered_games
    
    def _popularity_based_recommendations(self, user, num_recommendations):
        """
        Popularity-based recommendations sebagai fallback
        """
        # Get games yang belum di-rate user
        if user.is_authenticated:
            rated_game_ids = UserGameRating.objects.filter(user=user).values_list('game_id', flat=True)
            games = Game.objects.exclude(id__in=rated_game_ids)
        else:
            games = Game.objects.all()
        
        # Order by rating dan popularity
        popular_games = games.annotate(
            rating_count=Count('usergamerating'),
            avg_user_rating=Avg('usergamerating__rating')
        ).filter(
            rating__isnull=False
        ).order_by('-rating', '-rating_count')
        
        return list(popular_games[:num_recommendations])
    
    def _calculate_user_content_preferences(self, user_ratings):
        """
        Calculate user preferences berdasarkan rated games
        """
        preferences = {
            'genres': {},
            'platforms': {},
            'publishers': {},
            'tags': {},
            'avg_rating': 0,
            'avg_metacritic': 0
        }
        
        total_weight = 0
        rating_sum = 0
        metacritic_sum = 0
        
        for rating_obj in user_ratings:
            game = rating_obj.game
            weight = rating_obj.rating / 5.0  # Normalize to 0-1
            total_weight += weight
            
            # Genre preferences
            for genre in game.genres.all():
                preferences['genres'][genre.name] = preferences['genres'].get(genre.name, 0) + weight
            
            # Platform preferences
            for platform in game.platforms.all():
                preferences['platforms'][platform.name] = preferences['platforms'].get(platform.name, 0) + weight
            
            # Publisher preferences
            for publisher in game.publishers.all():
                preferences['publishers'][publisher.name] = preferences['publishers'].get(publisher.name, 0) + weight
            
            # Tag preferences
            for tag in game.tags.all():
                preferences['tags'][tag.name] = preferences['tags'].get(tag.name, 0) + weight
            
            # Rating preferences
            if game.rating:
                rating_sum += game.rating * weight
            if game.metacritic:
                metacritic_sum += game.metacritic * weight
        
        # Normalize preferences
        if total_weight > 0:
            for category in ['genres', 'platforms', 'publishers', 'tags']:
                for item in preferences[category]:
                    preferences[category][item] /= total_weight
            
            preferences['avg_rating'] = rating_sum / total_weight
            preferences['avg_metacritic'] = metacritic_sum / total_weight
        
        return preferences
    
    def _calculate_content_similarity(self, game, user_preferences):
        """
        Calculate similarity score antara game dan user preferences
        """
        score = 0
        
        # Genre similarity
        game_genres = set(game.genres.values_list('name', flat=True))
        for genre in game_genres:
            score += user_preferences['genres'].get(genre, 0) * 0.3
        
        # Platform similarity
        game_platforms = set(game.platforms.values_list('name', flat=True))
        for platform in game_platforms:
            score += user_preferences['platforms'].get(platform, 0) * 0.2
        
        # Publisher similarity
        game_publishers = set(game.publishers.values_list('name', flat=True))
        for publisher in game_publishers:
            score += user_preferences['publishers'].get(publisher, 0) * 0.1
        
        # Tag similarity
        game_tags = set(game.tags.values_list('name', flat=True))
        for tag in game_tags:
            score += user_preferences['tags'].get(tag, 0) * 0.2
        
        # Rating similarity
        if game.rating and user_preferences['avg_rating'] > 0:
            rating_diff = abs(game.rating - user_preferences['avg_rating'])
            rating_similarity = max(0, 1 - rating_diff / 5.0)  # Normalize
            score += rating_similarity * 0.1
        
        # Metacritic similarity
        if game.metacritic and user_preferences['avg_metacritic'] > 0:
            metacritic_diff = abs(game.metacritic - user_preferences['avg_metacritic'])
            metacritic_similarity = max(0, 1 - metacritic_diff / 100.0)  # Normalize
            score += metacritic_similarity * 0.1
        
        return score
    
    def _create_user_item_matrix(self):
        """
        Create user-item matrix untuk collaborative filtering
        """
        ratings = UserGameRating.objects.select_related('user', 'game').all()
        
        if not ratings.exists():
            return pd.DataFrame()
        
        # Create DataFrame
        data = []
        for rating in ratings:
            data.append({
                'user_id': rating.user.id,
                'game_id': rating.game.id,
                'rating': rating.rating
            })
        
        df = pd.DataFrame(data)
        
        # Create pivot table
        user_item_matrix = df.pivot_table(
            index='user_id',
            columns='game_id',
            values='rating',
            fill_value=0
        )
        
        return user_item_matrix
    
    def _find_similar_users(self, user, ratings_df, num_similar=10):
        """
        Find users yang similar dengan target user
        """
        if user.id not in ratings_df.index:
            return []
        
        user_ratings = ratings_df.loc[user.id].values.reshape(1, -1)
        
        # Calculate cosine similarity dengan semua users
        similarities = cosine_similarity(user_ratings, ratings_df.values)[0]
        
        # Get indices of most similar users (excluding self)
        user_indices = ratings_df.index.tolist()
        similar_indices = []
        
        for i, similarity in enumerate(similarities):
            if user_indices[i] != user.id and similarity > 0:
                similar_indices.append((user_indices[i], similarity))
        
        # Sort by similarity dan return top N
        similar_indices.sort(key=lambda x: x[1], reverse=True)
        return similar_indices[:num_similar]
    
    def _get_collaborative_recommendations(self, user, similar_users, ratings_df):
        """
        Get recommendations berdasarkan similar users
        """
        if not similar_users:
            return []
        
        # Get games yang sudah di-rate oleh user
        user_rated_games = set(ratings_df.columns[ratings_df.loc[user.id] > 0])
        
        # Calculate weighted scores untuk unrated games
        game_scores = {}
        total_similarity = sum(similarity for _, similarity in similar_users)
        
        for similar_user_id, similarity in similar_users:
            similar_user_ratings = ratings_df.loc[similar_user_id]
            
            for game_id, rating in similar_user_ratings.items():
                if rating > 0 and game_id not in user_rated_games:
                    weighted_score = rating * similarity
                    game_scores[game_id] = game_scores.get(game_id, 0) + weighted_score
        
        # Normalize scores
        if total_similarity > 0:
            for game_id in game_scores:
                game_scores[game_id] /= total_similarity
        
        # Sort by score
        sorted_games = sorted(game_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Get Game objects
        game_ids = [game_id for game_id, score in sorted_games if score > 3.0]  # Threshold
        games = Game.objects.filter(id__in=game_ids)
        
        # Maintain order
        games_dict = {game.id: game for game in games}
        ordered_games = [games_dict[game_id] for game_id in game_ids if game_id in games_dict]
        
        return ordered_games
    
    def _get_popular_games_for_new_user(self, user, num_recommendations):
        """
        Get popular games untuk new users berdasarkan interactions (jika ada)
        """
        # Check if user has any interactions
        interactions = UserGameInteraction.objects.filter(user=user)
        
        if interactions.exists():
            # Get genres dari games yang di-interact
            interacted_games = interactions.values_list('game', flat=True)
            preferred_genres = Genre.objects.filter(
                game__in=interacted_games
            ).distinct()
            
            if preferred_genres.exists():
                # Get popular games dalam preferred genres
                games = Game.objects.filter(
                    genres__in=preferred_genres
                ).distinct().order_by('-rating', '-metacritic')
                return list(games[:num_recommendations])
        
        # Fallback to overall popular games
        return self._popularity_based_recommendations(user, num_recommendations)
    
    def _get_cached_recommendations(self, user, recommendation_type):
        """
        Get cached recommendations jika masih valid
        """
        try:
            cache = RecommendationCache.objects.get(
                user=user,
                recommendation_type=recommendation_type
            )
            
            if not cache.is_expired():
                game_ids = [item['game_id'] for item in cache.recommended_games]
                games = Game.objects.filter(id__in=game_ids)
                
                # Maintain order
                games_dict = {game.id: game for game in games}
                ordered_games = [games_dict[game_id] for game_id in game_ids if game_id in games_dict]
                
                return ordered_games
            else:
                cache.delete()
                
        except RecommendationCache.DoesNotExist:
            pass
        
        return None
    
    def _cache_recommendations(self, user, recommendation_type, recommendations):
        """
        Cache recommendations untuk performance
        """
        try:
            # Prepare data untuk cache
            recommended_games = []
            for i, game in enumerate(recommendations):
                recommended_games.append({
                    'game_id': game.id,
                    'rank': i + 1,
                    'score': 1.0 - (i / len(recommendations))  # Simple scoring
                })
            
            # Set expiry time (24 hours untuk hybrid, 1 hour untuk others)
            if recommendation_type == 'hybrid':
                expires_at = timezone.now() + timedelta(hours=24)
            else:
                expires_at = timezone.now() + timedelta(hours=1)
            
            # Update or create cache
            RecommendationCache.objects.update_or_create(
                user=user,
                recommendation_type=recommendation_type,
                defaults={
                    'recommended_games': recommended_games,
                    'expires_at': expires_at
                }
            )
            
        except Exception as e:
            logger.error(f"Error caching recommendations: {str(e)}")
    
    def update_user_preferences(self, user):
        """
        Update user preferences berdasarkan interactions dan ratings
        """
        try:
            # Calculate preferences dari ratings
            user_ratings = UserGameRating.objects.filter(user=user).select_related('game')
            preferences = self._calculate_user_content_preferences(user_ratings)
            
            # Update atau create UserPreference
            user_pref, created = UserPreference.objects.update_or_create(
                user=user,
                defaults={
                    'preferred_genres': preferences['genres'],
                    'preferred_platforms': preferences['platforms'],
                    'preferred_publishers': preferences['publishers'],
                    'preferred_tags': preferences['tags'],
                    'avg_rating_preference': preferences['avg_rating'],
                    'avg_metacritic_preference': preferences['avg_metacritic'],
                }
            )
            
            # Clear recommendation cache
            RecommendationCache.objects.filter(user=user).delete()
            
            return user_pref
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {str(e)}")
            return None

# Utility functions
def record_user_interaction(user, game, interaction_type, session_id=None):
    """
    Record user interaction untuk implicit feedback
    """
    try:
        # Define interaction weights
        weights = {
            'view': 1.0,
            'click': 2.0,
            'search': 1.5,
            'like': 3.0,
            'bookmark': 4.0,
        }
        
        UserGameInteraction.objects.create(
            user=user,
            game=game,
            interaction_type=interaction_type,
            interaction_weight=weights.get(interaction_type, 1.0),
            session_id=session_id
        )
        
        # Update user preferences periodically
        interaction_count = UserGameInteraction.objects.filter(user=user).count()
        if interaction_count % 10 == 0:  # Update every 10 interactions
            engine = HybridRecommendationEngine()
            engine.update_user_preferences(user)
            
    except Exception as e:
        logger.error(f"Error recording interaction: {str(e)}")

def get_similar_games(game, num_similar=10):
    """
    Get games yang similar dengan game tertentu dengan algoritma yang lebih baik
    """
    try:
        similar_games = []
        
        # 1. Games dengan genre yang sama (40% dari hasil)
        genre_similar = Game.objects.filter(
            genres__in=game.genres.all()
        ).exclude(id=game.id).distinct().order_by('-rating')[:int(num_similar * 0.4) + 2]
        
        similar_games.extend(list(genre_similar))
        
        # 2. Games dari publisher yang sama (20% dari hasil)
        if game.publishers.exists():
            publisher_similar = Game.objects.filter(
                publishers__in=game.publishers.all()
            ).exclude(id=game.id).exclude(id__in=[g.id for g in similar_games]).distinct().order_by('-rating')[:int(num_similar * 0.2) + 1]
            
            similar_games.extend(list(publisher_similar))
        
        # 3. Games dengan platform yang sama (20% dari hasil)
        if game.platforms.exists():
            platform_similar = Game.objects.filter(
                platforms__in=game.platforms.all()
            ).exclude(id=game.id).exclude(id__in=[g.id for g in similar_games]).distinct().order_by('-rating')[:int(num_similar * 0.2) + 1]
            
            similar_games.extend(list(platform_similar))
        
        # 4. Games dengan rating serupa (20% dari hasil)
        if game.rating:
            rating_min = max(0, game.rating - 1.0)
            rating_max = min(5, game.rating + 1.0)
            
            rating_similar = Game.objects.filter(
                rating__gte=rating_min,
                rating__lte=rating_max
            ).exclude(id=game.id).exclude(id__in=[g.id for g in similar_games]).order_by('-rating')[:int(num_similar * 0.2) + 1]
            
            similar_games.extend(list(rating_similar))
        
        # Remove duplicates dan ambil hanya num_similar games
        seen_ids = set()
        unique_games = []
        for g in similar_games:
            if g.id not in seen_ids:
                unique_games.append(g)
                seen_ids.add(g.id)
                if len(unique_games) >= num_similar:
                    break
        
        # Jika masih kurang, tambahkan popular games
        if len(unique_games) < num_similar:
            additional_games = Game.objects.exclude(
                id__in=[game.id] + [g.id for g in unique_games]
            ).order_by('-rating')[:num_similar - len(unique_games)]
            
            unique_games.extend(list(additional_games))
        
        return unique_games[:num_similar]
        
    except Exception as e:
        logger.error(f"Error getting similar games: {str(e)}")
        # Fallback to random popular games
        return list(Game.objects.exclude(id=game.id).order_by('-rating')[:num_similar])

def _calculate_content_similarity_between_games(game1_features, game2_features):
    """
    Calculate content similarity between two games based on their features
    """
    similarity = 0.0
    
    # Genre similarity
    genres1 = set(game1_features.get('genres', []))
    genres2 = set(game2_features.get('genres', []))
    if genres1 or genres2:
        genre_similarity = len(genres1.intersection(genres2)) / len(genres1.union(genres2))
        similarity += genre_similarity * 0.3
    
    # Platform similarity
    platforms1 = set(game1_features.get('platforms', []))
    platforms2 = set(game2_features.get('platforms', []))
    if platforms1 or platforms2:
        platform_similarity = len(platforms1.intersection(platforms2)) / len(platforms1.union(platforms2))
        similarity += platform_similarity * 0.2
    
    # Publisher similarity
    publishers1 = set(game1_features.get('publishers', []))
    publishers2 = set(game2_features.get('publishers', []))
    if publishers1 or publishers2:
        publisher_similarity = len(publishers1.intersection(publishers2)) / len(publishers1.union(publishers2))
        similarity += publisher_similarity * 0.1
    
    # Tag similarity
    tags1 = set(game1_features.get('tags', []))
    tags2 = set(game2_features.get('tags', []))
    if tags1 or tags2:
        tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
        similarity += tag_similarity * 0.2
    
    # Rating similarity
    rating1 = game1_features.get('rating', 0)
    rating2 = game2_features.get('rating', 0)
    if rating1 > 0 and rating2 > 0:
        rating_diff = abs(rating1 - rating2)
        rating_similarity = max(0, 1 - rating_diff / 5.0)
        similarity += rating_similarity * 0.1
    
    # Metacritic similarity
    metacritic1 = game1_features.get('metacritic', 0)
    metacritic2 = game2_features.get('metacritic', 0)
    if metacritic1 > 0 and metacritic2 > 0:
        metacritic_diff = abs(metacritic1 - metacritic2)
        metacritic_similarity = max(0, 1 - metacritic_diff / 100.0)
        similarity += metacritic_similarity * 0.1
    
    return similarity
