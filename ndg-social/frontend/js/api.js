/**
 * api.js — FastAPI 백엔드 fetch 래퍼
 * 토큰 관리, 에러 핸들링, JSON 파싱 통합
 */

const API_BASE = '';  // 같은 origin 사용

// ── 토큰 관리 ─────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem('ndg_token') || '';
}

function setToken(token) {
  localStorage.setItem('ndg_token', token);
}

function clearToken() {
  localStorage.removeItem('ndg_token');
}

// ── 공통 fetch ────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  // FormData인 경우 Content-Type 헤더 제거 (브라우저가 자동 설정)
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  const response = await fetch(API_BASE + path, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
    // 로그인 없이 접근 허용 — 리디렉션 없음
  }

  let data;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else if (contentType.includes('text/html')) {
    data = await response.text();
  } else {
    data = await response.blob();
  }

  if (!response.ok) {
    const message = typeof data === 'object' ? (data.detail || '오류 발생') : '오류 발생';
    throw new Error(message);
  }

  return data;
}

// ── Auth API ──────────────────────────────────────────────────────

async function apiLogin(email, password) {
  const data = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (data.access_token) {
    setToken(data.access_token);
  }
  return data;
}

async function apiGetMe() {
  return apiFetch('/api/auth/me');
}

async function apiRegister(email, name, password, role = 'editor') {
  return apiFetch('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, name, password, role }),
  });
}

// ── Reports API ───────────────────────────────────────────────────

async function apiGetReports() {
  return apiFetch('/api/reports');
}

async function apiCreateReport(title, clientName, reportMonth) {
  return apiFetch('/api/reports', {
    method: 'POST',
    body: JSON.stringify({ title, client_name: clientName, report_month: reportMonth }),
  });
}

async function apiGetReport(reportId) {
  return apiFetch(`/api/reports/${reportId}`);
}

async function apiDeleteReport(reportId) {
  return apiFetch(`/api/reports/${reportId}`, { method: 'DELETE' });
}

async function apiUploadExcel(reportId, file, followersStart, followersEnd, sheetName, kpiSheetName) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('followers_start', followersStart);
  formData.append('followers_end', followersEnd);
  if (sheetName != null) formData.append('sheet_name', sheetName);
  if (kpiSheetName != null) formData.append('kpi_sheet_name', kpiSheetName);
  return apiFetch(`/api/reports/${reportId}/upload`, {
    method: 'POST',
    body: formData,
    headers: {},
  });
}

async function apiGetReportData(reportId, dataType) {
  return apiFetch(`/api/reports/${reportId}/data/${dataType}`);
}

async function apiUpdateSlide(reportId, slideNumber, fieldKey, newValue) {
  return apiFetch(`/api/reports/${reportId}/slides/${slideNumber}`, {
    method: 'PUT',
    body: JSON.stringify({ field_key: fieldKey, new_value: newValue }),
  });
}

async function apiSaveDraft(reportId) {
  return apiFetch(`/api/reports/${reportId}/draft`, { method: 'PUT' });
}

async function apiGetVersion(reportId, versionNumber) {
  return apiFetch(`/api/reports/${reportId}/versions/${versionNumber}`);
}

async function apiRestoreVersion(reportId, versionNumber) {
  return apiFetch(`/api/reports/${reportId}/versions/${versionNumber}/restore`, { method: 'POST' });
}

async function apiGetVersions(reportId) {
  return apiFetch(`/api/reports/${reportId}/versions`);
}

async function apiCreateVersion(reportId, versionLabel) {
  return apiFetch(`/api/reports/${reportId}/versions`, {
    method: 'POST',
    body: JSON.stringify({ version_label: versionLabel }),
  });
}

async function apiApproveReport(reportId) {
  return apiFetch(`/api/reports/${reportId}/approve`, { method: 'POST' });
}

// ── Pipeline API ──────────────────────────────────────────────────

async function apiStartPipeline(reportId, full = true) {
  return apiFetch(`/api/pipeline/${reportId}/start?full=${full}`, { method: 'POST' });
}

async function apiRestartPipeline(reportId) {
  return apiFetch(`/api/pipeline/${reportId}/restart`, { method: 'POST' });
}

async function apiRunAgent(reportId, agentSlug) {
  return apiFetch(`/api/pipeline/${reportId}/run/${agentSlug}`, { method: 'POST' });
}

async function apiGetPipelineStatus(reportId) {
  return apiFetch(`/api/pipeline/${reportId}/status`);
}

async function apiGetChangeLog(reportId) {
  return apiFetch(`/api/pipeline/${reportId}/change-log`);
}

// ── Export API ────────────────────────────────────────────────────

async function apiGetHtmlPreview(reportId) {
  return apiFetch(`/api/export/${reportId}/html`);
}

async function apiExportPdf(reportId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/export/${reportId}/pdf`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'PDF 생성 실패');
  }
  return response.blob();
}

async function apiExportPptx(reportId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/export/${reportId}/pptx`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'PPT 생성 실패');
  }
  return response.blob();
}

// ── 토스트 알림 ───────────────────────────────────────────────────

function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'none';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── 유틸 ─────────────────────────────────────────────────────────

function getReportIdFromUrl() {
  const parts = window.location.pathname.split('/');
  return parseInt(parts[parts.length - 1]);
}

function formatNumber(n) {
  return Number(n).toLocaleString('ko-KR');
}

function formatMonth(yyyyMm) {
  if (!yyyyMm) return '';
  const [y, m] = yyyyMm.split('-');
  return `${y}년 ${parseInt(m)}월`;
}

async function apiKpiSummary() {
  return apiFetch('/api/reports/kpi-summary');
}

async function apiDuplicateReport(reportId) {
  return apiFetch(`/api/reports/${reportId}/duplicate`, { method: 'POST' });
}

async function apiDirectInput(reportId, payload) {
  return apiFetch(`/api/reports/${reportId}/direct-input`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

async function apiExportExcel(reportId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/reports/${reportId}/export/excel`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Excel 내보내기 실패');
  }
  return response.blob();
}

async function apiGenerateExcelPreview(payload) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/reports/generate-excel-preview`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Excel 미리보기 생성 실패');
  }
  return response.blob();
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
