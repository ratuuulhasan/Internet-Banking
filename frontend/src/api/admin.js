import api from './axios';

export const adminApi = {
  // Dashboard
  getStats: () => api.get('/admin/stats/'),
  getActivity: () => api.get('/admin/activity/'),

  // Users
  listUsers: (params) => api.get('/admin/users/', { params }),
  blockUser: (id) => api.post(`/admin/users/${id}/block/`),
  unblockUser: (id) => api.post(`/admin/users/${id}/unblock/`),
  changeRole: (id, role) => api.post(`/admin/users/${id}/change_role/`, { role }),

  // KYC
  listKYC: (params) => api.get('/kyc/', { params }),
  approveKYC: (id, status, remarks) =>
    api.post(`/kyc/${id}/approve/`, { status, remarks }),

  // Fraud
  listFraudAlerts: () => api.get('/admin/fraud-alerts/'),
  decideFraud: (txnId, decision) =>
    api.post('/admin/fraud-alerts/', { transaction_id: txnId, decision }),

  // Loans
  listLoans: () => api.get('/loans/'),
  decideLoan: (id, status) =>
    api.post(`/loans/${id}/decide/`, { status }),

  // Complaints
  listComplaints: () => api.get('/complaints/'),
  updateComplaint: (id, data) =>
    api.post(`/complaints/${id}/update_status/`, data),
};