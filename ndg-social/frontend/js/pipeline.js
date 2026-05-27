/**
 * pipeline.js — 보고서 생성 상태 폴링 및 UI 업데이트
 */

let pipelineInterval = null;
const POLL_INTERVAL  = 500; // 0.5초

const STATUS_TEXT = {
  'draft':          '초안',
  'data_uploaded':  '데이터 업로드됨 — 생성 준비 완료',
  'pending_review': '보고서 생성 완료 — 검토 후 승인하세요',
  'approved':       '승인 완료',
  'exported':       '내보내기 완료',
  'failed':         '생성 실패 — 재시도하세요',
};

function startPipelinePolling(reportId) {
  if (pipelineInterval) stopPipelinePolling();
  pipelineInterval = setInterval(() => pollStatus(reportId), POLL_INTERVAL);
  pollStatus(reportId);
}

function stopPipelinePolling() {
  if (pipelineInterval) {
    clearInterval(pipelineInterval);
    pipelineInterval = null;
  }
}

async function pollStatus(reportId) {
  try {
    const status = await apiGetPipelineStatus(reportId);
    updatePipelineUI(status);

    const stopStates = ['pending_review', 'approved', 'exported', 'failed'];
    if (stopStates.includes(status.status)) {
      stopPipelinePolling();
      onPipelineComplete(status.status, reportId);
    }
  } catch (e) {
    // 네트워크 오류 시 조용히 무시
  }
}

function updatePipelineUI(status) {
  const statusText = document.getElementById('pipeline-status-text');
  if (statusText) {
    statusText.textContent = STATUS_TEXT[status.status] || status.status;
  }

  const indicator = document.getElementById('pipeline-indicator');
  if (indicator) {
    const isRunning = !['draft','data_uploaded','pending_review','approved','exported','failed']
      .includes(status.status);
    indicator.className = `pipeline-status-indicator${isRunning ? ' running' : ''}`;
  }

  const badge = document.getElementById('report-status-badge');
  if (badge) {
    badge.className = `badge badge--${status.status}`;
    badge.textContent = STATUS_TEXT[status.status] || status.status;
  }

  const progressBar = document.getElementById('pipeline-progress');
  if (progressBar) {
    progressBar.style.width = `${status.progress_pct || 0}%`;
  }
}

async function onPipelineComplete(state, reportId) {
  if (state === 'pending_review') {
    showToast('보고서가 생성되었습니다!', 'success', 4000);
    if (typeof loadEditorData === 'function') {
      await loadEditorData(reportId);
    }
    if (typeof loadInsights === 'function') {
      await loadInsights(reportId);
    }
  }
  if (state === 'failed') {
    showToast('보고서 생성 실패. Excel 파일을 확인하거나 재시도하세요.', 'error', 6000);
  }
}

// ── 버튼 액션 ─────────────────────────────────────────────────────

async function restartPipeline() {
  const reportId = getReportIdFromUrl();
  const btn = document.getElementById('btn-restart');
  if (btn) { btn.disabled = true; btn.textContent = '생성 중...'; }
  try {
    await apiRestartPipeline(reportId);
    showToast('보고서 재생성 시작', 'info', 3000);
    startPipelinePolling(reportId);
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '↺ 재생성'; }
  }
}

let _reuploadFile = null;

async function reuploadExcelPickSheets(input) {
  const file = input.files[0];
  if (!file) return;
  _reuploadFile = file;

  // 시트 목록 기본값 (API 실패 시 fallback)
  let sheets = [{ index: 0, name: '시트1' }];

  try {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await apiFetch('/api/reports/sheet-list', { method: 'POST', body: formData, headers: {} });
    if (resp && resp.sheets && resp.sheets.length > 0) {
      sheets = resp.sheets;
    }
  } catch (e) {
    console.warn('시트 목록 조회 실패 (기본값 사용):', e.message);
  } finally {
    input.value = '';
  }

  const options = sheets.map(s => `<option value="${s.index}">${s.name}</option>`).join('');
  document.getElementById('ru-sheet-select').innerHTML = options;
  document.getElementById('ru-kpi-sheet-select').innerHTML =
    '<option value="none">없음</option>' + options;
  if (sheets.length >= 2)
    document.getElementById('ru-kpi-sheet-select').value = sheets[1].index;

  // 모달 표시 (인라인 스타일 제거 + flex 직접 지정)
  const modal = document.getElementById('reupload-sheet-modal');
  modal.style.removeProperty('display');
  modal.style.display = 'flex';
}

function closeReuploadModal() {
  document.getElementById('reupload-sheet-modal').style.setProperty('display', 'none');
  _reuploadFile = null;
}

async function confirmReupload() {
  if (!_reuploadFile) return;
  const reportId     = getReportIdFromUrl();
  const sheetName    = document.getElementById('ru-sheet-select').value;
  const kpiSheetName = document.getElementById('ru-kpi-sheet-select').value;
  const fileToUpload = _reuploadFile;   // null이 되기 전에 복사
  closeReuploadModal();

  try {
    showToast('Excel 재업로드 중...', 'info', 2000);
    const result = await apiUploadExcel(reportId, fileToUpload, 0, 0, sheetName, kpiSheetName);
    showToast(`${result.row_count}행 재업로드 완료 — 보고서 재생성 시작`, 'success');
    await apiRestartPipeline(reportId);
    startPipelinePolling(reportId);
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function downloadPptx() {
  const reportId = getReportIdFromUrl();
  const btn = document.getElementById('btn-pptx');
  if (btn) { btn.disabled = true; btn.textContent = 'PPT 생성 중...'; }
  try {
    showToast('PPT 생성 중... 잠시 기다려주세요', 'info', 30000);
    const blob = await apiExportPptx(reportId);
    downloadBlob(blob, `NDG_${reportId}_보고서.pptx`);
    showToast('PPT 다운로드 완료', 'success');
  } catch (e) {
    showToast('PPT 생성 실패: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '⬇ PPT 다운로드'; }
  }
}

async function approveReport() {
  const reportId = getReportIdFromUrl();
  const btn = document.querySelector('[onclick="approveReport()"]');
  if (btn) { btn.disabled = true; btn.textContent = 'PPT 생성 중...'; }
  try {
    await apiApproveReport(reportId);
    showToast('승인 완료. PPT를 생성합니다...', 'success');
    const blob = await apiExportPptx(reportId);
    downloadBlob(blob, `NDG_${reportId}_보고서.pptx`);
    showToast('PPT 다운로드 완료', 'success');
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '승인 & 내보내기'; }
  }
}

async function saveDraft(silent = false) {
  const reportId = getReportIdFromUrl();
  if (!reportId) return;
  try {
    await apiSaveDraft(reportId);
    const timeStr = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    const indicator = document.getElementById('draft-indicator');
    if (indicator) indicator.textContent = `${timeStr} 임시저장됨`;
    if (!silent) showToast('임시저장 완료', 'success');
  } catch (e) {
    if (!silent) showToast(e.message, 'error');
  }
}

let _autoSaveTimer = null;
function startAutoSave() {
  if (_autoSaveTimer) return;
  _autoSaveTimer = setInterval(() => saveDraft(true), 2 * 60 * 1000); // 2분마다
}

async function saveVersion() {
  const reportId = getReportIdFromUrl();
  const label = prompt('버전 이름을 입력하세요 (예: 1차 수정)') || '수동 저장';
  try {
    const result = await apiCreateVersion(reportId, label);
    showToast(`버전 ${result.version_number} 저장 완료`, 'success');
  } catch (e) {
    showToast(e.message, 'error');
  }
}

async function openVersionHistory() {
  const reportId = getReportIdFromUrl();
  let versions;
  try {
    versions = await apiGetVersions(reportId);
  } catch (e) {
    showToast(e.message, 'error');
    return;
  }

  // 기존 모달 제거
  document.getElementById('version-history-modal')?.remove();

  const rows = versions.length === 0
    ? `<p style="color:var(--color-text-muted);text-align:center;padding:var(--space-6)">저장된 버전이 없습니다</p>`
    : versions.map(v => {
        const dt = new Date(v.created_at);
        const label = `${dt.getFullYear()}.${String(dt.getMonth()+1).padStart(2,'0')}.${String(dt.getDate()).padStart(2,'0')} ${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`;
        return `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:var(--space-3) 0;border-bottom:1px solid var(--color-border-default)">
            <div>
              <span style="font-weight:600">v${v.version_number}</span>
              <span style="margin-left:var(--space-2);color:var(--color-text-secondary)">${v.version_label}</span>
              <span style="margin-left:var(--space-3);font-size:var(--font-size-xs);color:var(--color-text-muted)">${label}</span>
            </div>
            <div style="display:flex;gap:var(--space-2)">
              <button class="btn btn--ghost btn--sm" onclick="previewVersion(${v.version_number}, '${v.version_label}')">보기</button>
              <button class="btn btn--secondary btn--sm" onclick="restoreVersion(${v.version_number})">복원</button>
            </div>
          </div>`;
      }).join('');

  const modal = document.createElement('div');
  modal.id = 'version-history-modal';
  modal.className = 'modal-backdrop';
  modal.innerHTML = `
    <div class="modal" style="width:560px;max-height:70vh;display:flex;flex-direction:column">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-4)">
        <h2 class="modal__title" style="margin:0">버전 기록</h2>
        <button class="btn btn--ghost btn--sm" onclick="document.getElementById('version-history-modal').remove()">✕</button>
      </div>
      <div style="overflow-y:auto;flex:1">${rows}</div>
    </div>`;
  document.body.appendChild(modal);
}

async function previewVersion(versionNumber, label) {
  const reportId = getReportIdFromUrl();
  let versionData;
  try {
    versionData = await apiGetVersion(reportId, versionNumber);
  } catch (e) {
    showToast(e.message, 'error');
    return;
  }

  document.getElementById('version-preview-overlay')?.remove();

  // 응답: { version_number, version_label, data: { slides, ... } }
  const slides = versionData?.data?.slides || [];
  let currentIdx = 0;

  // 슬라이드는 1920×1080 기준 — 오버레이 너비에 맞게 스케일 계산
  const SLIDE_W = 1920, SLIDE_H = 1080;
  const PREVIEW_W = Math.min(window.innerWidth - 80, 1200);
  const PREVIEW_H = Math.round(PREVIEW_W * SLIDE_H / SLIDE_W);
  const SCALE = PREVIEW_W / SLIDE_W;

  function renderSlide(idx) {
    const slide = slides[idx];
    const html = slide ? (typeof buildSlideHtml === 'function' ? buildSlideHtml(slide) : `<pre style="padding:20px">${JSON.stringify(slide.data, null, 2)}</pre>`) : '';
    document.getElementById('vp-canvas').innerHTML = html;
    document.getElementById('vp-counter').textContent = `${idx + 1} / ${slides.length}`;
    document.getElementById('vp-prev').disabled = idx === 0;
    document.getElementById('vp-next').disabled = idx === slides.length - 1;
  }

  const overlay = document.createElement('div');
  overlay.id = 'version-preview-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,0.85);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px';
  overlay.innerHTML = `
    <div style="display:flex;align-items:center;gap:16px;color:#fff">
      <span style="font-size:14px;opacity:0.7">v${versionNumber} · ${label} — 읽기 전용</span>
      <button class="btn btn--ghost btn--sm" onclick="document.getElementById('version-preview-overlay').remove()" style="color:#fff;border-color:rgba(255,255,255,0.3)">✕ 닫기</button>
    </div>
    <div style="position:relative;width:${PREVIEW_W}px;height:${PREVIEW_H}px;border-radius:8px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.5)">
      <div id="vp-canvas" class="slide-canvas" style="transform:scale(${SCALE});transform-origin:top left;width:${SLIDE_W}px;height:${SLIDE_H}px;"></div>
    </div>
    <div style="display:flex;align-items:center;gap:16px;color:#fff">
      <button id="vp-prev" class="btn btn--secondary btn--sm" onclick="vp_nav(-1)">← 이전</button>
      <span id="vp-counter" style="font-size:14px;min-width:60px;text-align:center"></span>
      <button id="vp-next" class="btn btn--secondary btn--sm" onclick="vp_nav(1)">다음 →</button>
    </div>`;
  document.body.appendChild(overlay);

  window.vp_nav = (dir) => {
    currentIdx = Math.max(0, Math.min(slides.length - 1, currentIdx + dir));
    renderSlide(currentIdx);
  };

  renderSlide(0);
}

async function restoreVersion(versionNumber) {
  if (!confirm(`v${versionNumber}으로 복원하시겠습니까?\n현재 편집 내용은 임시저장 후 복원하는 것을 권장합니다.`)) return;
  const reportId = getReportIdFromUrl();
  try {
    await apiRestoreVersion(reportId, versionNumber);
    showToast(`v${versionNumber} 복원 완료 — 페이지를 새로고침합니다`, 'success');
    setTimeout(() => location.reload(), 1500);
  } catch (e) {
    showToast(e.message, 'error');
  }
}
