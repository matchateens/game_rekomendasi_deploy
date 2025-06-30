# Game Recommender System

A Django-based game recommendation system that provides personalized game suggestions using hybrid recommendation algorithms.

## Features

- **Advanced Hybrid Recommendation Engine**: 
  - K-Means Clustering (30%)
  - Content-Based Filtering (30%)
  - Collaborative Filtering (20%)
  - Popularity-Based Recommendations (20%)
- **Interactive Category Browsing**: Browse games by genres, publishers, ESRB ratings, and rating ranges
- **Clickable Menu System**: Enhanced navigation with visual category cards
- **Game Details**: Comprehensive game information with similar game suggestions
- **User Dashboard**: Personalized recommendations and user statistics
- **Search Functionality**: Advanced search with personalized ranking
- **Responsive Design**: Mobile-friendly interface

## Technology Stack

- **Backend**: Django 5.2.3
- **Database**: SQLite (development)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5.3
- **Machine Learning**: 
  - scikit-learn for K-Means clustering and similarity calculations
  - StandardScaler, OneHotEncoder, MultiLabelBinarizer for feature preprocessing
  - Cosine similarity for content-based filtering
- **Data Processing**: pandas, numpy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/matchateens/game-recommender-system.git
cd game-recommender-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Import game data:
```bash
python manage.py import_csv
```

6. Train recommendation models:
```bash
python manage.py train_recommendations
```

7. Run the development server:
```bash
python manage.py runserver
```

## Project Structure

```
game-recommender-system/
├── config/                 # Django settings
├── games/                  # Main application
│   ├── management/         # Custom management commands
│   ├── migrations/         # Database migrations
│   ├── static/            # CSS, JS files
│   ├── templates/         # HTML templates
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL routing
│   └── recommendation.py  # Recommendation engine
├── games.csv              # Game dataset
├── requirements.txt       # Python dependencies
└── manage.py             # Django management script
```

## Key Components

### Recommendation Engine
- **Content-based filtering**: Recommends games based on game features
- **Collaborative filtering**: Recommends games based on user behavior
- **Hybrid approach**: Combines both methods for better accuracy

### Category Navigation
- **Genres**: Browse games by genre with visual cards
- **Publishers**: Explore games by publisher
- **ESRB Ratings**: Filter by age-appropriate content
- **Rating Ranges**: Find games by user rating scores

### User Features
- Game rating and bookmarking
- Personalized recommendations
- Search with preference-based ranking
- User dashboard with statistics

## Usage

1. **Browse Categories**: Click on genre, publisher, ESRB, or rating cards to view filtered games
2. **Search Games**: Use the search bar for finding specific games
3. **Rate Games**: Click on games to view details and rate them
4. **Get Recommendations**: Visit the dashboard for personalized suggestions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Contact

- GitHub: [@matchateens](https://github.com/matchateens)
- Email: fatincahya69@gmail.com
