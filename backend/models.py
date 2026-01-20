from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/footy-predictor'))
db = client.get_database()

# Collections
users_collection = db['users']
predictions_collection = db['predictions']


# ==================== USER FUNCTIONS ====================

def create_user(username, email, password):
    """Create a new user"""
    # Check if user exists
    if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
        return None, 'Username or email already exists'
    
    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    user = {
        'username': username,
        'email': email,
        'password': hashed,
        'created_at': datetime.utcnow(),
        'predictions_count': 0,
        'correct_predictions': 0
    }
    
    result = users_collection.insert_one(user)
    user['_id'] = str(result.inserted_id)
    del user['password']  # Don't return password
    
    return user, None


def authenticate_user(username, password):
    """Authenticate a user"""
    user = users_collection.find_one({'username': username})
    
    if not user:
        return None, 'User not found'
    
    if bcrypt.checkpw(password.encode('utf-8'), user['password']):
        user['_id'] = str(user['_id'])
        del user['password']
        return user, None
    
    return None, 'Invalid password'


def get_user_by_id(user_id):
    """Get user by ID"""
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        del user['password']
    return user


def update_user_stats(user_id, correct=False):
    """Update user prediction stats"""
    update = {'$inc': {'predictions_count': 1}}
    if correct:
        update['$inc']['correct_predictions'] = 1
    
    users_collection.update_one({'_id': ObjectId(user_id)}, update)


# ==================== PREDICTION FUNCTIONS ====================

def save_prediction(user_id, fixture_id, home_team, away_team, prediction_data, user_prediction):
    """Save a user's prediction"""
    prediction = {
        'user_id': ObjectId(user_id),
        'fixture_id': fixture_id,
        'home_team': home_team,
        'away_team': away_team,
        'model_prediction': prediction_data,
        'user_prediction': user_prediction,  # 'home', 'draw', or 'away'
        'actual_result': None,
        'is_correct': None,
        'created_at': datetime.utcnow()
    }
    
    result = predictions_collection.insert_one(prediction)
    prediction['_id'] = str(result.inserted_id)
    prediction['user_id'] = str(prediction['user_id'])
    
    return prediction


def get_user_predictions(user_id, limit=20):
    """Get user's prediction history"""
    predictions = predictions_collection.find(
        {'user_id': ObjectId(user_id)}
    ).sort('created_at', -1).limit(limit)
    
    result = []
    for pred in predictions:
        pred['_id'] = str(pred['_id'])
        pred['user_id'] = str(pred['user_id'])
        result.append(pred)
    
    return result


def update_prediction_result(fixture_id, home_goals, away_goals):
    """Update predictions with actual match result"""
    if home_goals > away_goals:
        actual_result = 'home'
    elif away_goals > home_goals:
        actual_result = 'away'
    else:
        actual_result = 'draw'
    
    # Find all predictions for this fixture
    predictions = predictions_collection.find({'fixture_id': fixture_id})
    
    for pred in predictions:
        is_correct = pred['user_prediction'] == actual_result
        
        predictions_collection.update_one(
            {'_id': pred['_id']},
            {
                '$set': {
                    'actual_result': actual_result,
                    'actual_score': {'home': home_goals, 'away': away_goals},
                    'is_correct': is_correct
                }
            }
        )
        
        # Update user stats
        update_user_stats(str(pred['user_id']), correct=is_correct)


def get_prediction_by_fixture(user_id, fixture_id):
    """Check if user already predicted this fixture"""
    prediction = predictions_collection.find_one({
        'user_id': ObjectId(user_id),
        'fixture_id': fixture_id
    })
    
    if prediction:
        prediction['_id'] = str(prediction['_id'])
        prediction['user_id'] = str(prediction['user_id'])
    
    return prediction


def get_leaderboard(limit=10):
    """Get top predictors"""
    pipeline = [
        {
            '$match': {'predictions_count': {'$gt': 0}}
        },
        {
            '$project': {
                'username': 1,
                'predictions_count': 1,
                'correct_predictions': 1,
                'accuracy': {
                    '$multiply': [
                        {'$divide': ['$correct_predictions', '$predictions_count']},
                        100
                    ]
                }
            }
        },
        {
            '$sort': {'accuracy': -1, 'predictions_count': -1}
        },
        {
            '$limit': limit
        }
    ]
    
    result = list(users_collection.aggregate(pipeline))
    for user in result:
        user['_id'] = str(user['_id'])
        user['accuracy'] = round(user.get('accuracy', 0), 1)
    
    return result
