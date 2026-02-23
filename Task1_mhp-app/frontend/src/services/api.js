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

 
  batchAdminUpdateParticipation: (updates) =>
    api.post('/api/meals/participation/admin/batch', { updates }),

  getTodayHeadcount: () => api.get('/api/meals/headcount/today'),

  getHeadcount: (targetDate) =>
    api.get(`/api/meals/headcount/${targetDate}`),

  getTeamHeadcountToday: () =>
    api.get('/api/meals/headcount/team/today'),

  getTeamHeadcount: (targetDate) =>
    api.get(`/api/meals/headcount/team/${targetDate}`),

  getMealConfig: () => api.get('/api/meals/config'),

  updateMealConfig: (mealType, enabled) =>
    api.put('/api/meals/config', { meal_type: mealType, enabled }),

  bulkUpdate: (data) =>
    api.post('/api/meals/participation/bulk', data),

  setException: (data) =>
    api.post('/api/meals/participation/exception', data),

  setRange: ({ startDate, endDate, meals }) =>
    api.post('/api/meals/participation/range', {
      start_date: startDate,
      end_date: endDate,
      meals,
    }),
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

// ===========================
// Teams API
// ===========================

export const teamsAPI = {
  getTeams: () => api.get('/api/teams'),

  getMyTeamParticipation: (targetDate) =>
    api.get('/api/teams/me', { params: { target_date: targetDate } }),

  getAllTeamParticipation: (targetDate) =>
    api.get('/api/teams/all', { params: { target_date: targetDate } }),

  getTeamParticipation: (teamName, targetDate) =>
    api.get(`/api/teams/${encodeURIComponent(teamName)}`, {
      params: { target_date: targetDate },
    }),
};

// ===========================
// Work Locations API
// ===========================

export const workLocationsAPI = {
  set: (targetDate, location) =>
    api.put('/api/work-locations', { date: targetDate, location }),

  getMine: (targetDate) =>
    api.get('/api/work-locations/me', { params: { target_date: targetDate } }),

  getByDate: (targetDate) =>
    api.get('/api/work-locations/date', { params: { target_date: targetDate } }),

  adminSet: (userId, targetDate, location) =>
    api.put('/api/work-locations/admin', {
      user_id: userId,
      date: targetDate,
      location,
    }),
};

// ===========================
// Special Days API
// ===========================

export const specialDaysAPI = {
  getByDate: (targetDate) =>
    api.get('/api/special-days', { params: { date: targetDate } }),

  getRange: (startDate, endDate) =>
    api.get('/api/special-days/range', { params: { start: startDate, end: endDate } }),

  create: (date, dayType, note = '') =>
    api.post('/api/special-days', { date, day_type: dayType, note }),

  delete: (id) => api.delete(`/api/special-days/${id}`),
};

// ===========================
// Headcount Breakdown API
// ===========================

export const headcountAPI = {
  byTeam: (targetDate, team = null) =>
    api.get('/api/headcount/by-team', {
      params: { target_date: targetDate, ...(team ? { team } : {}) },
    }),

  byLocation: (targetDate, team = null) =>
    api.get('/api/headcount/by-location', {
      params: { target_date: targetDate, ...(team ? { team } : {}) },
    }),
};

// ===========================
// Announcements API
// ===========================

export const announcementsAPI = {
  createDraft: (title, body, audience, scheduledAt = null, expiry = null) =>
    api.post('/api/announcements/draft', {
      title,
      body,
      audience,
      ...(scheduledAt ? { scheduled_at: scheduledAt } : {}),
      ...(expiry ? { expiry } : {}),
    }),

  list: (statusFilter = null) =>
    api.get('/api/announcements/drafts', {
      params: statusFilter ? { status: statusFilter } : {},
    }),

  publish: (id, scheduledAt = null) =>
    api.post(`/api/announcements/${id}/publish`, {
      ...(scheduledAt ? { scheduled_at: scheduledAt } : {}),
    }),

  /** Fetch published announcements visible to the current user */
  getPublished: () => api.get('/api/announcements/published'),

  /** Delete an announcement by ID */
  delete: (id) => api.delete(`/api/announcements/${id}`),
};

// ===========================
// WFH Periods API
// ===========================

export const wfhPeriodsAPI = {
  list: ({ employeeId = null, team = null, startDate = null, endDate = null, page = 1, pageSize = 50 } = {}) =>
    api.get('/api/wfh-periods', {
      params: {
        ...(employeeId ? { employee_id: employeeId } : {}),
        ...(team ? { team } : {}),
        ...(startDate ? { start_date: startDate } : {}),
        ...(endDate ? { end_date: endDate } : {}),
        page,
        page_size: pageSize,
      },
    }),

  create: ({ employeeId, startDate, endDate, reason = null }) =>
    api.post('/api/wfh-periods', {
      employee_id: employeeId,
      start_date: startDate,
      end_date: endDate,
      ...(reason ? { reason } : {}),
    }),

  update: (id, { startDate = null, endDate = null, reason = null }) =>
    api.patch(`/api/wfh-periods/${id}`, {
      ...(startDate ? { start_date: startDate } : {}),
      ...(endDate ? { end_date: endDate } : {}),
      ...(reason !== null ? { reason } : {}),
    }),

  delete: (id) => api.delete(`/api/wfh-periods/${id}`),
};

// ===========================
// SSE Helpers
// ===========================

export const sseAPI = {
  /** Fetch a short-lived (60 s), single-use token for the SSE stream. */
  getSseToken: () => api.get('/api/auth/sse-token').then((r) => r.data),

  /** Build the SSE stream URL after obtaining a fresh token. */
  getStreamUrl: async (date = null) => {
    const { token } = await sseAPI.getSseToken();
    let url = `${API_BASE_URL}/api/stream/headcount?token=${encodeURIComponent(token)}`;
    if (date) url += `&date=${encodeURIComponent(date)}`;
    return url;
  },
};

export default api;
