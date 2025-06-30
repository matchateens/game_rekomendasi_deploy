"""
Test script untuk Hybrid Recommendation System
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from games.models import Game, UserGameRating
from games.recommendation import HybridRecommendationEngine
import time

def test_recommendation_system():
    print("🧪 Testing Hybrid Recommendation System...")
    
    # Test 1: Initialize engine
    print("\n1. Testing engine initialization...")
    try:
        engine = HybridRecommendationEngine()
        print("✅ Recommendation engine initialized successfully")
        print(f"   Weights: Content={engine.content_weight}, Collaborative={engine.collaborative_weight}, Popularity={engine.popularity_weight}")
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False
    
    # Test 2: Get or create test user
    print("\n2. Testing user setup...")
    try:
        user, created = User.objects.get_or_create(
            username='test_user_clustering',
            defaults={'email': 'test@example.com'}
        )
        print(f"✅ Test user {'created' if created else 'found'}: {user.username}")
    except Exception as e:
        print(f"❌ User setup failed: {e}")
        return False
    
    # Test 3: Test with new user (no ratings)
    print("\n3. Testing recommendations for new user...")
    try:
        start_time = time.time()
        recommendations = engine.get_recommendations(user, num_recommendations=10, recommendation_type='hybrid')
        end_time = time.time()
        
        print(f"✅ Got {len(recommendations)} recommendations for new user")
        print(f"   Response time: {end_time - start_time:.3f} seconds")
        for i, game in enumerate(recommendations[:3]):
            print(f"   {i+1}. {game.name} (Rating: {game.rating})")
    except Exception as e:
        print(f"❌ New user recommendations failed: {e}")
        return False
    
    # Test 4: Add some ratings for the user
    print("\n4. Testing with user ratings...")
    try:
        # Get some games to rate
        games_to_rate = Game.objects.all()[:5]
        ratings = [5, 4, 5, 3, 4]  # Sample ratings
        
        for game, rating in zip(games_to_rate, ratings):
            UserGameRating.objects.update_or_create(
                user=user,
                game=game,
                defaults={'rating': rating}
            )
        
        print(f"✅ Added {len(ratings)} ratings for test user")
        for game, rating in zip(games_to_rate, ratings):
            print(f"   {game.name}: {rating}/5")
    except Exception as e:
        print(f"❌ Adding ratings failed: {e}")
        return False
    
    # Test 5: Test hybrid recommendations with ratings
    print("\n5. Testing hybrid recommendations with user data...")
    try:
        start_time = time.time()
        recommendations = engine.get_recommendations(user, num_recommendations=10, recommendation_type='hybrid')
        end_time = time.time()
        
        print(f"✅ Got {len(recommendations)} hybrid recommendations")
        print(f"   Response time: {end_time - start_time:.3f} seconds")
        for i, game in enumerate(recommendations[:5]):
            print(f"   {i+1}. {game.name} (Rating: {game.rating})")
    except Exception as e:
        print(f"❌ Hybrid recommendations failed: {e}")
        return False
    
    # Test 6: Test individual recommendation types
    print("\n6. Testing individual recommendation types...")
    
    # Content-based
    try:
        content_recs = engine.get_recommendations(user, num_recommendations=5, recommendation_type='content')
        print(f"✅ Content-based: {len(content_recs)} recommendations")
    except Exception as e:
        print(f"❌ Content-based failed: {e}")
    
    # Collaborative
    try:
        collab_recs = engine.get_recommendations(user, num_recommendations=5, recommendation_type='collaborative')
        print(f"✅ Collaborative: {len(collab_recs)} recommendations")
    except Exception as e:
        print(f"❌ Collaborative failed: {e}")
    
    # Popular
    try:
        popular_recs = engine.get_recommendations(user, num_recommendations=5, recommendation_type='popular')
        print(f"✅ Popular: {len(popular_recs)} recommendations")
    except Exception as e:
        print(f"❌ Popular failed: {e}")
    
    # Test 7: Test caching
    print("\n7. Testing recommendation caching...")
    try:
        # First call
        start_time = time.time()
        recs1 = engine.get_recommendations(user, num_recommendations=10, recommendation_type='hybrid')
        time1 = time.time() - start_time
        
        # Second call (should be cached)
        start_time = time.time()
        recs2 = engine.get_recommendations(user, num_recommendations=10, recommendation_type='hybrid')
        time2 = time.time() - start_time
        
        print(f"✅ Caching test completed")
        print(f"   First call: {time1:.3f}s, Second call: {time2:.3f}s")
        print(f"   Cache speedup: {time1/time2:.1f}x" if time2 > 0 else "   Cache working")
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
    
    print("\n🎉 All recommendation tests completed!")
    return True

if __name__ == "__main__":
    test_recommendation_system()
