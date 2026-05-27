/**
 * dashboard.js — 대시보드 홈 페이지
 */

let deleteTargetId = null;
let currentFilter = '';
let _allReports = [];

const STATUS_LABELS = {
  draft: '초안',
  data_uploaded: '데이터 업로드됨',
  analyzing: '분석 중',
  generating: '생성 중',
  paused_bc: '검토 대기',
  reviewing: '교정 중',
  paused_d: '교정 확인 대기',
  assembling: '조립 중',
  pending_review: '최종 검토',
  approved: '승인됨',
  exported: '내보내기 완료',
  failed: '실패',
};

const IN_PROGRESS = ['analyzing','generating','paused_bc','reviewing','paused_d','assembling'];
const DONE        = ['approved','exported'];

function getProgressPct(status) {
  const map = {
    draft: 0, data_uploaded: 10,
    analyzing: 22, generating: 44, paused_bc: 50,
    reviewing: 60, paused_d: 68,
    assembling: 80, pending_review: 90,
    approved: 96, exported: 100, failed: 0,
  };
  return map[status] ?? 0;
}

// ── KPI 서머리 3선 꺾은선 그래프 ─────────────────────────────────

function _kpiLineChart(data, width, height) {
  if (!data || !data.length) return '<p style="color:#9CA3AF;font-size:13px">데이터 없음</p>';

  const series = [
    { key: 'followers_end', label: '팔로워', color: '#371704' },
    { key: 'total_reach',   label: '도달',   color: '#936435' },
    { key: 'total_interactions', label: '인터랙션', color: '#C00000' },
  ];

  const allVals = series.flatMap(s => data.map(d => d[s.key] || 0)).filter(v => v > 0);
  if (!allVals.length) return '<p style="color:#9CA3AF;font-size:13px">데이터 없음</p>';
  const maxVal = Math.max(...allVals) * 1.1;
  const padL = 50, padR = 14, padT = 28, padB = 32;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;
  const gap = chartW / Math.max(data.length - 1, 1);
  const toX = i => padL + i * gap;
  const toY = v => maxVal > 0 ? padT + chartH - (v / maxVal) * chartH : padT + chartH;

  const lines = series.map(s => {
    const pts = data.map((d, i) => ({ i, v: d[s.key] || 0 })).filter(p => p.v > 0);
    if (!pts.length) return '';
    const pathD = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'}${toX(p.i)},${toY(p.v)}`).join(' ');
    const dots = pts.map(p =>
      `<circle cx="${toX(p.i)}" cy="${toY(p.v)}" r="3" fill="${s.color}" stroke="#fff" stroke-width="1"/>`
    ).join('');
    return `<path d="${pathD}" fill="none" stroke="${s.color}" stroke-width="2"/>${dots}`;
  }).join('');

  const xLabels = data.map((d, i) => {
    const lbl = d.month && d.month.length > 4 ? d.month.slice(5) + '월' : (d.month || '');
    return `<text x="${toX(i)}" y="${padT + chartH + 20}" text-anchor="middle" font-size="10" fill="#936435">${lbl}</text>`;
  }).join('');

  const ticks = [0, 0.5, 1.0].map(f => {
    const v = Math.round(maxVal * f);
    const ty = padT + chartH - f * chartH;
    return `<line x1="${padL}" y1="${ty}" x2="${padL + chartW}" y2="${ty}" stroke="#EDE5DF" stroke-width="0.5"/>
      <text x="${padL - 6}" y="${ty + 4}" text-anchor="end" font-size="9" fill="#936435">${v >= 1000 ? (v/1000).toFixed(0)+'K' : v}</text>`;
  }).join('');

  const legend = series.map((s, i) =>
    `<text x="${padL + i * 80}" y="12" font-size="10" fill="${s.color}" font-weight="700">● ${s.label}</text>`
  ).join('');

  return `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
    ${ticks}${legend}
    <line x1="${padL}" y1="${padT+chartH}" x2="${padL+chartW}" y2="${padT+chartH}" stroke="#E7DCD5" stroke-width="1"/>
    ${lines}${xLabels}
  </svg>`;
}

// (레거시 바차트 유지)
function _miniBarChart(data, width, height) {
  if (!data || !data.length) {
    return '<p style="color:#9CA3AF;font-size:13px">데이터 없음</p>';
  }
  const maxVal = Math.max(...data.map(d => d.value || 0)) * 1.2 || 1;
  const padL = 10, padR = 14, padT = 22, padB = 28;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;
  const barW   = Math.floor(chartW / data.length * 0.55);
  const gap    = chartW / data.length;

  const bars = data.map((d, i) => {
    const x  = padL + i * gap + (gap - barW) / 2;
    const bh = Math.max(2, Math.round((d.value / maxVal) * chartH));
    const y  = padT + chartH - bh;
    const lbl = d.value >= 10000 ? (d.value / 10000).toFixed(1) + '만'
              : d.value >= 1000  ? (d.value / 1000).toFixed(0) + 'K'
              : String(d.value);
    return `
    <rect x="${x}" y="${y}" width="${barW}" height="${bh}" fill="#371704" rx="2"/>
    <text x="${x+barW/2}" y="${y-4}" text-anchor="middle" font-size="11" fill="#371704" font-weight="700">${lbl}</text>
    <text x="${x+barW/2}" y="${padT+chartH+18}" text-anchor="middle" font-size="10" fill="#936435">${d.label||''}</text>`;
  }).join('');

  return `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible">
    <line x1="${padL}" y1="${padT+chartH}" x2="${padL+chartW}" y2="${padT+chartH}" stroke="#E7DCD5" stroke-width="1.5"/>
    ${bars}
  </svg>`;
}

// ── KPI 서머리 로드/렌더링 ──────────────────────────────────────

async function loadKpiSummary() {
  try {
    const data = await apiKpiSummary();
    renderKpiSummary(data);
  } catch {
    document.getElementById('kpi-summary-body').innerHTML =
      '<p style="color:#9CA3AF;font-size:13px;padding:8px 0">KPI 데이터를 불러올 수 없습니다</p>';
  }
}

function renderKpiSummary(data) {
  const el = document.getElementById('kpi-summary-body');
  if (!data || !data.length) {
    el.innerHTML = `<p style="color:#9CA3AF;font-size:13px;padding:20px 0;text-align:center">
      보고서 데이터가 쌓이면 KPI 추이가 여기에 표시됩니다</p>`;
    return;
  }

  const valid = data.filter(d => d.followers_end > 0);
  if (!valid.length) {
    el.innerHTML = `<p style="color:#9CA3AF;font-size:13px;padding:20px 0;text-align:center">
      유효한 KPI 데이터가 없습니다</p>`;
    return;
  }

  const thS = 'padding:4px 6px;font-size:10px;font-weight:700;color:#371704;text-align:center;border:1px solid #E7DCD5;white-space:nowrap;background:#E7DCD5;';
  const tdS = 'padding:3px 6px;font-size:10px;color:#371704;text-align:center;border:1px solid #EDE5DF;white-space:nowrap;';

  const mHeaders = valid.map(d => {
    const lbl = d.month && d.month.length > 4 ? d.month.slice(5) + '월' : d.month;
    return `<th style="${thS}">${lbl}</th>`;
  }).join('');

  function makeRow(label, key) {
    return `<tr><td style="${tdS}font-weight:700;background:#FAFAF8;">${label}</td>` +
      valid.map(d => {
        const v = d[key] || 0;
        return `<td style="${tdS}">${v > 0 ? v.toLocaleString() : '-'}</td>`;
      }).join('') + '</tr>';
  }

  const kpiTable = `
    <table style="width:100%;border-collapse:collapse;margin-top:8px;table-layout:fixed;">
      <thead><tr><th style="${thS}width:64px;">지표</th>${mHeaders}</tr></thead>
      <tbody>
        ${makeRow('팔로워', 'followers_end')}
        ${makeRow('도달', 'total_reach')}
        ${makeRow('인터랙션', 'total_interactions')}
        ${makeRow('광고비', 'total_ad_spend')}
      </tbody>
    </table>`;

  // 누적값 계산
  const totalFollowers    = valid[valid.length - 1].followers_end;
  const totalInteractions = valid.reduce((s, d) => s + (d.total_interactions || 0), 0);
  const totalReach        = valid.reduce((s, d) => s + (d.total_reach || 0), 0);
  const totalAdSpend      = valid.reduce((s, d) => s + (d.total_ad_spend || 0), 0);

  function metricCard(label, value, unit) {
    return `<div style="background:var(--color-bg-surface,#FAFAF8);border-left:3px solid #371704;
      padding:8px 10px;overflow:hidden;">
      <div style="font-size:10px;font-weight:600;color:#936435;margin-bottom:2px;">${label}</div>
      <div style="font-size:16px;font-weight:900;color:#371704;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
        ${formatNumber(value)}${unit ? `<span style="font-size:10px;font-weight:400;color:#936435"> ${unit}</span>` : ''}
      </div>
    </div>`;
  }

  el.innerHTML = `
  <div style="display:flex;flex-direction:column;gap:12px;">
    <div style="display:flex;gap:16px;align-items:flex-start;">
      <div style="flex:1;min-width:0;">
        <div class="kpi-chart-title">KPI 월간 추이</div>
        ${_kpiLineChart(valid, 480, 200)}
      </div>
      <div style="width:280px;flex-shrink:0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
        ${metricCard('팔로워 (최근)', totalFollowers, '')}
        ${metricCard('인터랙션 누적', totalInteractions, '')}
        ${metricCard('도달 누적', totalReach, '')}
        ${metricCard('광고비 누적', totalAdSpend, '원')}
      </div>
    </div>
    ${kpiTable}
  </div>`;
}

// ── 대시보드 로드 ───────────────────────────────────────────────

async function loadDashboard() {
  try {
    const reports = await apiGetReports();
    _allReports = reports;
    renderStats(reports);
    renderReports(reports);
    loadKpiSummary();
  } catch (e) {
    renderStats([]);
    document.getElementById('report-grid').innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:var(--space-16)">
        <p style="color:var(--color-text-muted);margin-bottom:var(--space-4)">로그인이 필요합니다</p>
        <a href="/login" class="btn btn--primary">로그인</a>
      </div>`;
  }
}

function renderStats(reports) {
  const now = new Date();
  const thisMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  document.getElementById('stat-total').textContent       = reports.length;
  document.getElementById('stat-month').textContent       = reports.filter(r => r.report_month === thisMonth).length;
  document.getElementById('stat-in-progress').textContent = reports.filter(r => IN_PROGRESS.includes(r.status)).length;
  document.getElementById('stat-exported').textContent    = reports.filter(r => r.status === 'exported').length;
}

// ── 필터 탭 ─────────────────────────────────────────────────────

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === filter);
  });
  renderReports(_allReports);
}

function getFilteredReports(reports) {
  if (!currentFilter) return reports;
  if (currentFilter === 'in_progress')    return reports.filter(r => IN_PROGRESS.includes(r.status));
  if (currentFilter === 'pending_review') return reports.filter(r => r.status === 'pending_review');
  if (currentFilter === 'done')           return reports.filter(r => DONE.includes(r.status));
  return reports;
}

// ── 보고서 카드 렌더링 ──────────────────────────────────────────

function renderReports(reports) {
  const grid     = document.getElementById('report-grid');
  const filtered = getFilteredReports(reports);

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:var(--space-16)">
        <p style="font-size:48px;margin-bottom:var(--space-4)">📋</p>
        <p style="color:var(--color-text-muted);margin-bottom:var(--space-4)">
          ${currentFilter ? '해당 상태의 보고서가 없습니다' : '아직 보고서가 없습니다'}
        </p>
        <a href="/new" class="btn btn--accent">첫 보고서 만들기</a>
      </div>`;
    return;
  }

  grid.innerHTML = filtered.map(r => {
    const pct = getProgressPct(r.status);
    return `
    <article class="report-card" onclick="window.location='/report/${r.id}'">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:var(--space-3)">
        <div class="report-card__month">${formatMonth(r.report_month)}</div>
        <span class="badge badge--${r.status}">${STATUS_LABELS[r.status] || r.status}</span>
      </div>
      <div class="report-card__client">${r.client_name}</div>
      <div class="report-card__title">${r.title}</div>
      <div style="font-size:var(--font-size-xs);color:var(--color-text-muted);margin-bottom:var(--space-3)">
        ${new Date(r.created_at).toLocaleDateString('ko-KR')} 생성
      </div>
      <div class="progress-pipeline" title="${pct}% 완료">
        <div class="progress-pipeline__bar" style="width:${pct}%"></div>
      </div>
      <div style="font-size:10px;color:var(--color-text-muted);margin-top:3px;margin-bottom:var(--space-3)">${pct}% 완료</div>
      <div class="report-card__actions" onclick="event.stopPropagation()">
        <a href="/report/${r.id}" class="btn btn--secondary btn--sm">편집</a>
        <a href="/preview/${r.id}" class="btn btn--secondary btn--sm">미리보기</a>
        <button class="btn btn--ghost btn--sm" onclick="duplicateReport(${r.id},event)">복제</button>
        <button class="btn btn--ghost btn--sm" onclick="openDeleteModal(${r.id})">삭제</button>
      </div>
    </article>`;
  }).join('');
}

// ── 복제 ────────────────────────────────────────────────────────

async function duplicateReport(reportId, e) {
  if (e) e.stopPropagation();
  try {
    await apiDuplicateReport(reportId);
    showToast('보고서가 복제되었습니다', 'success');
    const reports = await apiGetReports();
    _allReports = reports;
    renderStats(reports);
    renderReports(reports);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── 삭제 ────────────────────────────────────────────────────────

function openDeleteModal(reportId) {
  deleteTargetId = reportId;
  document.getElementById('delete-modal').style.display = 'flex';
  document.getElementById('confirm-delete-btn').onclick = confirmDelete;
}

function closeDeleteModal() {
  deleteTargetId = null;
  document.getElementById('delete-modal').style.display = 'none';
}

async function confirmDelete() {
  if (!deleteTargetId) return;
  try {
    await apiDeleteReport(deleteTargetId);
    showToast('보고서가 삭제되었습니다', 'success');
    closeDeleteModal();
    const reports = await apiGetReports().catch(() => []);
    _allReports = reports;
    renderStats(reports);
    renderReports(reports);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── 초기 로드 ────────────────────────────────────────────────────
loadDashboard();
