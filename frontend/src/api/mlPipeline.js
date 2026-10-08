import api from './axios';

export const mlApi = {
  getStats: () => api.get('/admin/ml/stats/'),
  listVersions: () => api.get('/admin/ml/versions/'),
  getActive: () => api.get('/admin/ml/versions/active/'),
  activateVersion: (id) => api.post(`/admin/ml/versions/${id}/activate/`),
  listJobs: () => api.get('/admin/ml/jobs/'),
  triggerRetrain: () => api.post('/admin/ml/jobs/trigger/'),
  getJob: (id) => api.get(`/admin/ml/jobs/${id}/`),
  listDrift: () => api.get('/admin/ml/drift/'),
};