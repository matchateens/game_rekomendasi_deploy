# games/admin.py

from django.contrib import admin
from .models import (
    Game, Genre, Platform, Publisher, Tag,
    UserGameRating, UserGameInteraction, UserPreference,
    GameSimilarity, RecommendationCache
)

# Game Admin
class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'released', 'rating', 'metacritic', 'popularity_score')
    search_fields = ('name', 'description')
    list_filter = ('released', 'rating', 'genres', 'platforms')
    filter_horizontal = ('genres', 'platforms', 'publishers', 'tags')
    readonly_fields = ('popularity_score', 'content_vector')

# User Rating Admin
class UserGameRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'rating', 'created_at', 'updated_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'game__name')

# User Interaction Admin
class UserGameInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'interaction_type', 'interaction_weight', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'game__name')

# User Preference Admin
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'avg_rating_preference', 'avg_metacritic_preference', 'last_updated')
    search_fields = ('user__username',)
    readonly_fields = ('preferred_genres', 'preferred_platforms', 'preferred_publishers', 'preferred_tags')

# Game Similarity Admin
class GameSimilarityAdmin(admin.ModelAdmin):
    list_display = ('game1', 'game2', 'content_similarity', 'collaborative_similarity', 'hybrid_similarity')
    search_fields = ('game1__name', 'game2__name')
    list_filter = ('last_calculated',)

# Recommendation Cache Admin
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = ('user', 'recommendation_type', 'created_at', 'expires_at')
    list_filter = ('recommendation_type', 'created_at', 'expires_at')
    search_fields = ('user__username',)
    readonly_fields = ('recommended_games',)

# Register models
admin.site.register(Game, GameAdmin)
admin.site.register(Genre)
admin.site.register(Platform)
admin.site.register(Publisher)
admin.site.register(Tag)
admin.site.register(UserGameRating, UserGameRatingAdmin)
admin.site.register(UserGameInteraction, UserGameInteractionAdmin)
admin.site.register(UserPreference, UserPreferenceAdmin)
admin.site.register(GameSimilarity, GameSimilarityAdmin)
admin.site.register(RecommendationCache, RecommendationCacheAdmin)
