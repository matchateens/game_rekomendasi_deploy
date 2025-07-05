# games/urls.py

from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.home_page, name='home'),
    path('game/<int:game_id>/', views.game_detail, name='game_detail'),
    path('dashboard/', views.user_dashboard, name='dashboard'),

    # Category pages
    path('genres/', views.genre_list, name='genre_list'),
    path('genre/<str:genre_name>/', views.games_by_genre, name='games_by_genre'),
    path('publishers/', views.publisher_list, name='publisher_list'),
    path('publisher/<str:publisher_name>/', views.games_by_publisher, name='games_by_publisher'),
    path('esrb/', views.esrb_list, name='esrb_list'),
    path('esrb/<slug:esrb_slug>/', views.games_by_esrb, name='games_by_esrb'),
    path('ratings/', views.rating_list, name='rating_list'),
    path('rating/<str:rating_range>/', views.games_by_rating, name='games_by_rating'),
    path('platform/<slug:platform_slug>/', views.games_by_platform, name='games_by_platform'),
    
    # API endpoints
    path('api/rate/', views.rate_game, name='rate_game'),
    path('api/bookmark/', views.bookmark_game, name='bookmark_game'),
    path('api/recommendations/', views.get_recommendations_api, name='recommendations_api'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/create-demo-user/', views.create_demo_user, name='create_demo_user'),
]
