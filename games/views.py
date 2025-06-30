# games/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import uuid

from .models import Game, UserGameRating, UserGameInteraction, Genre, Platform, Publisher, Tag
from .recommendation import HybridRecommendationEngine, record_user_interaction, get_similar_games
from django.db.models import Q

def home_page(request):
    """Enhanced home page dengan hybrid recommendations"""
    today = timezone.now().date()
    
    # Initialize recommendation engine
    rec_engine = HybridRecommendationEngine()
    
    # Basic categories (fallback untuk non-authenticated users)
    popular_games = Game.objects.order_by('-rating')[:6]
    upcoming_games = Game.objects.filter(released__gt=today).order_by('released')[:6]
    new_games = Game.objects.filter(released__lte=today).order_by('-released')[:6]
    
    # Personalized recommendations untuk authenticated users
    recommended_games = []
    content_based_games = []
    collaborative_games = []
    
    if request.user.is_authenticated:
        try:
            # Get hybrid recommendations
            recommended_games = rec_engine.get_recommendations(
                request.user, 
                num_recommendations=6, 
                recommendation_type='hybrid'
            )
            
            # Get content-based recommendations
            content_based_games = rec_engine.get_recommendations(
                request.user,
                num_recommendations=6,
                recommendation_type='content'
            )
            
            # Get collaborative recommendations
            collaborative_games = rec_engine.get_recommendations(
                request.user,
                num_recommendations=6,
                recommendation_type='collaborative'
            )
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            # Fallback to popular games
            recommended_games = popular_games
    
    # Enhanced search dengan hybrid approach
    query = request.GET.get('q')
    search_results = None
    search_type = request.GET.get('search_type', 'hybrid')
    
    if query:
        if request.user.is_authenticated:
            # Record search interaction
            session_id = request.session.get('session_id', str(uuid.uuid4()))
            request.session['session_id'] = session_id
            
            # Hybrid search: text + recommendations
            if search_type == 'hybrid':
                search_results = enhanced_search(request.user, query, rec_engine)
            else:
                search_results = Game.objects.filter(name__icontains=query)
                
            # Record search interaction untuk games yang ditemukan
            for game in search_results[:5]:  # Record top 5 results
                record_user_interaction(request.user, game, 'search', session_id)
        else:
            # Simple text search untuk non-authenticated users
            search_results = Game.objects.filter(name__icontains=query)

    context = {
        'popular_games': popular_games,
        'upcoming_games': upcoming_games,
        'new_games': new_games,
        'recommended_games': recommended_games,
        'content_based_games': content_based_games,
        'collaborative_games': collaborative_games,
        'search_results': search_results,
        'query': query,
        'search_type': search_type,
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'games/home.html', context)

# New views for category pages
def genre_list(request):
    genres = Genre.objects.all()
    # For each genre, get some example games (limit 3)
    genre_data = []
    for genre in genres:
        example_games = genre.game_set.all()[:3]
        genre_data.append({
            'genre': genre,
            'example_games': example_games,
        })
    return render(request, 'games/genre_list.html', {'genre_data': genre_data})

def publisher_list(request):
    publishers = Publisher.objects.all()
    publisher_data = []
    for publisher in publishers:
        example_games = publisher.game_set.all()[:3]
        publisher_data.append({
            'publisher': publisher,
            'example_games': example_games,
        })
    return render(request, 'games/publisher_list.html', {'publisher_data': publisher_data})

def esrb_list(request):
    # Get distinct ESRB ratings from games
    esrb_ratings = Game.objects.exclude(esrb__isnull=True).exclude(esrb='').values_list('esrb', flat=True).distinct()
    esrb_data = []
    for esrb_rating in esrb_ratings:
        example_games = Game.objects.filter(esrb=esrb_rating)[:3]
        if example_games.exists():
            esrb_data.append({
                'esrb_rating': esrb_rating,
                'example_games': example_games,
            })
    return render(request, 'games/esrb_list.html', {'esrb_data': esrb_data})

def rating_list(request):
    # Show games grouped by rating ranges or distinct ratings
    rating_groups = {
        '5-stars': {'name': '5 Stars', 'games': Game.objects.filter(rating__gte=4.5)},
        '4-stars': {'name': '4 Stars', 'games': Game.objects.filter(rating__gte=3.5, rating__lt=4.5)},
        '3-stars': {'name': '3 Stars', 'games': Game.objects.filter(rating__gte=2.5, rating__lt=3.5)},
        'below-3-stars': {'name': 'Below 3 Stars', 'games': Game.objects.filter(rating__lt=2.5)},
    }
    rating_data = {}
    for slug, data in rating_groups.items():
        rating_data[slug] = {
            'name': data['name'],
            'games': data['games'][:3],
            'total': data['games'].count()
        }
    return render(request, 'games/rating_list.html', {'rating_data': rating_data})

def games_by_genre(request, genre_name):
    genre = get_object_or_404(Genre, name=genre_name)
    games = Game.objects.filter(genres=genre).order_by('-rating')
    return render(request, 'games/games_by_category.html', {
        'category_type': 'Genre',
        'category_name': genre.name,
        'games': games
    })

def games_by_publisher(request, publisher_name):
    publisher = get_object_or_404(Publisher, name=publisher_name)
    games = Game.objects.filter(publishers=publisher).order_by('-rating')
    return render(request, 'games/games_by_category.html', {
        'category_type': 'Publisher',
        'category_name': publisher.name,
        'games': games
    })

def games_by_esrb(request, esrb_slug):
    # Convert slug back to ESRB rating
    esrb_map = {
        'everyone': 'Everyone',
        'everyone-10-plus': 'Everyone 10+',
        'teen': 'Teen',
        'mature': 'Mature',
        'adults-only': 'Adults Only',
        'rating-pending': 'Rating Pending',
        'na': 'N/A'
    }
    esrb_rating = esrb_map.get(esrb_slug)
    if not esrb_rating:
        raise Http404("ESRB rating not found")
        
    games = Game.objects.filter(esrb=esrb_rating).order_by('-rating')
    return render(request, 'games/games_by_category.html', {
        'category_type': 'ESRB Rating',
        'category_name': esrb_rating,
        'games': games
    })

def games_by_rating(request, rating_range):
    rating_ranges = {
        '5-stars': {'name': '5 Stars', 'min': 4.5, 'max': 5.0},
        '4-stars': {'name': '4 Stars', 'min': 3.5, 'max': 4.5},
        '3-stars': {'name': '3 Stars', 'min': 2.5, 'max': 3.5},
        'below-3-stars': {'name': 'Below 3 Stars', 'min': 0, 'max': 2.5},
    }
    
    range_info = rating_ranges.get(rating_range)
    if not range_info:
        raise Http404("Rating range not found")
        
    games = Game.objects.filter(
        rating__gte=range_info['min'],
        rating__lt=range_info['max']
    ).order_by('-rating')
    
    return render(request, 'games/games_by_category.html', {
        'category_type': 'Rating',
        'category_name': range_info['name'],
        'games': games
    })

def enhanced_search(user, query, rec_engine):
    """
    Enhanced search yang menggabungkan text search dengan user preferences
    """
    # Basic text search
    text_results = Game.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(genres__name__icontains=query) |
        Q(tags__name__icontains=query)
    ).distinct()
    
    # Jika user punya preferences, rank results berdasarkan preferences
    try:
        user_ratings = UserGameRating.objects.filter(user=user).select_related('game')
        if user_ratings.exists():
            # Calculate user preferences
            user_preferences = rec_engine._calculate_user_content_preferences(user_ratings)
            
            # Score each result berdasarkan user preferences
            scored_results = []
            for game in text_results:
                content_score = rec_engine._calculate_content_similarity(game, user_preferences)
                scored_results.append((game, content_score))
            
            # Sort by score
            scored_results.sort(key=lambda x: x[1], reverse=True)
            return [game for game, score in scored_results]
    except:
        pass
    
    # Fallback to basic text search results
    return text_results

def game_detail(request, game_id):
    """Game detail page dengan similar games recommendations"""
    game = get_object_or_404(Game, id=game_id)
    
    # Get similar games
    similar_games = get_similar_games(game, num_similar=6)
    
    # Get user's rating untuk game ini if logged in
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = UserGameRating.objects.get(user=request.user, game=game)
            # Record view interaction
            session_id = request.session.get('session_id', str(uuid.uuid4()))
            request.session['session_id'] = session_id
            record_user_interaction(request.user, game, 'view', session_id)
        except UserGameRating.DoesNotExist:
            pass
    
    context = {
        'game': game,
        'similar_games': similar_games,
        'user_rating': user_rating,
    }
    return render(request, 'games/game_detail.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def rate_game(request):
    """API endpoint untuk rating games"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        rating = float(data.get('rating'))
        
        if not (1 <= rating <= 5):
            return JsonResponse({'error': 'Rating must be between 1 and 5'}, status=400)
        
        game = get_object_or_404(Game, id=game_id)
        
        # Update or create rating
        user_rating, created = UserGameRating.objects.update_or_create(
            user=request.user,
            game=game,
            defaults={'rating': rating}
        )
        
        # Record interaction
        session_id = request.session.get('session_id', str(uuid.uuid4()))
        record_user_interaction(request.user, game, 'like', session_id)
        
        # Update user preferences
        rec_engine = HybridRecommendationEngine()
        rec_engine.update_user_preferences(request.user)
        
        return JsonResponse({
            'success': True,
            'rating': rating,
            'created': created
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def bookmark_game(request):
    """API endpoint untuk bookmark games"""
    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')
        
        game = get_object_or_404(Game, id=game_id)
        
        # Record bookmark interaction
        session_id = request.session.get('session_id', str(uuid.uuid4()))
        record_user_interaction(request.user, game, 'bookmark', session_id)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_recommendations_api(request):
    """API endpoint untuk mendapatkan recommendations"""
    try:
        rec_type = request.GET.get('type', 'hybrid')
        num_recs = int(request.GET.get('num', 10))
        
        rec_engine = HybridRecommendationEngine()
        recommendations = rec_engine.get_recommendations(
            request.user,
            num_recommendations=num_recs,
            recommendation_type=rec_type
        )
        
        # Convert to JSON
        recs_data = []
        for game in recommendations:
            recs_data.append({
                'id': game.id,
                'name': game.name,
                'rating': game.rating,
                'cover_image_url': game.cover_image_url,
                'released': game.released.isoformat() if game.released else None,
            })
        
        return JsonResponse({
            'recommendations': recs_data,
            'type': rec_type,
            'count': len(recs_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def search_suggestions(request):
    """API endpoint untuk search suggestions"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Get game name suggestions
    games = Game.objects.filter(
        name__icontains=query
    ).values('id', 'name', 'cover_image_url')[:10]
    
    # Get genre suggestions
    genres = Genre.objects.filter(
        name__icontains=query
    ).values('name')[:5]
    
    # Get tag suggestions
    tags = Tag.objects.filter(
        name__icontains=query
    ).values('name')[:5]
    
    suggestions = {
        'games': list(games),
        'genres': [g['name'] for g in genres],
        'tags': [t['name'] for t in tags],
    }
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def user_dashboard(request):
    """User dashboard dengan personalized content"""
    # Get user statistics
    user_ratings = UserGameRating.objects.filter(user=request.user)
    user_interactions = UserGameInteraction.objects.filter(user=request.user)
    
    stats = {
        'total_ratings': user_ratings.count(),
        'avg_rating': user_ratings.aggregate(avg=Avg('rating'))['avg'] or 0,
        'total_interactions': user_interactions.count(),
        'favorite_genres': user_interactions.values('game__genres__name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    }
    
    # Get recent recommendations
    rec_engine = HybridRecommendationEngine()
    recent_recommendations = rec_engine.get_recommendations(request.user, 12)
    
    # Get recently rated games
    recent_ratings = user_ratings.select_related('game').order_by('-updated_at')[:10]
    
    context = {
        'stats': stats,
        'recent_recommendations': recent_recommendations,
        'recent_ratings': recent_ratings,
    }
    return render(request, 'games/dashboard.html', context)

# Demo user creation untuk testing
def create_demo_user(request):
    """Create demo user untuk testing recommendations"""
    if request.method == 'POST':
        username = f"demo_user_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        user = User.objects.create_user(
            username=username,
            password='demo123',
            email=f"{username}@demo.com"
        )
        login(request, user)
        return JsonResponse({'success': True, 'username': username})
    
    return JsonResponse({'error': 'POST method required'}, status=405)
