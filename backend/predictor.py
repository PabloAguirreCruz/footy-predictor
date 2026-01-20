"""
Footy Predictor - Match Prediction Module
Uses the Football-Data.org API for La Liga predictions.
"""
from typing import Dict, Any, Optional, List
from api_football import FootballAPI


def get_match_prediction(
    home_team_id: int,
    away_team_id: int,
    competition_code: str = "PD",
    api: Optional[FootballAPI] = None
) -> Dict[str, Any]:
    """Generate a match prediction based on team statistics and standings."""
    if api is None:
        api = FootballAPI()
    
    standings_response = api.get_standings(competition_code)
    standings = _extract_standings_table(standings_response)
    
    home_stats = _get_team_from_standings(standings, home_team_id)
    away_stats = _get_team_from_standings(standings, away_team_id)
    
    try:
        home_matches = api.get_team_matches(home_team_id, status="FINISHED", limit=5)
        away_matches = api.get_team_matches(away_team_id, status="FINISHED", limit=5)
        home_form = _calculate_form(home_matches, home_team_id)
        away_form = _calculate_form(away_matches, away_team_id)
    except Exception:
        home_form = 50
        away_form = 50
    
    prediction = _calculate_prediction(
        home_stats=home_stats,
        away_stats=away_stats,
        home_form=home_form,
        away_form=away_form
    )
    
    return prediction


def get_upcoming_predictions(
    competition_code: str = "PD",
    api: Optional[FootballAPI] = None
) -> List[Dict[str, Any]]:
    """Get predictions for all upcoming matches in a competition."""
    if api is None:
        api = FootballAPI()
    
    standings_response = api.get_standings(competition_code)
    standings = _extract_standings_table(standings_response)
    
    matches_response = api.get_matches(competition_code, status="SCHEDULED")
    matches = matches_response.get("matches", [])
    
    predictions = []
    
    for match in matches:
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        
        home_id = home_team.get("id")
        away_id = away_team.get("id")
        
        if not home_id or not away_id:
            continue
        
        home_stats = _get_team_from_standings(standings, home_id)
        away_stats = _get_team_from_standings(standings, away_id)
        
        prediction = _calculate_prediction(
            home_stats=home_stats,
            away_stats=away_stats,
            home_form=50,
            away_form=50
        )
        
        prediction["match_id"] = match.get("id")
        prediction["home_team"] = home_team.get("name", "Unknown")
        prediction["away_team"] = away_team.get("name", "Unknown")
        prediction["home_team_id"] = home_id
        prediction["away_team_id"] = away_id
        prediction["match_date"] = match.get("utcDate")
        prediction["matchday"] = match.get("matchday")
        prediction["status"] = match.get("status")
        
        predictions.append(prediction)
    
    return predictions


def _extract_standings_table(standings_response: Dict) -> List[Dict]:
    """Extract the standings table from API response."""
    standings_list = standings_response.get("standings", [])
    
    for standing in standings_list:
        if standing.get("type") == "TOTAL":
            return standing.get("table", [])
    
    if standings_list:
        return standings_list[0].get("table", [])
    
    return []


def _get_team_from_standings(standings: List[Dict], team_id: int) -> Dict[str, Any]:
    """Get team data from standings list."""
    for team in standings:
        if team.get("team", {}).get("id") == team_id:
            return team
    
    return {
        "position": 10,
        "playedGames": 0,
        "won": 0,
        "draw": 0,
        "lost": 0,
        "points": 0,
        "goalsFor": 0,
        "goalsAgainst": 0,
        "goalDifference": 0,
        "team": {"id": team_id, "name": "Unknown"}
    }


def _calculate_form(matches_response: Dict, team_id: int) -> float:
    """Calculate team form (0-100) based on recent matches."""
    matches = matches_response.get("matches", [])
    
    if not matches:
        return 50
    
    points = 0
    max_points = len(matches) * 3
    
    for match in matches:
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        score = match.get("score", {}).get("fullTime", {})
        
        home_goals = score.get("home", 0) or 0
        away_goals = score.get("away", 0) or 0
        
        is_home = home_team.get("id") == team_id
        
        if is_home:
            if home_goals > away_goals:
                points += 3
            elif home_goals == away_goals:
                points += 1
        else:
            if away_goals > home_goals:
                points += 3
            elif home_goals == away_goals:
                points += 1
    
    if max_points == 0:
        return 50
    
    return (points / max_points) * 100


def _calculate_prediction(
    home_stats: Dict,
    away_stats: Dict,
    home_form: float,
    away_form: float
) -> Dict[str, Any]:
    """Calculate match prediction based on standings and form."""
    home_data = {
        "position": home_stats.get("position", 10),
        "points": home_stats.get("points", 0),
        "played": home_stats.get("playedGames", 0),
        "won": home_stats.get("won", 0),
        "draw": home_stats.get("draw", 0),
        "lost": home_stats.get("lost", 0),
        "goals_for": home_stats.get("goalsFor", 0),
        "goals_against": home_stats.get("goalsAgainst", 0),
        "goal_diff": home_stats.get("goalDifference", 0),
        "form": home_form,
        "name": home_stats.get("team", {}).get("name", "Home Team")
    }
    
    away_data = {
        "position": away_stats.get("position", 10),
        "points": away_stats.get("points", 0),
        "played": away_stats.get("playedGames", 0),
        "won": away_stats.get("won", 0),
        "draw": away_stats.get("draw", 0),
        "lost": away_stats.get("lost", 0),
        "goals_for": away_stats.get("goalsFor", 0),
        "goals_against": away_stats.get("goalsAgainst", 0),
        "goal_diff": away_stats.get("goalDifference", 0),
        "form": away_form,
        "name": away_stats.get("team", {}).get("name", "Away Team")
    }
    
    home_strength = _calculate_team_strength(home_data, is_home=True)
    away_strength = _calculate_team_strength(away_data, is_home=False)
    
    draw_factor = 0.25 + (0.1 if abs(home_strength - away_strength) < 0.15 else 0)
    total = home_strength + away_strength + draw_factor
    
    home_win_prob = round(home_strength / total * 100, 1)
    away_win_prob = round(away_strength / total * 100, 1)
    draw_prob = round(100 - home_win_prob - away_win_prob, 1)
    
    if home_win_prob > away_win_prob and home_win_prob > draw_prob:
        predicted_outcome = "HOME_WIN"
        confidence = home_win_prob
    elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
        predicted_outcome = "AWAY_WIN"
        confidence = away_win_prob
    else:
        predicted_outcome = "DRAW"
        confidence = draw_prob
    
    # Predict score that matches the outcome
    predicted_score = _predict_scoreline(home_data, away_data, predicted_outcome)
    
    return {
        "home_team": home_data["name"],
        "away_team": away_data["name"],
        "probabilities": {
            "home_win": home_win_prob,
            "draw": draw_prob,
            "away_win": away_win_prob
        },
        "predicted_outcome": predicted_outcome,
        "confidence": confidence,
        "predicted_score": predicted_score,
        "team_stats": {
            "home": {
                "position": home_data["position"],
                "points": home_data["points"],
                "form": round(home_data["form"], 1),
                "goals_for": home_data["goals_for"],
                "goals_against": home_data["goals_against"],
                "goal_diff": home_data["goal_diff"]
            },
            "away": {
                "position": away_data["position"],
                "points": away_data["points"],
                "form": round(away_data["form"], 1),
                "goals_for": away_data["goals_for"],
                "goals_against": away_data["goals_against"],
                "goal_diff": away_data["goal_diff"]
            }
        }
    }


def _calculate_team_strength(data: Dict, is_home: bool) -> float:
    """Calculate team strength based on standings data."""
    base_strength = 1.0
    
    position = data.get("position", 10)
    position_factor = (21 - position) / 20
    base_strength *= (0.6 + 0.8 * position_factor)
    
    played = data.get("played", 1) or 1
    ppg = data.get("points", 0) / played
    ppg_factor = ppg / 3.0
    base_strength *= (0.7 + 0.6 * ppg_factor)
    
    goal_diff = data.get("goal_diff", 0)
    gd_normalized = (goal_diff + 40) / 80
    gd_normalized = max(0.2, min(1.0, gd_normalized))
    base_strength *= (0.8 + 0.4 * gd_normalized)
    
    form = data.get("form", 50)
    form_factor = form / 100
    base_strength *= (0.8 + 0.4 * form_factor)
    
    if is_home:
        base_strength *= 1.15
    
    return base_strength


def _predict_scoreline(home_data: Dict, away_data: Dict, outcome: str) -> Dict[str, int]:
    """Predict the scoreline that matches the predicted outcome."""
    played_home = home_data.get("played", 1) or 1
    played_away = away_data.get("played", 1) or 1
    
    # Average goals per game
    home_avg_scored = home_data.get("goals_for", 0) / played_home
    away_avg_scored = away_data.get("goals_for", 0) / played_away
    
    # Base expected goals
    home_expected = home_avg_scored * 1.1  # Home boost
    away_expected = away_avg_scored * 0.9  # Away reduction
    
    # Round to get base scores
    home_goals = max(0, round(home_expected))
    away_goals = max(0, round(away_expected))
    
    # Adjust score to match the predicted outcome
    if outcome == "HOME_WIN":
        if home_goals <= away_goals:
            home_goals = away_goals + 1
    elif outcome == "AWAY_WIN":
        if away_goals <= home_goals:
            away_goals = home_goals + 1
    elif outcome == "DRAW":
        # Set both to the average
        avg = round((home_goals + away_goals) / 2)
        home_goals = avg
        away_goals = avg
    
    # Keep scores realistic (0-5 range typically)
    home_goals = min(5, max(0, home_goals))
    away_goals = min(5, max(0, away_goals))
    
    # Final check to ensure outcome matches
    if outcome == "HOME_WIN" and home_goals <= away_goals:
        home_goals = away_goals + 1
    elif outcome == "AWAY_WIN" and away_goals <= home_goals:
        away_goals = home_goals + 1
    elif outcome == "DRAW":
        away_goals = home_goals
    
    return {
        "home": home_goals,
        "away": away_goals
    }


if __name__ == "__main__":
    print("Testing Footy Predictor...")
    print("=" * 60)
    
    try:
        api = FootballAPI()
        
        print("\nGenerating predictions for upcoming La Liga matches...\n")
        predictions = get_upcoming_predictions("PD", api)
        
        for pred in predictions[:5]:
            print(f"Match: {pred['home_team']} vs {pred['away_team']}")
            print(f"Prediction: {pred['predicted_outcome']} ({pred['confidence']:.1f}%)")
            print(f"Score: {pred['predicted_score']['home']}-{pred['predicted_score']['away']}")
            print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")
