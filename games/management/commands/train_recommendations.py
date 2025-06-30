# games/management/commands/train_recommendations.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from datetime import timedelta
import random

from games.models import Game, UserGameRating, UserGameInteraction, UserPreference
from games.recommendation import HybridRecommendationEngine

class Command(BaseCommand):
    help = 'Train recommendation system and create sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample users and ratings for testing',
        )
        parser.add_argument(
            '--num-users',
            type=int,
            default=20,
            help='Number of sample users to create',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting recommendation system training...'))
        
        if options['create_sample_data']:
            self.create_sample_data(options['num_users'])
        
        self.train_recommendation_system()
        
        self.stdout.write(self.style.SUCCESS('Recommendation system training completed!'))

    def create_sample_data(self, num_users):
        """Create sample users and ratings for testing"""
        self.stdout.write('Creating sample data...')
        
        # Get all games
        games = list(Game.objects.all())
        if not games:
            self.stdout.write(self.style.ERROR('No games found. Please import games first.'))
            return
        
        # Create sample users
        for i in range(num_users):
            username = f'user_{i+1}'
            email = f'user{i+1}@example.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'User',
                    'last_name': f'{i+1}',
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {username}')
                
                # Create random ratings for this user
                num_ratings = random.randint(5, 15)
                rated_games = random.sample(games, min(num_ratings, len(games)))
                
                for game in rated_games:
                    # Create realistic rating distribution
                    rating = random.choices(
                        [1.0, 2.0, 3.0, 4.0, 5.0],
                        weights=[5, 10, 20, 35, 30]  # More higher ratings
                    )[0]
                    
                    UserGameRating.objects.create(
                        user=user,
                        game=game,
                        rating=rating
                    )
                
                # Create random interactions
                num_interactions = random.randint(10, 30)
                interaction_games = random.sample(games, min(num_interactions, len(games)))
                
                for game in interaction_games:
                    interaction_type = random.choice(['view', 'click', 'search', 'like'])
                    
                    UserGameInteraction.objects.create(
                        user=user,
                        game=game,
                        interaction_type=interaction_type,
                        timestamp=timezone.now() - timedelta(days=random.randint(1, 30))
                    )
        
        self.stdout.write(self.style.SUCCESS(f'Created {num_users} sample users with ratings and interactions'))

    def train_recommendation_system(self):
        """Train the recommendation system"""
        self.stdout.write('Training recommendation system...')
        
        # Initialize recommendation engine
        rec_engine = HybridRecommendationEngine()
        
        # Update user preferences for all users
        users_with_ratings = User.objects.filter(usergamerating__isnull=False).distinct()
        
        for user in users_with_ratings:
            try:
                user_pref = rec_engine.update_user_preferences(user)
                if user_pref:
                    self.stdout.write(f'Updated preferences for user: {user.username}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error updating preferences for {user.username}: {str(e)}')
                )
        
        # Calculate game popularity scores
        self.calculate_popularity_scores()
        
        # Pre-calculate some similarities for performance
        self.precalculate_similarities()
        
        self.stdout.write(self.style.SUCCESS('Recommendation system training completed'))

    def calculate_popularity_scores(self):
        """Calculate popularity scores for games"""
        self.stdout.write('Calculating game popularity scores...')
        
        games = Game.objects.all()
        
        for game in games:
            # Calculate popularity based on ratings and interactions
            rating_count = UserGameRating.objects.filter(game=game).count()
            avg_rating = UserGameRating.objects.filter(game=game).aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or 0
            
            interaction_count = UserGameInteraction.objects.filter(game=game).count()
            
            # Simple popularity formula
            popularity_score = (
                (avg_rating * 0.4) +
                (min(rating_count / 10, 5) * 0.3) +  # Normalize rating count
                (min(interaction_count / 50, 5) * 0.3)  # Normalize interaction count
            )
            
            game.popularity_score = popularity_score
            game.save(update_fields=['popularity_score'])
        
        self.stdout.write(f'Updated popularity scores for {games.count()} games')

    def precalculate_similarities(self):
        """Pre-calculate game similarities for better performance"""
        self.stdout.write('Pre-calculating game similarities...')
        
        from games.recommendation import get_similar_games
        
        # Get top 20 most popular games and calculate similarities
        popular_games = Game.objects.order_by('-popularity_score')[:20]
        
        calculated_count = 0
        for game in popular_games:
            try:
                similar_games = get_similar_games(game, num_similar=10)
                calculated_count += 1
                if calculated_count % 5 == 0:
                    self.stdout.write(f'Calculated similarities for {calculated_count} games')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Error calculating similarities for {game.name}: {str(e)}')
                )
        
        self.stdout.write(f'Pre-calculated similarities for {calculated_count} games')

    def create_demo_user(self):
        """Create a demo user for testing"""
        demo_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'User',
            }
        )
        
        if created:
            demo_user.set_password('demo123')
            demo_user.save()
            
            # Add some sample ratings for demo user
            games = list(Game.objects.all()[:10])
            for game in games:
                rating = random.uniform(3.0, 5.0)
                UserGameRating.objects.create(
                    user=demo_user,
                    game=game,
                    rating=rating
                )
            
            self.stdout.write(self.style.SUCCESS('Created demo user with sample ratings'))
        
        return demo_user
