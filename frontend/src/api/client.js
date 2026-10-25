import axios from 'axios';

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000/api', timeout: 20000 });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cybersahak_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use((response) => response, (error) => {
  if (error.response?.status === 401) {
    localStorage.removeItem('cybersahak_token');
    localStorage.removeItem('cybersahak_user');
    if (window.location.pathname !== '/login') window.location.assign('/login?expired=1');
  }
  return Promise.reject(error);
});
export default api;
