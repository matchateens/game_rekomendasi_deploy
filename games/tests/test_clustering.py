"""
Test suite untuk K-Means Clustering Engine
"""

from django.test import TestCase
from games.models import Game
from games.clustering import GameClusteringEngine
import pandas as pd

class ClusteringTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create some test games
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
        
        # Initialize clustering engine
        self.engine = GameClusteringEngine(n_clusters=2)
    
    def test_engine_initialization(self):
        """Test clustering engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.n_clusters, 2)
    
    def test_feature_preparation(self):
        """Test feature preparation"""
        games = Game.objects.all()
        features = self.engine.prepare_features(games)
        
        # Check if features DataFrame has correct shape
        self.assertIsInstance(features, pd.DataFrame)
        self.assertEqual(len(features), len(games))
        
        # Check if required columns exist
        self.assertIn('Rating', features.columns)
    
    def test_model_fitting(self):
        """Test model fitting"""
        games = Game.objects.all()
        cluster_labels = self.engine.fit(games)
        
        # Check if cluster labels are assigned
        self.assertEqual(len(cluster_labels), len(games))
        self.assertTrue(all(label in [0, 1] for label in cluster_labels))
        
        # Check if silhouette score is calculated
        self.assertTrue(hasattr(self.engine, 'silhouette_avg'))
        self.assertIsInstance(self.engine.silhouette_avg, float)
    
    def test_predictions(self):
        """Test cluster predictions"""
        # First fit the model
        games = Game.objects.all()
        self.engine.fit(games)
        
        # Test prediction for a single game
        prediction = self.engine.predict([self.game1])[0]
        self.assertIn(prediction, [0, 1])
    
    def test_cluster_recommendations(self):
        """Test getting recommendations from same cluster"""
        # First fit the model
        games = Game.objects.all()
        self.engine.fit(games)
        
        # Get recommendations
        recommendations = self.engine.get_cluster_recommendations(self.game1, num_recommendations=2)
        
        # Check recommendations
        self.assertLessEqual(len(recommendations), 2)
        self.assertNotIn(self.game1, recommendations)
