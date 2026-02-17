import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach Bearer token to every request if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      // Only redirect if not already on login/register
      if (
        !window.location.pathname.includes('/login') &&
        !window.location.pathname.includes('/register')
      ) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ===========================
// Auth API
// ===========================

export const authAPI = {
  login: (email, password) =>
    api.post('/api/auth/login', { email, password }),

  register: (name, email, password, team) =>
    api.post('/api/auth/register', { name, email, password, team }),

  // Kept for backwards compat but prefer usersAPI.getMe
  getMe: () => api.get('/api/users/me'),
};

// ===========================
// Meals API
// ===========================

export const mealsAPI = {
  getTodayMeals: () => api.get('/api/meals/today'),

  getUserMeals: (userId, targetDate) =>
    api.get(`/api/meals/user/${userId}`, {
      params: { target_date: targetDate },
    }),

  updateParticipation: (userId, targetDate, mealType, isParticipating) =>
    api.put(`/api/meals/${userId}/${targetDate}/${mealType}`, {
      is_participating: isParticipating,
    }),

  adminUpdateParticipation: (userId, mealType, isParticipating) =>
    api.post('/api/meals/participation/admin', {
      user_id: userId,
      meal_type: mealType,
      is_participating: isParticipating,
    }),

  getTodayHeadcount: () => api.get('/api/meals/headcount/today'),

  getHeadcount: (targetDate) =>
    api.get(`/api/meals/headcount/${targetDate}`),

  getTeamHeadcountToday: () =>
    api.get('/api/meals/headcount/team/today'),

  getTeamHeadcount: (targetDate) =>
    api.get(`/api/meals/headcount/team/${targetDate}`),
};

// ===========================
// Users API
// ===========================

export const usersAPI = {
  getAllUsers: () => api.get('/api/users'),

  getMe: () => api.get('/api/users/me'),

  getTeamUsers: () => api.get('/api/users/team'),

  getUser: (userId) => api.get(`/api/users/${userId}`),

  createUser: (data) => api.post('/api/users/create', data),

  updateUser: (userId, data) => api.put(`/api/users/${userId}`, data),

  deactivateUser: (userId) => api.delete(`/api/users/${userId}`),
};

export default api;
