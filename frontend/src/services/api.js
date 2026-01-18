import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const register = (userData) => api.post('/auth/register', userData);
export const login = (userData) => api.post('/auth/login', userData);
export const getMe = () => api.get('/auth/me');
export const getTeams = () => api.get('/teams');
export const getTeamStats = (teamId) => api.get(`/teams/${teamId}/stats`);
export const getStandings = () => api.get('/standings');
export const getFixtures = (limit = 10) => api.get(`/fixtures?limit=${limit}`);
export const getPrediction = (homeTeamId, awayTeamId) => 
  api.post('/predict', { home_team_id: homeTeamId, away_team_id: awayTeamId });
export const savePrediction = (predictionData) => api.post('/predictions', predictionData);
export const getMyPredictions = () => api.get('/predictions');
export const checkPrediction = (fixtureId) => api.get(`/predictions/check/${fixtureId}`);
export const getLeaderboard = () => api.get('/leaderboard');

export default api;