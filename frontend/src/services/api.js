import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true,
});

// Auth
export async function registerUser(email, password, fullName, role) {
  const res = await api.post('/auth/register', { email, password, full_name: fullName, role });
  return res.data;
}

export async function loginUser(email, password) {
  const res = await api.post('/auth/login', { email, password });
  return res.data;
}

export async function logoutUser() {
  const res = await api.post('/auth/logout');
  return res.data;
}

export async function getMe() {
  const res = await api.get('/auth/me');
  return res.data;
}

// Projects
export async function fetchProjects() {
  const res = await api.get('/projects');
  return res.data;
}

export async function createProject(name, description, aiUseCase, aiToolIds = [], facultyAdvisorEmail = '', studentCollaboratorEmail = '', riskContext = {}) {
  const res = await api.post('/projects', {
    name,
    description,
    ai_use_case: aiUseCase,
    ai_tool_ids: aiToolIds,
    faculty_advisor_email: facultyAdvisorEmail,
    student_collaborator_email: studentCollaboratorEmail,
    risk_context: riskContext,
  });
  return res.data;
}

export async function fetchProject(projectId) {
  const res = await api.get(`/projects/${projectId}`);
  return res.data;
}

export async function updateProject(projectId, data) {
  const res = await api.put(`/projects/${projectId}`, data);
  return res.data;
}

export async function toggleCheckpoint(projectId, checkpointId) {
  const res = await api.put(`/projects/${projectId}/checkpoints/${checkpointId}`);
  return res.data;
}

export async function logDecision(projectId, data) {
  const res = await api.post(`/projects/${projectId}/decisions`, data);
  return res.data;
}

export async function exportProjectCSV(projectId) {
  const res = await api.get(`/projects/${projectId}/export`, { responseType: 'blob' });
  return res.data;
}

// AI Tool Registry
export async function fetchTools(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await api.get(`/tools${query ? '?' + query : ''}`);
  return res.data;
}

export async function createTool(data) {
  const res = await api.post('/tools', data);
  return res.data;
}

export async function updateTool(toolId, data) {
  const res = await api.put(`/tools/${toolId}`, data);
  return res.data;
}

export async function fetchToolDetail(toolId) {
  const res = await api.get(`/tools/${toolId}/detail`);
  return res.data;
}

// Checkpoint Comments
export async function fetchCheckpointComments(projectId, checkpointId) {
  const res = await api.get(`/projects/${projectId}/checkpoints/${checkpointId}/comments`);
  return res.data;
}

export async function postCheckpointComment(projectId, checkpointId, text) {
  const res = await api.post(`/projects/${projectId}/checkpoints/${checkpointId}/comments`, { text });
  return res.data;
}

// Verification (automated checkpoint checks)
export async function scanFileForPII(file, scanType = 'pii') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('scan_type', scanType);
  const res = await api.post('/verify/scan-pii', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}

export async function classifyData(description) {
  const res = await api.post('/verify/classify-data', { description });
  return res.data;
}

export async function runBiasAudit(file, outcomeColumn, protectedColumn, positiveValue = '') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('outcome_column', outcomeColumn);
  formData.append('protected_column', protectedColumn);
  if (positiveValue) formData.append('positive_value', positiveValue);
  const res = await api.post('/verify/bias-audit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}

export async function getFileColumns(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/verify/file-columns', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
}

// Dashboard
export async function fetchDashboardStats(scope = 'mine') {
  const res = await api.get(`/dashboard/stats?scope=${scope}`);
  return res.data;
}

// Consent
export async function submitConsent(data) {
  const res = await api.post('/research/consent', data);
  return res.data;
}

// Session tracking
export async function startSession(participantCode, initialScenario) {
  const res = await api.post('/research/session/start', {
    participant_code: participantCode,
    initial_scenario: initialScenario
  });
  return res.data;
}

export async function recordResponse(sessionCode, nodeKey, answerValue, answerLabel, order) {
  const res = await api.post('/research/session/response', {
    session_code: sessionCode,
    node_key: nodeKey,
    answer_value: answerValue,
    answer_label: answerLabel,
    response_order: order
  });
  return res.data;
}

export async function completeSession(sessionCode, terminalNode, riskLevel) {
  const res = await api.post('/research/session/complete', {
    session_code: sessionCode,
    terminal_node: terminalNode,
    risk_level: riskLevel
  });
  return res.data;
}

// Analytics
export async function fetchStats(category = null) {
  const params = category ? `?category=${category}` : '';
  const res = await api.get(`/analytics/stats${params}`);
  return res.data;
}

export async function fetchInsights() {
  const res = await api.get('/analytics/insights');
  return res.data;
}

export async function fetchCategories() {
  const res = await api.get('/analytics/categories');
  return res.data;
}

// Assessment
export async function fetchAssessmentQuestions() {
  const res = await api.get('/assessment/questions');
  return res.data;
}

export async function submitAssessment(answers) {
  const res = await api.post('/assessment/submit', { answers });
  return res.data;
}

// Ethics Assistant API
export async function fetchEthicsStart() {
  const res = await api.get('/ethics/start');
  return res.data;
}

export async function fetchEthicsNode(nodeKey) {
  const res = await api.get(`/ethics/node/${nodeKey}`);
  return res.data;
}

export async function evaluateEthicsPath(answers) {
  const res = await api.post('/ethics/evaluate', { answers });
  return res.data;
}

// Templates & Documents
export async function fetchTemplates() {
  const res = await api.get('/ethics/templates');
  return res.data;
}

export async function fetchTemplate(templateKey) {
  const res = await api.get(`/ethics/templates/${templateKey}`);
  return res.data;
}

export async function generateDocument(templateKey, fieldValues) {
  const res = await api.post('/ethics/generate', {
    template_key: templateKey,
    fields: fieldValues
  });
  return res.data;
}

// Notifications
export async function fetchNotifications() {
  const res = await api.get('/notifications');
  return res.data;
}

export async function markNotificationRead(notificationId) {
  const res = await api.post(`/notifications/${notificationId}/read`);
  return res.data;
}

export async function markAllNotificationsRead() {
  const res = await api.post('/notifications/read-all');
  return res.data;
}

