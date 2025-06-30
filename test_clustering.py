"""
Test script untuk K-Means Clustering Engine
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from games.models import Game
from games.clustering import GameClusteringEngine
import pandas as pd

def test_clustering_engine():
    print("🧪 Testing K-Means Clustering Engine...")
    
    # Test 1: Initialize engine
    print("\n1. Testing engine initialization...")
    try:
        engine = GameClusteringEngine(n_clusters=4)
        print("✅ Engine initialized successfully")
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False
    
    # Test 2: Get sample games
    print("\n2. Testing data preparation...")
    try:
        games = Game.objects.all()[:50]  # Test with 50 games
        if not games:
            print("❌ No games found in database")
            return False
        print(f"✅ Found {len(games)} games for testing")
    except Exception as e:
        print(f"❌ Failed to get games: {e}")
        return False
    
    # Test 3: Prepare features
    print("\n3. Testing feature preparation...")
    try:
        features = engine.prepare_features(games)
        print(f"✅ Features prepared successfully: {features.shape}")
        print(f"   Columns: {list(features.columns)[:10]}...")  # Show first 10 columns
    except Exception as e:
        print(f"❌ Feature preparation failed: {e}")
        return False
    
    # Test 4: Fit clustering model
    print("\n4. Testing model fitting...")
    try:
        cluster_labels = engine.fit(games)
        print(f"✅ Model fitted successfully")
        print(f"   Cluster labels: {set(cluster_labels)}")
        print(f"   Silhouette score: {engine.silhouette_avg:.3f}")
    except Exception as e:
        print(f"❌ Model fitting failed: {e}")
        return False
    
    # Test 5: Test predictions
    print("\n5. Testing predictions...")
    try:
        test_game = games[0]
        predicted_cluster = engine.predict([test_game])[0]
        print(f"✅ Prediction successful for '{test_game.name}': Cluster {predicted_cluster}")
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return False
    
    # Test 6: Test recommendations
    print("\n6. Testing cluster recommendations...")
    try:
        recommendations = engine.get_cluster_recommendations(test_game, num_recommendations=5)
        print(f"✅ Got {len(recommendations)} recommendations for '{test_game.name}'")
        for i, rec in enumerate(recommendations[:3]):
            print(f"   {i+1}. {rec.name} (Rating: {rec.rating})")
    except Exception as e:
        print(f"❌ Cluster recommendations failed: {e}")
        return False
    
    print("\n🎉 All clustering tests passed!")
    return True

if __name__ == "__main__":
    test_clustering_engine()
