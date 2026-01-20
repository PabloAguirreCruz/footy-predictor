import React, { useState, useEffect } from 'react';
import { getMatches, getPrediction } from './services/api';
import './App.css';

function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predictions, setPredictions] = useState({});
  const [loadingPrediction, setLoadingPrediction] = useState(null);

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    try {
      const response = await getMatches();
      setMatches(response.data.matches || []);
      setLoading(false);
    } catch (err) {
      setError('Failed to load matches');
      setLoading(false);
    }
  };

  const handleGetPrediction = async (match) => {
  setLoadingPrediction(match.id);
  try {
    const response = await getPrediction(match.home_team.id, match.away_team.id);
    setPredictions(prev => ({
      ...prev,
      [match.id]: response.data.prediction
    }));
  } catch (err) {
    console.error('Failed to get prediction:', err);
  }
  setLoadingPrediction(null);
};

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="app">
        <div className="loading">Loading matches...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <h1>⚽ Footy Predictor</h1>
        <p>La Liga Match Predictions</p>
      </header>

      <main className="main">
        <div className="matches-grid">
          {matches.map(match => (
            <div key={match.id} className="match-card">
              <div className="match-date">{formatDate(match.date)}</div>
              <div className="match-status">{match.status}</div>
              
              <div className="teams">
                <div className="team home">
                  <img src={match.home_team.crest} alt={match.home_team.name} className="crest" />
                  <span className="team-name">{match.home_team.name}</span>
                </div>
                
                <div className="vs">VS</div>
                
                <div className="team away">
                  <img src={match.away_team.crest} alt={match.away_team.name} className="crest" />
                  <span className="team-name">{match.away_team.name}</span>
                </div>
              </div>

              {match.score.home !== null && (
                <div className="score">
                  {match.score.home} - {match.score.away}
                </div>
              )}

              <button 
                className="predict-btn"
                onClick={() => handleGetPrediction(match)}
                disabled={loadingPrediction === match.id}
              >
                {loadingPrediction === match.id ? 'Loading...' : 'Get Prediction'}
              </button>

              {predictions[match.id] && (
  <div className="prediction">
    <h4>Prediction</h4>
    <div className="prediction-result">
      {predictions[match.id].predicted_outcome === 'HOME_WIN' 
        ? match.home_team.name 
        : predictions[match.id].predicted_outcome === 'AWAY_WIN'
        ? match.away_team.name
        : 'Draw'}
    </div>
    <div className="confidence">
      Confidence: {predictions[match.id].confidence}%
    </div>
    <div className="predicted-score">
      Predicted: {predictions[match.id].predicted_score?.home} - {predictions[match.id].predicted_score?.away}
    </div>
    <div className="probabilities">
      <span>H: {predictions[match.id].probabilities?.home_win}%</span>
      <span>D: {predictions[match.id].probabilities?.draw}%</span>
      <span>A: {predictions[match.id].probabilities?.away_win}%</span>
    </div>
  </div>
)}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

export default App;
