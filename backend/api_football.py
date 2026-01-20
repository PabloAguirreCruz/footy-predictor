"""
Football-Data.org API Module
https://www.football-data.org/documentation/api

Usage:
    from api_football import FootballAPI
    
    api = FootballAPI()
    standings = api.get_standings("PD")  # PD = La Liga (Primera División)
    matches = api.get_matches("PD")
"""
import os
import requests
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class FootballAPI:
    """Client for the Football-Data.org API v4."""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    # League codes for football-data.org
    # Free tier includes: PL, BL1, SA, PD, FL1, ELC, DED, PPL, BSA, CL, EC, WC
    LEAGUE_CODES = {
        "la_liga": "PD",           # Primera División (Spain)
        "premier_league": "PL",     # Premier League (England)
        "bundesliga": "BL1",        # Bundesliga (Germany)
        "serie_a": "SA",            # Serie A (Italy)
        "ligue_1": "FL1",           # Ligue 1 (France)
        "championship": "ELC",      # Championship (England)
        "eredivisie": "DED",        # Eredivisie (Netherlands)
        "primeira_liga": "PPL",     # Primeira Liga (Portugal)
        "serie_a_brazil": "BSA",    # Série A (Brazil)
        "champions_league": "CL",   # UEFA Champions League
        "euro": "EC",               # European Championship
        "world_cup": "WC",          # FIFA World Cup
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Football API client.
        
        Args:
            api_key: API key from football-data.org. 
                     If not provided, reads from FOOTBALL_DATA_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key required. Pass api_key parameter or set FOOTBALL_DATA_API_KEY environment variable."
            )
        
        self.headers = {
            "X-Auth-Token": self.api_key
        }
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint path (e.g., "/competitions/PD/matches")
            params: Optional query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    # ==================== COMPETITIONS ====================
    
    def get_competitions(self) -> Dict[str, Any]:
        """Get all available competitions."""
        return self._request("/competitions")
    
    def get_competition(self, code: str) -> Dict[str, Any]:
        """
        Get details for a specific competition.
        
        Args:
            code: Competition code (e.g., "PD" for La Liga)
        """
        return self._request(f"/competitions/{code}")
    
    # ==================== MATCHES ====================
    
    def get_matches(self, competition_code: str, matchday: Optional[int] = None, 
                    status: Optional[str] = None, date_from: Optional[str] = None,
                    date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get matches for a competition.
        
        Args:
            competition_code: Competition code (e.g., "PD" for La Liga)
            matchday: Filter by matchday number
            status: Filter by status (SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED, etc.)
            date_from: Filter from date (YYYY-MM-DD)
            date_to: Filter to date (YYYY-MM-DD)
        """
        params = {}
        if matchday:
            params["matchday"] = matchday
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
            
        return self._request(f"/competitions/{competition_code}/matches", params)
    
    def get_all_matches(self, date_from: Optional[str] = None, 
                        date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all matches (across all competitions in your tier).
        
        Args:
            date_from: Filter from date (YYYY-MM-DD)
            date_to: Filter to date (YYYY-MM-DD)
        """
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
            
        return self._request("/matches", params)
    
    def get_match(self, match_id: int) -> Dict[str, Any]:
        """
        Get details for a specific match.
        
        Args:
            match_id: Match ID
        """
        return self._request(f"/matches/{match_id}")
    
    # ==================== STANDINGS ====================
    
    def get_standings(self, competition_code: str) -> Dict[str, Any]:
        """
        Get standings for a competition.
        
        Args:
            competition_code: Competition code (e.g., "PD" for La Liga)
        """
        return self._request(f"/competitions/{competition_code}/standings")
    
    # ==================== TEAMS ====================
    
    def get_teams(self, competition_code: str) -> Dict[str, Any]:
        """
        Get all teams in a competition.
        
        Args:
            competition_code: Competition code (e.g., "PD" for La Liga)
        """
        return self._request(f"/competitions/{competition_code}/teams")
    
    def get_team(self, team_id: int) -> Dict[str, Any]:
        """
        Get details for a specific team.
        
        Args:
            team_id: Team ID
        """
        return self._request(f"/teams/{team_id}")
    
    def get_team_matches(self, team_id: int, status: Optional[str] = None,
                         limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Get matches for a specific team.
        
        Args:
            team_id: Team ID
            status: Filter by status (SCHEDULED, FINISHED, etc.)
            limit: Limit number of results
        """
        params = {}
        if status:
            params["status"] = status
        if limit:
            params["limit"] = limit
            
        return self._request(f"/teams/{team_id}/matches", params)
    
    # ==================== SCORERS ====================
    
    def get_scorers(self, competition_code: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get top scorers for a competition.
        
        Args:
            competition_code: Competition code (e.g., "PD" for La Liga)
            limit: Number of scorers to return
        """
        return self._request(f"/competitions/{competition_code}/scorers", {"limit": limit})
    
    # ==================== PERSONS ====================
    
    def get_person(self, person_id: int) -> Dict[str, Any]:
        """
        Get details for a specific person (player/coach).
        
        Args:
            person_id: Person ID
        """
        return self._request(f"/persons/{person_id}")
    
    def get_person_matches(self, person_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get matches for a specific person.
        
        Args:
            person_id: Person ID
            limit: Number of matches to return
        """
        return self._request(f"/persons/{person_id}/matches", {"limit": limit})
    
    # ==================== LA LIGA HELPERS ====================
    
    def get_laliga_standings(self) -> Dict[str, Any]:
        """Get current La Liga standings."""
        return self.get_standings(self.LEAGUE_CODES["la_liga"])
    
    def get_laliga_matches(self, matchday: Optional[int] = None) -> Dict[str, Any]:
        """Get La Liga matches."""
        return self.get_matches(self.LEAGUE_CODES["la_liga"], matchday=matchday)
    
    def get_laliga_teams(self) -> Dict[str, Any]:
        """Get all La Liga teams."""
        return self.get_teams(self.LEAGUE_CODES["la_liga"])
    
    def get_laliga_scorers(self, limit: int = 10) -> Dict[str, Any]:
        """Get La Liga top scorers."""
        return self.get_scorers(self.LEAGUE_CODES["la_liga"], limit=limit)
    
    def get_upcoming_laliga_matches(self) -> Dict[str, Any]:
        """Get upcoming (scheduled) La Liga matches."""
        return self.get_matches(self.LEAGUE_CODES["la_liga"], status="SCHEDULED")
    
    def get_finished_laliga_matches(self) -> Dict[str, Any]:
        """Get finished La Liga matches."""
        return self.get_matches(self.LEAGUE_CODES["la_liga"], status="FINISHED")


# Convenience function
def get_api(api_key: Optional[str] = None) -> FootballAPI:
    """Get a FootballAPI instance."""
    return FootballAPI(api_key)


# Test the API
if __name__ == "__main__":
    import json
    
    try:
        api = FootballAPI()
        
        print("=" * 50)
        print("Fetching La Liga standings...")
        print("=" * 50)
        standings = api.get_laliga_standings()
        
        # Print top 5 teams
        table = standings.get("standings", [{}])[0].get("table", [])
        for team in table[:5]:
            print(f"{team['position']}. {team['team']['name']} - {team['points']} pts")
        
        print("\n" + "=" * 50)
        print("Fetching upcoming La Liga matches...")
        print("=" * 50)
        matches = api.get_upcoming_laliga_matches()
        
        for match in matches.get("matches", [])[:5]:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            date = match["utcDate"][:10]
            print(f"{date}: {home} vs {away}")
        
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Error: {e}")