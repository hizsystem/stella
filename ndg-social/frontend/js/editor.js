/**
 * editor.js — 보고서 편집기 (report.html)
 */

const TEMPLATE_NAMES = {
  'title':            'Title',
  'calendar':         'Calendar',
  'kpi':              'KPI',
  'engagement':       '피드&릴스',
  'story':            'Story',
  'popular_content':  'Popular',
  'story_strategy':   '광고성과',
  'operating_review': 'Review',
  'closing':          'Closing',
};

// 슬라이드별 편집 가능 필드 정의
const SLIDE_FIELDS = {
  1: [
    { key: 'main_title', label: '메인 타이틀', maxLen: 30 },
    { key: 'sub_title', label: '부제목 (월/연도)', maxLen: 20 },
    { key: 'client_name', label: '클라이언트명', maxLen: 20 },
    { key: 'prepared_by', label: '작성팀', maxLen: 30 },
  ],
  2: [
    { key: 'summary', label: '월간 콘텐츠 요약', maxLen: 60 },
    { key: 'highlight_note', label: '하이라이트', maxLen: 60 },
  ],
  3: [
    { key: 'table_caption', label: '표 캡션', maxLen: 40 },
    { key: 'mom_note', label: '전월 비교 문구', maxLen: 45 },
    { key: 'summary_sentence', label: '요약 문장', maxLen: 45 },
  ],
  4: [
    { key: 'summary_sentence', label: '요약 문장', maxLen: 45 },
    { key: 'engagement_breakdown', label: '콘텐츠 비중', maxLen: 60 },
  ],
  5: [
    { key: 'rank1_description', label: '1위 콘텐츠 설명', maxLen: 60 },
    { key: 'rank2_description', label: '2위 콘텐츠 설명', maxLen: 60 },
    { key: 'rank3_description', label: '3위 콘텐츠 설명', maxLen: 60 },
    { key: 'insight_line', label: '인사이트 라인', maxLen: 45 },
  ],
  6: [
    { key: 'performance_summary', label: '성과 요약', maxLen: 45 },
    { key: 'efficiency_note', label: '효율 메모', maxLen: 45 },
    { key: 'caution_note', label: '주의 메모', maxLen: 45 },
  ],
  7: [], // 인사이트 패널에서 별도 관리
  8: [
    { key: 'closing_statement', label: '마무리 문구', maxLen: 60 },
    { key: 'prepared_by', label: '작성팀', maxLen: 30 },
  ],
};

let reportStructure = null;
let currentSlide = 1;
const reportId = getReportIdFromUrl();

// ── HTML 새니타이저 (볼드·줄바꿈만 허용) ──────────────────────────

function _sanitizeHtml(html) {
  const tmp = document.createElement('div');
  tmp.innerHTML = html;
  const ALLOWED = new Set(['B', 'STRONG', 'EM', 'I', 'BR']);

  function serialize(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
    if (node.nodeType !== Node.ELEMENT_NODE) return '';
    const tag = node.tagName;
    if (tag === 'BR') return '<br>';
    const inner = Array.from(node.childNodes).map(serialize).join('');
    if (ALLOWED.has(tag)) return `<${tag.toLowerCase()}>${inner}</${tag.toLowerCase()}>`;
    // div/p → 내용 + 줄바꿈 (Enter 키 결과물 처리)
    if (tag === 'DIV' || tag === 'P') return inner ? inner + '<br>' : '';
    return inner;
  }

  return Array.from(tmp.childNodes)
    .map(serialize)
    .join('')
    .replace(/(<br>\s*)+$/, '')   // 끝 줄바꿈 제거
    .trim();
}

// ── Undo / Redo ───────────────────────────────────────────────────

const _undoStack = [];
const _redoStack = [];

function _pushUndo(entry) {
  _undoStack.push(entry);
  if (_undoStack.length > 50) _undoStack.shift();
  _redoStack.length = 0;
}

function _getNestedValue(obj, fieldKey) {
  const parts = fieldKey.split('.');
  let cur = obj;
  for (const p of parts) {
    if (cur == null) return undefined;
    cur = p.match(/^\d+$/) ? cur[parseInt(p)] : cur[p];
  }
  return cur;
}

function _setNestedValue(obj, fieldKey, value) {
  const parts = fieldKey.split('.');
  let cur = obj;
  for (const p of parts.slice(0, -1)) {
    if (cur == null) return false;
    cur = p.match(/^\d+$/) ? cur[parseInt(p)] : cur[p];
  }
  if (cur == null) return false;
  const last = parts[parts.length - 1];
  if (last.match(/^\d+$/)) cur[parseInt(last)] = value;
  else cur[last] = value;
  return true;
}

async function _applyValue(slideNum, fieldKey, value) {
  const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
  if (slide?.data) _setNestedValue(slide.data, fieldKey, value);
  await apiUpdateSlide(reportId, slideNum, fieldKey, value);
  if (currentSlide === slideNum) renderSlide(slideNum);
}

async function performUndo() {
  const e = _undoStack.pop();
  if (!e) { showToast('되돌릴 내용이 없습니다', 'info', 1500); return; }
  _redoStack.push(e);
  try {
    await _applyValue(e.slideNum, e.fieldKey, e.oldValue);
    showToast('되돌렸습니다 (Ctrl+Y로 다시 실행)', 'info', 2000);
  } catch (err) {
    showToast('되돌리기 실패: ' + err.message, 'error');
  }
}

async function performRedo() {
  const e = _redoStack.pop();
  if (!e) { showToast('다시 실행할 내용이 없습니다', 'info', 1500); return; }
  _undoStack.push(e);
  try {
    await _applyValue(e.slideNum, e.fieldKey, e.newValue);
    showToast('다시 실행했습니다', 'info', 1500);
  } catch (err) {
    showToast('다시 실행 실패: ' + err.message, 'error');
  }
}

// ── 초기화 ────────────────────────────────────────────────────────

async function initEditor() {
  const report = await apiGetReport(reportId).catch(() => null);
  if (report) {
    document.getElementById('report-title-bar').textContent = report.title;
    document.getElementById('report-status-badge').textContent = report.status;
    document.getElementById('report-status-badge').className = `badge badge--${report.status}`;
    // btn-preview removed
  }

  await loadEditorData(reportId);
  renderNavigator();
  startPipelinePolling(reportId);
}

async function loadEditorData(reportId) {
  try {
    // user_edited 우선 (사용자 편집 반영), 없으면 agent_e_output
    let data = await apiGetReportData(reportId, 'user_edited').catch(() => null);
    if (!data) data = await apiGetReportData(reportId, 'agent_e_output').catch(() => null);
    if (data) {
      reportStructure = data;
      renderNavigator();
      renderSlide(currentSlide);
    }
  } catch (e) {
    // 데이터 없음 — 정상
  }

  await loadInsights(reportId);
}

// ── 슬라이드 네비게이터 ───────────────────────────────────────────

function renderNavigator() {
  const nav = document.getElementById('slide-navigator');
  const slides = reportStructure?.slides || [];
  if (slides.length === 0) {
    // 데이터 없을 때 빈 썸네일 9개
    nav.innerHTML = Array.from({ length: 9 }, (_, i) => `
      <div class="slide-thumb" onclick="selectSlide(${i+1})" id="thumb-${i+1}">
        <div class="slide-thumb__number">${i+1}</div>
        <div class="slide-thumb__label">—</div>
      </div>`).join('');
    return;
  }
  nav.innerHTML = slides.map(slide => {
    const num = slide.slide_number;
    const label = TEMPLATE_NAMES[slide.template] || slide.template || num;
    const isActive = num === currentSlide;
    return `
      <div class="slide-thumb${isActive ? ' active' : ''}"
        onclick="selectSlide(${num})" id="thumb-${num}" style="position:relative;">
        <div class="slide-thumb__number">${num}</div>
        <div class="slide-thumb__label">${label}</div>
        <button class="slide-thumb-delete" title="슬라이드 삭제"
          onclick="event.stopPropagation();deleteSlide(${num})"
          style="position:absolute;top:4px;right:4px;width:18px;height:18px;
            background:rgba(185,28,28,0.85);color:#fff;border:none;border-radius:50%;
            font-size:12px;line-height:1;cursor:pointer;opacity:0;transition:opacity 0.15s;
            display:flex;align-items:center;justify-content:center;padding:0;">×</button>
      </div>`;
  }).join('');

  // 썸네일 hover 시 삭제 버튼 표시
  nav.querySelectorAll('.slide-thumb').forEach(thumb => {
    const btn = thumb.querySelector('.slide-thumb-delete');
    if (!btn) return;
    thumb.addEventListener('mouseenter', () => { btn.style.opacity = '1'; });
    thumb.addEventListener('mouseleave', () => { btn.style.opacity = '0'; });
  });
}

function selectSlide(num) {
  currentSlide = num;
  document.querySelectorAll('.slide-thumb').forEach(el => el.classList.remove('active'));
  const thumb = document.getElementById(`thumb-${num}`);
  if (thumb) thumb.classList.add('active');
  renderSlide(num);
}

// ── 슬라이드 미리보기 ─────────────────────────────────────────────

function renderSlide(slideNum) {
  const canvas = document.getElementById('slide-canvas');
  const wrapper = document.getElementById('slide-wrapper');
  if (!reportStructure) return;

  const slide = (reportStructure.slides || []).find(s => s.slide_number === slideNum);
  if (!slide) return;

  canvas.innerHTML = buildSlideHtml(slide);
  scaleSlideCanvas();
  attachInlineEditors(slideNum);
}

// ── 인라인 편집 ─────────────────────────────────────────────────

function attachInlineEditors(slideNum) {
  const canvas = document.getElementById('slide-canvas');
  if (!canvas) return;

  canvas.querySelectorAll('[data-field]').forEach(el => {
    el.contentEditable = 'true';
    el.style.cursor = 'text';

    // hover 힌트
    el.addEventListener('mouseenter', () => {
      if (!el._editing) el.style.outline = '2px dashed rgba(147,100,53,0.4)';
    });
    el.addEventListener('mouseleave', () => {
      if (!el._editing) el.style.outline = 'none';
    });

    // focus
    el.addEventListener('focus', () => {
      el._editing = true;
      el.style.outline = '2px solid #936435';
      el._originalText = _sanitizeHtml(el.innerHTML); // sanitized로 저장
    });

    // blur → save
    el.addEventListener('blur', async () => {
      el._editing = false;
      el.style.outline = 'none';
      const fieldKey = el.dataset.field;
      const newValue = _sanitizeHtml(el.innerHTML);
      if (newValue === el._originalText) return; // 변경 없으면 스킵

      // ★ await 이전에 in-memory 업데이트 (네비게이션 레이스 컨디션 방지)
      const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
      if (slide?.data) _setNestedValue(slide.data, fieldKey, newValue);

      try {
        await apiUpdateSlide(reportId, slideNum, fieldKey, newValue);
        _pushUndo({ slideNum, fieldKey, oldValue: el._originalText, newValue });
        showToast('저장됨', 'success', 1500);
      } catch (e) {
        showToast('저장 실패: ' + e.message, 'error');
        // 실패 시 in-memory + DOM 모두 되돌리기
        if (slide?.data) _setNestedValue(slide.data, fieldKey, el._originalText);
        el.innerHTML = el._originalText;
      }
    });
  });

  // ── 이미지 드롭존 바인딩 ──
  attachDropZones(slideNum);
}

function attachDropZones(slideNum) {
  const canvas = document.getElementById('slide-canvas');
  if (!canvas) return;

  canvas.querySelectorAll('.slide-dropzone').forEach(zone => {
    const fieldKey = zone.dataset.dropField;

    // 드래그 오버 시각 효과
    zone.addEventListener('dragover', e => {
      e.preventDefault();
      zone.style.outline = '3px dashed #936435';
      zone.style.opacity = '0.8';
    });
    zone.addEventListener('dragleave', () => {
      zone.style.outline = 'none';
      zone.style.opacity = '1';
    });

    // 드롭 → 업로드
    zone.addEventListener('drop', async e => {
      e.preventDefault();
      zone.style.outline = 'none';
      zone.style.opacity = '1';
      const file = e.dataTransfer.files[0];
      if (!file || !file.type.startsWith('image/')) {
        showToast('이미지 파일만 업로드 가능합니다', 'error');
        return;
      }
      await uploadSlideImage(slideNum, fieldKey, file);
    });

    // 붙여넣기 (Ctrl+V) → 클립보드 이미지 업로드
    zone.setAttribute('tabindex', '0'); // 포커스 가능하게
    zone.addEventListener('paste', async e => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) await uploadSlideImage(slideNum, fieldKey, file);
          return;
        }
      }
    });

    // 클릭 → 파일 선택
    zone.addEventListener('click', e => {
      if (e.target.closest('[data-field]')) return; // 텍스트 편집 클릭은 무시
      if (e.target.closest('.slide-img-remove')) return; // 삭제 버튼 클릭은 무시
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async () => {
        if (input.files[0]) await uploadSlideImage(slideNum, fieldKey, input.files[0]);
      };
      input.click();
    });

    // 이미지 제거 버튼 표시/숨김 + 클릭
    const rmBtn = zone.querySelector('.slide-img-remove');
    if (rmBtn) {
      zone.addEventListener('mouseenter', () => { rmBtn.style.opacity = '1'; });
      zone.addEventListener('mouseleave', () => { rmBtn.style.opacity = '0'; });
      rmBtn.addEventListener('click', async e => {
        e.stopPropagation();
        await removeSlideImage(slideNum, fieldKey);
      });
    }
  });
}

async function deleteSlide(slideNum) {
  if (!confirm(`슬라이드 ${slideNum}을 삭제할까요?\n이 작업은 되돌릴 수 없습니다.`)) return;
  try {
    await apiFetch(`/api/reports/${reportId}/slides/${slideNum}`, { method: 'DELETE' });
    reportStructure.slides = reportStructure.slides.filter(s => s.slide_number !== slideNum);
    // 삭제된 슬라이드에 있었다면 첫 번째 슬라이드로 이동
    if (currentSlide === slideNum) {
      const first = reportStructure.slides[0];
      if (first) { currentSlide = first.slide_number; renderSlide(currentSlide); }
    }
    renderNavigator();
    showToast(`슬라이드 ${slideNum} 삭제됨`, 'info', 2000);
  } catch (e) {
    showToast('삭제 실패: ' + e.message, 'error');
  }
}

async function removeSlideImage(slideNum, fieldKey) {
  const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
  const oldUrl = slide?.data ? (_getNestedValue(slide.data, fieldKey) || '') : '';
  try {
    await apiUpdateSlide(reportId, slideNum, fieldKey, '');
    if (slide?.data) _setNestedValue(slide.data, fieldKey, '');
    _pushUndo({ slideNum, fieldKey, oldValue: oldUrl, newValue: '' });
    renderSlide(slideNum);
    showToast('이미지 제거됨 (Ctrl+Z로 되돌리기)', 'info', 2000);
  } catch (e) {
    showToast('이미지 제거 실패: ' + e.message, 'error');
  }
}

async function uploadSlideImage(slideNum, fieldKey, file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('field_key', fieldKey);

  // 되돌리기를 위해 기존 값 기록
  const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
  const oldUrl = slide?.data ? (_getNestedValue(slide.data, fieldKey) || '') : '';

  try {
    showToast('이미지 업로드 중...', 'info', 2000);
    const resp = await fetch(`/api/reports/${reportId}/slides/${slideNum}/image`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${getToken()}` },
      body: formData,
    });
    if (!resp.ok) throw new Error('업로드 실패');
    const result = await resp.json();

    // 로컬 데이터 업데이트
    if (slide?.data) _setNestedValue(slide.data, fieldKey, result.image_url);
    _pushUndo({ slideNum, fieldKey, oldValue: oldUrl, newValue: result.image_url });

    renderSlide(slideNum);
    showToast('이미지 저장됨 (Ctrl+Z로 되돌리기)', 'success', 2000);
  } catch (e) {
    showToast('이미지 업로드 실패: ' + e.message, 'error');
  }
}

function scaleSlideCanvas() {
  const wrapper = document.getElementById('slide-wrapper');
  const canvas = document.getElementById('slide-canvas');
  if (!wrapper || !canvas) return;
  const scale = wrapper.offsetWidth / 1920;
  canvas.style.transform = `scale(${scale})`;
  wrapper.style.height = `${1080 * scale}px`;
}

window.addEventListener('resize', scaleSlideCanvas);

// ── 필드 편집 패널 ────────────────────────────────────────────────

function renderFieldGroups(slideNum) {
  const pane = document.getElementById('field-groups');
  const title = document.getElementById('fields-pane-title');
  if (title) {
    const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
    const label = slide ? (TEMPLATE_NAMES[slide.template] || slide.template) : slideNum;
    title.textContent = `슬라이드 ${slideNum}: ${label}`;
  }

  if (!reportStructure) {
    pane.innerHTML = '<p style="font-size:var(--font-size-sm);color:var(--color-text-muted)">보고서 데이터가 없습니다</p>';
    return;
  }

  const slide = (reportStructure.slides || []).find(s => s.slide_number === slideNum);
  const fields = SLIDE_FIELDS[slideNum] || [];

  if (slideNum === 7) {
    pane.innerHTML = '<p style="font-size:var(--font-size-sm);color:var(--color-text-secondary)">인사이트는 우측 패널에서 편집하세요.</p>';
    return;
  }

  pane.innerHTML = fields.map(f => {
    const val = slide?.data?.[f.key] || '';
    return `
      <div class="field-group">
        <div class="field-label">
          ${f.label}
          <span class="ai-badge">AI</span>
        </div>
        <textarea class="field-input" id="field-${slideNum}-${f.key}"
          maxlength="${f.maxLen}"
          onchange="saveField(${slideNum}, '${f.key}', this.value)"
          oninput="updateCharCount(this, ${f.maxLen})"
          rows="2">${val}</textarea>
        <div class="field-meta">
          <span>${f.label}</span>
          <span class="char-count" id="cc-${slideNum}-${f.key}">${val.length}/${f.maxLen}</span>
        </div>
      </div>`;
  }).join('');
}

function updateCharCount(textarea, maxLen) {
  const parts = textarea.id.split('-');
  const ccEl = document.getElementById(`cc-${parts[1]}-${parts.slice(2).join('-')}`);
  if (ccEl) {
    ccEl.textContent = `${textarea.value.length}/${maxLen}`;
    ccEl.className = `char-count${textarea.value.length > maxLen * 0.9 ? ' over' : ''}`;
  }
}

async function saveField(slideNum, fieldKey, value) {
  try {
    await apiUpdateSlide(reportId, slideNum, fieldKey, value);
    // 로컬 구조 업데이트
    const slide = (reportStructure?.slides || []).find(s => s.slide_number === slideNum);
    if (slide?.data) slide.data[fieldKey] = value;
    renderSlide(slideNum);
  } catch (e) {
    showToast('저장 실패: ' + e.message, 'error');
  }
}

// ── 인사이트 패널 ──────────────────────────────────────────────────

async function loadInsights(reportId) {
  try {
    const data = await apiGetReportData(reportId, 'agent_c_output');
    const insights = data?.insights || [];
    if (insights.length > 0) {
      renderInsights(insights);
    }
  } catch (e) {
    // 없으면 무시
  }
}

function renderInsights(insights) {
  const list = document.getElementById('insights-list');
  if (!list) return;
  list.innerHTML = insights.map(ins => `
    <div class="insight-item" data-category="${ins.category}" id="insight-${ins.number}">
      <div class="insight-item__category">${ins.number}. ${ins.category}</div>
      <div class="insight-item__text" contenteditable="true"
        onblur="saveInsight(${ins.number}, this.textContent)">${ins.full_sentence}</div>
      <button class="btn btn--ghost btn--sm" style="margin-top:var(--space-2);font-size:10px"
        onclick="regenerateSingleInsight(${ins.number})">재생성</button>
    </div>
  `).join('');
}

async function saveInsight(num, text) {
  // 인사이트 편집은 슬라이드 7 data.insights 배열 업데이트
  try {
    await apiUpdateSlide(reportId, 7, `insights.${num-1}.full_sentence`, text);
    showToast('인사이트 저장됨', 'success', 1500);
  } catch (e) {
    showToast('저장 실패: ' + e.message, 'error');
  }
}

async function regenerateInsights() {
  await restartPipeline();
}

async function regenerateSingleInsight(num) {
  await restartPipeline();
}

// ── change_log ────────────────────────────────────────────────────

async function loadChangeLog(reportId) {
  try {
    const data = await apiGetChangeLog(reportId);
    const section = document.getElementById('change-log-section');
    if (!section) return;

    if (data.change_log && data.change_log.length > 0) {
      section.style.display = 'block';
      const score = document.getElementById('change-log-score');
      if (score) {
        score.textContent = `품질 ${data.quality_score}점`;
        score.className = `badge badge--${data.quality_score >= 80 ? 'approved' : 'pending_review'}`;
      }
      document.getElementById('change-log-list').innerHTML = data.change_log.map((item, i) => `
        <div class="change-log-item" id="cl-${i}">
          <div class="change-log-item__location">${item.location}</div>
          <div class="change-log-item__original">원문: ${item.original}</div>
          <div class="change-log-item__corrected">교정: ${item.corrected}</div>
          <div class="change-log-item__reason">${item.reason}</div>
          <div class="change-log-item__actions">
            <button class="btn btn--sm btn--primary" onclick="acceptChange(${i}, '${item.location}', \`${item.corrected}\`)">수락</button>
            <button class="btn btn--sm btn--secondary" onclick="rejectChange(${i})">거절</button>
          </div>
        </div>`).join('');
    }
  } catch (e) {
    // 없으면 무시
  }
}

function acceptChange(index, location, corrected) {
  const el = document.getElementById(`cl-${index}`);
  if (el) el.style.opacity = '0.4';
  showToast('수락됨', 'success', 1500);
}

function rejectChange(index) {
  const el = document.getElementById(`cl-${index}`);
  if (el) { el.style.opacity = '0.4'; el.style.textDecoration = 'line-through'; }
  showToast('거절됨', 'info', 1500);
}

async function acceptAllChanges() {
  showToast('모든 교정이 수락되었습니다', 'success');
  document.querySelectorAll('.change-log-item').forEach(el => el.style.opacity = '0.4');
}


// ── 초기화 ────────────────────────────────────────────────────────
initEditor();
