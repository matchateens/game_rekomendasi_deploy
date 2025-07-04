# games/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Model-model kecil untuk relasi data
class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Platform(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon_class = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

class Publisher(models.Model):
    name = models.CharField(max_length=150, unique=True)
    def __str__(self): return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

# Model Utama untuk Game
class Game(models.Model):
    name = models.CharField(max_length=255)
    released = models.DateField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    metacritic = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    cover_image_url = models.URLField(max_length=500, null=True, blank=True, default='https://via.placeholder.com/250x350.png?text=No+Image')
    esrb = models.CharField(max_length=10, null=True, blank=True)  # For storing ESRB ratings
    store_url = models.JSONField(null=True, blank=True, default=dict)  # For storing platform store URLs
    
    genres = models.ManyToManyField(Genre, blank=True)
    platforms = models.ManyToManyField(Platform, blank=True)
    publishers = models.ManyToManyField(Publisher, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)

    # Fields untuk content-based filtering
    popularity_score = models.FloatField(default=0.0)
    content_vector = models.JSONField(null=True, blank=True)  # Untuk menyimpan feature vector
    
    def __str__(self):
        return self.name

    def get_content_features(self):
        """Return content features untuk content-based filtering"""
        features = {
            'genres': list(self.genres.values_list('name', flat=True)),
            'platforms': list(self.platforms.values_list('name', flat=True)),
            'publishers': list(self.publishers.values_list('name', flat=True)),
            'tags': list(self.tags.values_list('name', flat=True)),
            'rating': self.rating or 0,
            'metacritic': self.metacritic or 0,
        }
        return features

# Model untuk User Ratings (Collaborative Filtering)
class UserGameRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    rating = models.FloatField(
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"{self.user.username} - {self.game.name}: {self.rating}"

# Model untuk User Interactions (Implicit Feedback)
class UserGameInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('click', 'Click'),
        ('search', 'Search'),
        ('like', 'Like'),
        ('bookmark', 'Bookmark'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    interaction_weight = models.FloatField(default=1.0)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.game.name}"

# Model untuk User Preferences (Learned dari interactions)
class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_genres = models.JSONField(default=dict)  # {'action': 0.8, 'rpg': 0.6}
    preferred_platforms = models.JSONField(default=dict)
    preferred_publishers = models.JSONField(default=dict)
    preferred_tags = models.JSONField(default=dict)
    avg_rating_preference = models.FloatField(default=0.0)
    avg_metacritic_preference = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"

# Model untuk Similarity Cache (Performance optimization)
class GameSimilarity(models.Model):
    game1 = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='similarity_from')
    game2 = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='similarity_to')
    content_similarity = models.FloatField(default=0.0)
    collaborative_similarity = models.FloatField(default=0.0)
    hybrid_similarity = models.FloatField(default=0.0)
    last_calculated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('game1', 'game2')

    def __str__(self):
        return f"Similarity: {self.game1.name} - {self.game2.name}"

# Model untuk Recommendation Cache
class RecommendationCache(models.Model):
    RECOMMENDATION_TYPES = [
        ('content', 'Content-Based'),
        ('collaborative', 'Collaborative'),
        ('hybrid', 'Hybrid'),
        ('popular', 'Popular'),
        ('trending', 'Trending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    recommended_games = models.JSONField()  # List of game IDs dengan scores
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ('user', 'recommendation_type')

    def __str__(self):
        return f"Recommendations for {self.user.username} - {self.recommendation_type}"

    def is_expired(self):
        return timezone.now() > self.expires_at
