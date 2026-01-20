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

export const getMatches = () => api.get('/matches');
export const getStandings = () => api.get('/standings');
export const getPrediction = (homeTeamId, awayTeamId) => 
  api.post('/predict', { home_team_id: homeTeamId, away_team_id: awayTeamId });
export const healthCheck = () => api.get('/health');

export const register = (userData) => api.post('/auth/register', userData);
export const login = (userData) => api.post('/auth/login', userData);
export const getMe = () => api.get('/auth/me');

export default api;