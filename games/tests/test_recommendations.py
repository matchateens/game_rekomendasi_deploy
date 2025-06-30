"""
Test suite untuk Hybrid Recommendation System
"""

from django.test import TestCase
from django.contrib.auth.models import User
from games.models import Game, UserGameRating
from games.recommendation import HybridRecommendationEngine

class RecommendationTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test games
        self.game1 = Game.objects.create(
            name="Test Game 1",
            rating=4.5,
            esrb="Teen"
        )
        self.game2 = Game.objects.create(
            name="Test Game 2",
            rating=3.8,
            esrb="Everyone"
        )
        self.game3 = Game.objects.create(
            name="Test Game 3",
            rating=4.2,
            esrb="Mature"
        )
        self.game4 = Game.objects.create(
            name="Test Game 4",
            rating=4.0,
            esrb="Teen"
        )
        
        # Initialize recommendation engine
        self.engine = HybridRecommendationEngine()
    
    def test_engine_initialization(self):
        """Test recommendation engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.content_weight, 0.4)
        self.assertEqual(self.engine.collaborative_weight, 0.4)
        self.assertEqual(self.engine.popularity_weight, 0.2)
    
    def test_recommendations_for_new_user(self):
        """Test recommendations for user with no ratings"""
        recommendations = self.engine.get_recommendations(
            self.user, 
            num_recommendations=3, 
            recommendation_type='hybrid'
        )
        
        # Should return popular games for new users
        self.assertLessEqual(len(recommendations), 3)
        self.assertIsInstance(recommendations, list)
    
    def test_recommendations_with_user_ratings(self):
        """Test recommendations for user with ratings"""
        # Add some ratings
        UserGameRating.objects.create(user=self.user, game=self.game1, rating=5)
        UserGameRating.objects.create(user=self.user, game=self.game2, rating=3)
        
        recommendations = self.engine.get_recommendations(
            self.user,
            num_recommendations=2,
            recommendation_type='hybrid'
        )
        
        # Should not recommend already rated games
        recommended_ids = [game.id for game in recommendations]
        self.assertNotIn(self.game1.id, recommended_ids)
        self.assertNotIn(self.game2.id, recommended_ids)
    
    def test_content_based_recommendations(self):
        """Test content-based recommendations"""
        # Add a rating
        UserGameRating.objects.create(user=self.user, game=self.game1, rating=5)
        
        recommendations = self.engine.get_recommendations(
            self.user,
            num_recommendations=2,
            recommendation_type='content'
        )
        
        self.assertIsInstance(recommendations, list)
    
    def test_popular_recommendations(self):
        """Test popular recommendations"""
        recommendations = self.engine.get_recommendations(
            self.user,
            num_recommendations=3,
            recommendation_type='popular'
        )
        
        self.assertLessEqual(len(recommendations), 3)
        # Should be sorted by rating
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                self.assertGreaterEqual(
                    recommendations[i].rating or 0,
                    recommendations[i + 1].rating or 0
                )
    
    def test_collaborative_recommendations(self):
        """Test collaborative filtering recommendations"""
        # Create another user with similar ratings
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Both users rate game1 highly
        UserGameRating.objects.create(user=self.user, game=self.game1, rating=5)
        UserGameRating.objects.create(user=user2, game=self.game1, rating=5)
        
        # User2 also rates game3 highly
        UserGameRating.objects.create(user=user2, game=self.game3, rating=5)
        
        recommendations = self.engine.get_recommendations(
            self.user,
            num_recommendations=2,
            recommendation_type='collaborative'
        )
        
        self.assertIsInstance(recommendations, list)
    
    def test_recommendation_caching(self):
        """Test that recommendations are cached properly"""
        # First call
        recs1 = self.engine.get_recommendations(
            self.user,
            num_recommendations=2,
            recommendation_type='hybrid'
        )
        
        # Second call (should use cache)
        recs2 = self.engine.get_recommendations(
            self.user,
            num_recommendations=2,
            recommendation_type='hybrid'
        )
        
        # Results should be the same
        self.assertEqual(len(recs1), len(recs2))
        if recs1 and recs2:
            self.assertEqual(recs1[0].id, recs2[0].id)
