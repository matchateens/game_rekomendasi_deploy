"""
Simple test untuk memastikan Django CI berfungsi
"""

from django.test import TestCase
from django.contrib.auth.models import User
from games.models import Game, Genre, Platform, Publisher, UserGameRating

class SimpleGameTests(TestCase):
    def setUp(self):
        """Set up test data"""
        self.genre = Genre.objects.create(name="Action")
        self.platform = Platform.objects.create(name="PC")
        self.publisher = Publisher.objects.create(name="Test Publisher")
        
        self.game = Game.objects.create(
            name="Test Game",
            rating=4.5,
            esrb="Teen"
        )
        self.game.genres.add(self.genre)
        self.game.platforms.add(self.platform)
        self.game.publishers.add(self.publisher)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_game_creation(self):
        """Test game model creation"""
        self.assertEqual(self.game.name, "Test Game")
        self.assertEqual(self.game.rating, 4.5)
        self.assertEqual(self.game.esrb, "Teen")
    
    def test_game_str_method(self):
        """Test game string representation"""
        self.assertEqual(str(self.game), "Test Game")
    
    def test_genre_creation(self):
        """Test genre model creation"""
        self.assertEqual(self.genre.name, "Action")
        self.assertEqual(str(self.genre), "Action")
    
    def test_user_game_rating(self):
        """Test user game rating model"""
        rating = UserGameRating.objects.create(
            user=self.user,
            game=self.game,
            rating=5
        )
        
        self.assertEqual(rating.user, self.user)
        self.assertEqual(rating.game, self.game)
        self.assertEqual(rating.rating, 5)
