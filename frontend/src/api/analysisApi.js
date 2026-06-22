import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail;
    const errorMessage =
      (Array.isArray(detail)
        ? detail
            .map((item) => {
              const location = Array.isArray(item.loc)
                ? item.loc.filter((part) => part !== 'body').join('.')
                : 'request';
              return `${location}: ${item.msg}`;
            })
            .join('; ')
        : detail) ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';

    console.error('API Error:', errorMessage);

    return Promise.reject(new Error(errorMessage));
  }
);

export const analysisApi = {
  listParcels: async () => {
    return await apiClient.get('/parcels');
  },

  /**
   * Run the main land analysis
   * @param {Object} payload - The parcel data and buffers
   */
  analyzeParcel: async (payload) => {
    return await apiClient.post('/analysis', payload);
  },

  /**
   * Exclude a specific geographic area from the buildable land
   * @param {Object} payload - The geometry to exclude and current state
   */
  excludeArea: async (payload) => {
    return await apiClient.post('/exclude', { ...payload, edit_type: 'exclude' });
  },

  /**
   * Restore a previously excluded geographic area
   * @param {Object} payload - The geometry to restore and current state
   */
  restoreArea: async (payload) => {
    return await apiClient.post('/restore', { ...payload, edit_type: 'restore' });
  },

  /**
   * Get the current configuration and default buffers
   */
  getConfig: async () => {
    return await apiClient.get('/config');
  },

};
