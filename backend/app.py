from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, 
    create_access_token, 
    jwt_required, 
    get_jwt_identity
)
from datetime import timedelta
import os
from dotenv import load_dotenv

# Import our modules
from api_football import FootballAPI
from predictor import get_match_prediction, get_upcoming_predictions
from models import (
    create_user,
    authenticate_user,
    get_user_by_id,
    save_prediction,
    get_user_predictions,
    get_prediction_by_fixture,
    get_leaderboard
)

load_dotenv()

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'dev-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
jwt = JWTManager(app)

# Initialize Football API
try:
    football_api = FootballAPI()
except ValueError as e:
    print(f"Warning: Football API not configured - {e}")
    football_api = None


# ==================== HELPER FUNCTIONS ====================

def format_match(match):
    """Format a match from the API response"""
    return {
        'id': match.get('id'),
        'home_team': {
            'id': match.get('homeTeam', {}).get('id'),
            'name': match.get('homeTeam', {}).get('name'),
            'crest': match.get('homeTeam', {}).get('crest')
        },
        'away_team': {
            'id': match.get('awayTeam', {}).get('id'),
            'name': match.get('awayTeam', {}).get('name'),
            'crest': match.get('awayTeam', {}).get('crest')
        },
        'date': match.get('utcDate'),
        'status': match.get('status'),
        'matchday': match.get('matchday'),
        'score': {
            'home': match.get('score', {}).get('fullTime', {}).get('home'),
            'away': match.get('score', {}).get('fullTime', {}).get('away')
        }
    }


# ==================== AUTH ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    user, error = create_user(username, email, password)
    
    if error:
        return jsonify({'error': error}), 400
    
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        'message': 'Registration successful',
        'user': user,
        'access_token': access_token
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user, error = authenticate_user(username, password)
    
    if error:
        return jsonify({'error': error}), 401
    
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        'message': 'Login successful',
        'user': user,
        'access_token': access_token
    }), 200


@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user}), 200


# ==================== TEAM ROUTES ====================

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get all La Liga teams"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        response = football_api.get_laliga_teams()
        teams = response.get('teams', [])
        
        formatted = []
        for team in teams:
            formatted.append({
                'id': team.get('id'),
                'name': team.get('name'),
                'short_name': team.get('shortName'),
                'crest': team.get('crest'),
                'venue': team.get('venue')
            })
        
        return jsonify({'teams': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/teams/<int:team_id>', methods=['GET'])
def get_team_details(team_id):
    """Get detailed info for a team"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        team = football_api.get_team(team_id)
        return jsonify({'team': team}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/teams/<int:team_id>/matches', methods=['GET'])
def get_team_matches(team_id):
    """Get matches for a team"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        status = request.args.get('status')  # SCHEDULED, FINISHED, etc.
        limit = request.args.get('limit', 10, type=int)
        
        response = football_api.get_team_matches(team_id, status=status, limit=limit)
        matches = response.get('matches', [])
        
        formatted = [format_match(m) for m in matches]
        
        return jsonify({'matches': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== STANDINGS ROUTES ====================

@app.route('/api/standings', methods=['GET'])
def get_league_standings():
    """Get current La Liga standings"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        response = football_api.get_laliga_standings()
        standings_list = response.get('standings', [])
        
        # Get TOTAL standings (not HOME or AWAY)
        table = []
        for standing in standings_list:
            if standing.get('type') == 'TOTAL':
                table = standing.get('table', [])
                break
        
        # Fallback to first standings
        if not table and standings_list:
            table = standings_list[0].get('table', [])
        
        formatted = []
        for team in table:
            formatted.append({
                'position': team.get('position'),
                'team': {
                    'id': team.get('team', {}).get('id'),
                    'name': team.get('team', {}).get('name'),
                    'crest': team.get('team', {}).get('crest')
                },
                'points': team.get('points'),
                'played': team.get('playedGames'),
                'won': team.get('won'),
                'drawn': team.get('draw'),
                'lost': team.get('lost'),
                'goals_for': team.get('goalsFor'),
                'goals_against': team.get('goalsAgainst'),
                'goal_diff': team.get('goalDifference'),
                'form': team.get('form', '')
            })
        
        return jsonify({'standings': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== MATCH/FIXTURE ROUTES ====================

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """Get La Liga matches"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        status = request.args.get('status')  # SCHEDULED, FINISHED, IN_PLAY, etc.
        matchday = request.args.get('matchday', type=int)
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        response = football_api.get_matches(
            'PD',  # La Liga
            matchday=matchday,
            status=status,
            date_from=date_from,
            date_to=date_to
        )
        matches = response.get('matches', [])
        
        formatted = [format_match(m) for m in matches]
        
        return jsonify({'matches': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/matches/upcoming', methods=['GET'])
def get_upcoming_matches():
    """Get upcoming La Liga matches"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        response = football_api.get_upcoming_laliga_matches()
        matches = response.get('matches', [])
        
        formatted = [format_match(m) for m in matches]
        
        return jsonify({'matches': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/matches/finished', methods=['GET'])
def get_finished_matches():
    """Get finished La Liga matches"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        response = football_api.get_finished_laliga_matches()
        matches = response.get('matches', [])
        
        formatted = [format_match(m) for m in matches]
        
        return jsonify({'matches': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match_details(match_id):
    """Get details for a specific match"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        match = football_api.get_match(match_id)
        return jsonify({'match': format_match(match)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== SCORERS ROUTE ====================

@app.route('/api/scorers', methods=['GET'])
def get_top_scorers():
    """Get La Liga top scorers"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        limit = request.args.get('limit', 10, type=int)
        response = football_api.get_laliga_scorers(limit=limit)
        scorers = response.get('scorers', [])
        
        formatted = []
        for scorer in scorers:
            formatted.append({
                'player': {
                    'id': scorer.get('player', {}).get('id'),
                    'name': scorer.get('player', {}).get('name'),
                    'nationality': scorer.get('player', {}).get('nationality')
                },
                'team': {
                    'id': scorer.get('team', {}).get('id'),
                    'name': scorer.get('team', {}).get('name'),
                    'crest': scorer.get('team', {}).get('crest')
                },
                'goals': scorer.get('goals'),
                'assists': scorer.get('assists'),
                'penalties': scorer.get('penalties')
            })
        
        return jsonify({'scorers': formatted}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PREDICTION ROUTES ====================

@app.route('/api/predict', methods=['POST'])
def predict_match():
    """Get prediction for a match"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    data = request.get_json()
    
    home_team_id = data.get('home_team_id')
    away_team_id = data.get('away_team_id')
    
    if not home_team_id or not away_team_id:
        return jsonify({'error': 'Missing team IDs'}), 400
    
    try:
        prediction = get_match_prediction(home_team_id, away_team_id, api=football_api)
        return jsonify({'prediction': prediction}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/upcoming', methods=['GET'])
def predict_upcoming_matches():
    """Get predictions for all upcoming matches"""
    if not football_api:
        return jsonify({'error': 'Football API not configured'}), 500
    
    try:
        predictions = get_upcoming_predictions('PD', api=football_api)
        return jsonify({'predictions': predictions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predictions', methods=['POST'])
@jwt_required()
def save_user_prediction():
    """Save user's prediction for a match"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    match_id = data.get('match_id')
    home_team = data.get('home_team')
    away_team = data.get('away_team')
    model_prediction = data.get('model_prediction')
    user_prediction = data.get('user_prediction')  # 'home', 'draw', 'away'
    
    if not all([match_id, home_team, away_team, user_prediction]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if user_prediction not in ['home', 'draw', 'away']:
        return jsonify({'error': 'Invalid prediction value'}), 400
    
    # Check if already predicted
    existing = get_prediction_by_fixture(user_id, match_id)
    if existing:
        return jsonify({'error': 'Already predicted this match'}), 400
    
    prediction = save_prediction(
        user_id, match_id, home_team, away_team, 
        model_prediction, user_prediction
    )
    
    return jsonify({
        'message': 'Prediction saved',
        'prediction': prediction
    }), 201


@app.route('/api/predictions', methods=['GET'])
@jwt_required()
def get_my_predictions():
    """Get current user's prediction history"""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 20, type=int)
    
    predictions = get_user_predictions(user_id, limit)
    
    return jsonify({'predictions': predictions}), 200


@app.route('/api/predictions/check/<int:match_id>', methods=['GET'])
@jwt_required()
def check_prediction(match_id):
    """Check if user already predicted a match"""
    user_id = get_jwt_identity()
    
    prediction = get_prediction_by_fixture(user_id, match_id)
    
    return jsonify({
        'has_predicted': prediction is not None,
        'prediction': prediction
    }), 200


# ==================== LEADERBOARD ROUTE ====================

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    """Get top predictors"""
    limit = request.args.get('limit', 10, type=int)
    leaders = get_leaderboard(limit)
    
    return jsonify({'leaderboard': leaders}), 200


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'message': 'Footy Predictor API is running',
        'api_configured': football_api is not None
    }), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000) 