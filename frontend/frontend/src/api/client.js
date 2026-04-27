import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 15000,
});

export const getбатters = (params) => api.get("/players/batters", { params });

export const getBowlers = (params) => api.get("/players/bowlers", { params });

export const getPlayerProfile = (name) =>
  api.get(`/players/${encodeURIComponent(name)}/profile`);

export const comparePlayers = (params) =>
  api.get("/players/compare", { params });

export const getMatches = (params) => api.get("/matches/", { params });

export const getMatchTimeline = (matchId, innings) =>
  api.get(`/matches/${matchId}/timeline`, { params: { innings } });

export default api;
