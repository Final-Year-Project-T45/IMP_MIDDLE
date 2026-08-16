import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const executeTask = (request, userId = 'EMP-1092') =>
  api.post('/tasks/execute', { request, user_id: userId });

export const getTasks = () => api.get('/tasks');
export const getTaskDetails = (taskId) => api.get(`/tasks/${taskId}`);

export const getAccounts = () => api.get('/banking/accounts');
export const getAccountDetails = (id) => api.get(`/banking/accounts/${id}`);
export const freezeAccount = (id, reason) => api.post(`/banking/accounts/${id}/freeze`, { reason });
export const unfreezeAccount = (id) => api.post(`/banking/accounts/${id}/unfreeze`);

export const getTransactions = () => api.get('/banking/transactions');
export const executeTransfer = (sender, receiver, amount, description) =>
  api.post('/banking/transfers', { sender_account: sender, receiver_account: receiver, amount: parseFloat(amount), description });

export const getLoans = () => api.get('/banking/loans');
export const disburseLoan = (loanId) => api.post(`/banking/loans/${loanId}/disburse`);

export const getFraudCases = () => api.get('/fraud-cases');
export const getFraudCaseDetails = (id) => api.get(`/fraud-cases/${id}`);

export const getPolicies = () => api.get('/policies');
export const searchPolicies = (query) => api.get(`/policies/search?q=${encodeURIComponent(query)}`);

export const getAuditEvents = () => api.get('/audit-events');

export default api;
