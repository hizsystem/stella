/**
 * slides.js — NDG 보고서 슬라이드 렌더링
 * 1920×1080 기준 / CSS transform 스케일 조정
 *
 * 팔레트
 *   #371704  Espresso  — 브랜드 다크 / 표지 배경
 *   #C00000  Red       — 강조 수치·섹션 라벨·하락 지표
 *   #FFC000  Gold      — 3번째 유형 / 차트 목표선 / 보조 강조
 *   #E7DCD5  Beige     — 헤더 배경 / 표면
 *   #936435  Brown     — 보조 텍스트 / 헤더 라벨
 *   #2E7D32  Green     — 상승 지표
 *   #FAFAF8  WarmWhite — 카드 배경
 */

function _hdr(num, label) {
  return `
  <div style="position:absolute;top:0;left:0;right:0;height:84px;
    display:flex;align-items:center;justify-content:space-between;
    padding:0 80px;background:#E7DCD5;border-bottom:2px solid #C8B9B0;">
    <div style="display:flex;align-items:center;gap:20px;">
      <span style="font-size:18px;font-weight:800;letter-spacing:0.22em;
        color:#371704;text-transform:uppercase;">NDG</span>
      <span style="width:1px;height:16px;background:#C8B9B0;display:inline-block;"></span>
      <span style="font-size:18px;font-weight:600;letter-spacing:0.12em;
        color:#936435;text-transform:uppercase;">${label}</span>
    </div>
    <span></span>
  </div>`;
}

function _ftr(date) {
  return `
  <div style="position:absolute;bottom:0;left:0;right:0;height:52px;
    display:flex;align-items:center;justify-content:space-between;
    padding:0 80px;background:#FAFAF8;border-top:1.5px solid #E7DCD5;">
    <span style="font-size:18px;color:#936435;font-weight:500;letter-spacing:0.04em;">
      HIZ-NDG &nbsp;·&nbsp; SNS Monthly Report</span>
    <span style="font-size:18px;color:#936435;font-weight:500;letter-spacing:0.04em;">
      ${date || ''}</span>
  </div>`;
}

function _secHead(label, title, sub, fieldKey) {
  return `
  <div style="margin-bottom:32px;">
    <div style="font-size:18px;font-weight:700;letter-spacing:0.18em;color:#C00000;
      text-transform:uppercase;margin-bottom:8px;">${label}</div>
    <h2 ${fieldKey ? `data-field="${fieldKey}"` : ''} style="font-size:40px;font-weight:900;color:#371704;line-height:1.1;
      margin:0${sub ? ' 0 8px' : ''};outline:none;">${title}</h2>
    ${sub ? `<p style="font-size:17px;color:#936435;margin:0;font-weight:400;">${sub}</p>` : ''}
  </div>`;
}

// calendar_entries 타입별 색상 (feed_reel = 짙은 갈색, story = 노란색)
const CAL_TYPE_COLOR = { feed_reel: '#371704', feed: '#371704', reel: '#371704', story: '#FFC000' };

function _buildCalGrid(reportMonth, entries) {
  const parts = (reportMonth || '2026-02').split('-');
  const y = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (!y || !m) return '';

  const firstDow    = new Date(y, m - 1, 1).getDay();
  const startOffset = (firstDow + 6) % 7;
  const totalDays   = new Date(y, m, 0).getDate();

  // 날짜별 마커 맵 { "15": [{type:'feed'}, {type:'story'}] }
  const markerMap = {};
  (entries || []).forEach(e => {
    if (!e.date) return;
    const day = String(parseInt(e.date.split('-')[2] || '0', 10));
    if (!markerMap[day]) markerMap[day] = [];
    markerMap[day].push(e);
  });

  const DAYS = ['MON','TUE','WED','THU','FRI','SAT','SUN'];
  const cells = Array(startOffset).fill(null);
  for (let i = 1; i <= totalDays; i++) cells.push(i);
  while (cells.length % 7) cells.push(null);

  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  const rowH = Math.floor(490 / weeks.length);

  const header = DAYS.map((d, i) => {
    const c = i === 5 ? '#936435' : '#371704';
    return `<div style="text-align:center;padding:10px 0 12px;font-size:18px;font-weight:700;
      letter-spacing:0.1em;color:${c};background:#E7DCD5;border-bottom:2px solid #C8B9B0;">${d}</div>`;
  }).join('');

  const rows = weeks.map(week =>
    week.map((day, i) => {
      if (!day) return `<div style="height:${rowH}px;background:#FAFAF8;"></div>`;
      const isSat = i === 5;
      const tc = isSat ? '#936435' : '#371704';
      const dayMarkers = markerMap[String(day)] || [];
      const dots = dayMarkers.slice(0, 4).map(e => {
        const dc = CAL_TYPE_COLOR[e.type] || '#371704';
        return `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;
          background:${dc};margin:1px;flex-shrink:0;"></span>`;
      }).join('');
      const hasMarkers = dayMarkers.length > 0;
      return `
      <div style="height:${rowH}px;display:flex;flex-direction:column;align-items:flex-start;
        padding:8px 0 4px 10px;border-bottom:1px solid #EDE5DF;border-right:1px solid #EDE5DF;
        background:${hasMarkers ? '#FFFDF9' : '#FFFFFF'};">
        <span style="font-size:18px;font-weight:${hasMarkers ? 700 : 500};color:${tc};
          margin-bottom:4px;">${day}</span>
        ${hasMarkers ? `<div style="display:flex;flex-wrap:wrap;gap:2px;">${dots}</div>` : ''}
      </div>`;
    }).join('')
  ).join('');

  return `
  <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:0;
    border:1.5px solid #C8B9B0;flex:1;">
    ${header}${rows}
  </div>`;
}

function _svgLineChart(data, width, height, target, currentMonth) {
  if (!data || !data.length) return '';
  const vals = data.map(d => d.value || 0).filter(v => v > 0);
  if (!vals.length) return '';
  const minVal = Math.min(...vals) * 0.98;
  const maxVal = Math.max(...vals, target || 0) * 1.04;
  const padL = 80, padR = 30, padT = 24, padB = 48;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;
  const gap = chartW / Math.max(data.length - 1, 1);

  const toX = i => padL + i * gap;
  const toY = v => padT + chartH - ((v - minVal) / (maxVal - minVal)) * chartH;

  // 데이터가 있는 포인트만 연결
  const activePoints = data.map((d, i) => ({i, v: d.value || 0, label: d.label || ''}))
    .filter(p => p.v > 0);

  const pathD = activePoints.map((p, idx) =>
    `${idx === 0 ? 'M' : 'L'}${toX(p.i)},${toY(p.v)}`
  ).join(' ');

  const line = `<path d="${pathD}" fill="none" stroke="#371704" stroke-width="2.5"/>`;

  const dots = activePoints.map(p => {
    const isCurrent = p.label === currentMonth;
    const r = isCurrent ? 7 : 4;
    const fill = isCurrent ? '#C00000' : '#371704';
    return `
    <circle cx="${toX(p.i)}" cy="${toY(p.v)}" r="${r}" fill="${fill}" stroke="#fff" stroke-width="2"/>
    ${isCurrent ? `<text x="${toX(p.i)}" y="${toY(p.v) - 14}" text-anchor="middle"
      font-size="14" fill="#C00000" font-weight="800">${p.v.toLocaleString()}</text>` : ''}`;
  }).join('');

  const xLabels = data.map((d, i) =>
    `<text x="${toX(i)}" y="${padT + chartH + 28}" text-anchor="middle"
      font-size="14" fill="#936435" font-weight="${d.label === currentMonth ? '800' : '400'}">${d.label || ''}</text>`
  ).join('');

  let targetLine = '';
  if (target && target > minVal) {
    const ty = toY(target);
    targetLine = `
    <line x1="${padL}" y1="${ty}" x2="${padL + chartW}" y2="${ty}"
      stroke="#FFC000" stroke-width="2" stroke-dasharray="8,4"/>
    <text x="${padL + chartW + 4}" y="${ty + 4}" font-size="13" fill="#FFC000" font-weight="700">
      목표 ${(target/1000).toFixed(0)}K</text>`;
  }

  const ticks = [0, 0.25, 0.5, 0.75, 1.0].map(f => {
    const v  = Math.round(minVal + (maxVal - minVal) * f);
    const ty = padT + chartH - f * chartH;
    return `
    <line x1="${padL}" y1="${ty}" x2="${padL + chartW}" y2="${ty}"
      stroke="#EDE5DF" stroke-width="0.5"/>
    <text x="${padL - 8}" y="${ty + 4}" text-anchor="end"
      font-size="13" fill="#936435">${v >= 1000 ? (v/1000).toFixed(1)+'K' : v}</text>`;
  }).join('');

  return `
  <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    ${ticks}
    <line x1="${padL}" y1="${padT+chartH}" x2="${padL+chartW}" y2="${padT+chartH}"
      stroke="#C8B9B0" stroke-width="1"/>
    ${targetLine}
    ${line}
    ${dots}
    ${xLabels}
  </svg>`;
}

function buildSlideHtml(slide) {
  const d = slide.data || {};
  switch (slide.template) {
    case 'title':            return _tmplTitle(d);
    case 'calendar':         return _tmplCalendar(d, slide.slide_number);
    case 'kpi':              return _tmplKpi(d, slide.slide_number);
    case 'engagement':       return _tmplEngagement(d, slide.slide_number);
    case 'popular_content':  return _tmplPopular(d, slide.slide_number);
    case 'story_strategy':   return _tmplStory(d, slide.slide_number);
    case 'operating_review': return _tmplReview(d, slide.slide_number);
    case 'closing':          return _tmplClosing(d);
    default:                 return _tmplFallback(d, slide.slide_number, slide.template);
  }
}

function _tmplTitle(d) {
  return `
  <div style="width:1920px;height:1080px;background:#371704;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">

    <div style="position:absolute;top:0;left:0;right:0;bottom:0;
      display:flex;flex-direction:column;justify-content:center;padding:0 120px 0 80px;">

      <div style="margin-bottom:36px;">
        <span data-field="client_name" style="display:inline-block;padding:8px 24px;background:#936435;
          color:#FFFFFF;font-size:18px;font-weight:700;letter-spacing:0.14em;
          text-transform:uppercase;outline:none;">${d.client_name || 'HIZ-NDG'}</span>
      </div>

      <h1 data-field="main_title" style="font-size:68px;font-weight:900;color:#FFFFFF;line-height:1.1;
        margin:0 0 16px;letter-spacing:-0.02em;outline:none;">
        ${d.main_title || 'SNS Monthly Report'}
      </h1>

      <div data-field="sub_title" style="font-size:40px;font-weight:300;color:#E7DCD5;letter-spacing:0.04em;
        margin-bottom:52px;outline:none;min-height:48px;">
        ${d.sub_title || ''}
      </div>

      <div style="width:52px;height:3px;background:#C8B9B0;"></div>
    </div>

    <div style="position:absolute;bottom:48px;right:80px;
      font-size:18px;font-weight:500;color:#C8B9B0;letter-spacing:0.04em;">
      ${d.report_date || ''}
    </div>
  </div>`;
}

function _tmplCalendar(d, num) {
  const summary        = d.summary || '';
  const feedReelCount  = d.feed_reel_count  ?? (summary.match(/피드&릴스\s*(\d+)/) || [, '–'])[1];
  const storyCount     = d.story_count      ?? (summary.match(/스토리\s*(\d+)/)     || [, '–'])[1];
  const total          = (summary.match(/총\s*(\d+)/) || [, '–'])[1];

  const types = [
    { label: 'FEED & REELS', ko: '피드&릴스', count: feedReelCount, color: '#371704' },
    { label: 'STORY',        ko: '스토리',    count: storyCount,    color: '#FFC000' },
  ];

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Monthly Content')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;padding:44px 80px;gap:56px;">

      <div style="flex:1;display:flex;flex-direction:column;min-width:0;">
        ${_secHead('CALENDAR', d.section_title || '월간 콘텐츠 캘린더', '', 'section_title')}
        ${_buildCalGrid(d.report_month || '2026-02', d.calendar_entries || [])}
      </div>

      <div style="width:360px;flex-shrink:0;display:flex;flex-direction:column;gap:14px;">

        <div style="background:#371704;padding:24px 28px;">
          <div style="font-size:18px;font-weight:700;letter-spacing:0.16em;
            color:rgba(231,220,213,0.7);text-transform:uppercase;margin-bottom:8px;">TOTAL</div>
          <div style="display:flex;align-items:baseline;gap:8px;">
            <span style="font-size:68px;font-weight:900;color:#FFFFFF;line-height:1;">${total}</span>
            <span style="font-size:18px;font-weight:300;color:rgba(231,220,213,0.6);">건</span>
          </div>
          <div style="font-size:18px;color:rgba(231,220,213,0.45);margin-top:4px;">
            이달 총 콘텐츠 운영</div>
        </div>

        ${types.map(t => `
        <div style="background:#FAFAF8;border-left:4px solid ${t.color};padding:16px 22px;
          display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:18px;font-weight:700;letter-spacing:0.14em;color:${t.color};
              text-transform:uppercase;margin-bottom:4px;">${t.label}</div>
            <div style="font-size:18px;color:#936435;">${t.ko}</div>
          </div>
          <div style="display:flex;align-items:baseline;gap:6px;">
            <span style="font-size:36px;font-weight:900;color:#371704;line-height:1;">${t.count}</span>
            <span style="font-size:18px;color:#936435;">건</span>
          </div>
        </div>`).join('')}

        <div style="border-left:4px solid #936435;background:#F5F0EB;padding:16px 20px;margin-top:auto;">
          <div style="font-size:18px;font-weight:700;letter-spacing:0.14em;color:#936435;
            text-transform:uppercase;margin-bottom:6px;">HIGHLIGHT</div>
          ${d.format_counts ? `<p style="font-size:18px;color:#371704;font-weight:500;margin:0;line-height:1.6;">
            이미지 ${d.format_counts.image}건 &nbsp;/&nbsp; 영상 ${d.format_counts.video}건 &nbsp;/&nbsp; 캐러셀 ${d.format_counts.carousel}건
            ${d.highlight_note ? '<br>' + d.highlight_note : ''}</p>` :
            `<p data-field="highlight_note" style="font-size:18px;color:#371704;font-weight:500;margin:0;line-height:1.6;outline:none;min-height:20px;">
            ${d.highlight_note || ''}</p>`}
        </div>
      </div>
    </div>

    ${_ftr('')}
  </div>`;
}

function _svgDualLineChart(data, width, height, currentMonth) {
  if (!data || !data.length) return '';
  const reachVals = data.map(d => d.reach || 0).filter(v => v > 0);
  const interVals = data.map(d => d.interactions || 0).filter(v => v > 0);
  if (!reachVals.length && !interVals.length) return '';

  const allVals = [...reachVals, ...interVals];
  const maxVal = Math.max(...allVals) * 1.15;
  const padL = 80, padR = 70, padT = 30, padB = 48;
  const chartW = width - padL - padR;
  const chartH = height - padT - padB;
  const gap = chartW / Math.max(data.length - 1, 1);

  const toX = i => padL + i * gap;
  const toY = v => maxVal > 0 ? padT + chartH - (v / maxVal) * chartH : padT + chartH;

  // 현재 월 레이블을 오른쪽 여백에 세로 나열 (도달 위, 인터랙션 아래)
  const labelOffsetY = { reach: -10, interactions: 10 };

  function buildLine(key, color) {
    const pts = data.map((d, i) => ({i, v: d[key] || 0, label: d.label || ''})).filter(p => p.v > 0);
    if (!pts.length) return '';
    const pathD = pts.map((p, idx) => `${idx === 0 ? 'M' : 'L'}${toX(p.i)},${toY(p.v)}`).join(' ');
    const dots = pts.map(p => {
      const isCur = p.label === currentMonth;
      if (!isCur) return `<circle cx="${toX(p.i)}" cy="${toY(p.v)}" r="3" fill="${color}" stroke="#fff" stroke-width="1"/>`;
      const x = toX(p.i);
      const y = toY(p.v);
      // 레이블은 오른쪽 여백 영역(dot 오른쪽 10px)에 anchor="start"로 표시
      const lx = x + 10;
      const ly = y + (labelOffsetY[key] || 0);
      return `<circle cx="${x}" cy="${y}" r="6" fill="${color}" stroke="#fff" stroke-width="2"/>
        <text x="${lx}" y="${ly}" text-anchor="start"
          font-size="13" fill="${color}" font-weight="800">${p.v.toLocaleString()}</text>`;
    }).join('');
    return `<path d="${pathD}" fill="none" stroke="${color}" stroke-width="2.5"/>${dots}`;
  }

  const xLabels = data.map((d, i) =>
    `<text x="${toX(i)}" y="${padT + chartH + 28}" text-anchor="middle"
      font-size="13" fill="#936435" font-weight="${d.label === currentMonth ? '800' : '400'}">${d.label || ''}</text>`
  ).join('');

  const ticks = [0, 0.25, 0.5, 0.75, 1.0].map(f => {
    const v = Math.round(maxVal * f);
    const ty = padT + chartH - f * chartH;
    return `<line x1="${padL}" y1="${ty}" x2="${padL + chartW}" y2="${ty}" stroke="#EDE5DF" stroke-width="0.5"/>
    <text x="${padL - 8}" y="${ty + 4}" text-anchor="end" font-size="13" fill="#936435">
      ${v >= 1000 ? (v/1000).toFixed(0)+'K' : v}</text>`;
  }).join('');

  // 범례
  const legend = `
    <text x="${padL}" y="${padT - 6}" font-size="13" fill="#371704" font-weight="700">● 도달</text>
    <text x="${padL + 70}" y="${padT - 6}" font-size="13" fill="#C00000" font-weight="700">● 인터랙션</text>`;

  return `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    ${ticks}
    <line x1="${padL}" y1="${padT+chartH}" x2="${padL+chartW}" y2="${padT+chartH}" stroke="#C8B9B0" stroke-width="1"/>
    ${legend}
    ${buildLine('reach', '#371704')}
    ${buildLine('interactions', '#C00000')}
    ${xLabels}
  </svg>`;
}

function _kpiTargetTable(targets) {
  if (!targets) return '';
  const r = targets.reach        || {};
  const i = targets.interactions || {};
  const fmt = v => v ? v.toLocaleString() : '-';
  const thS = 'padding:4px 6px;font-size:14px;font-weight:700;color:#FFFFFF;text-align:center;background:#371704;border:1px solid rgba(255,255,255,0.15);white-space:nowrap;';
  const tdS = 'padding:4px 6px;font-size:14px;color:#371704;text-align:right;border:1px solid #E7DCD5;white-space:nowrap;';
  const td1S = 'padding:4px 6px;font-size:14px;font-weight:700;color:#936435;text-align:left;border:1px solid #E7DCD5;background:#FAFAF8;white-space:nowrap;';
  const tdHl = 'padding:4px 6px;font-size:14px;font-weight:700;color:#C00000;text-align:right;border:1px solid #E7DCD5;white-space:nowrap;';
  return `
  <div style="border-bottom:1px solid #E7DCD5;padding-bottom:14px;">
    <div style="font-size:13px;font-weight:700;letter-spacing:0.14em;color:#936435;
      text-transform:uppercase;margin-bottom:6px;">목표 KPI</div>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr>
          <th style="${thS}">구분</th>
          <th style="${thS}">월 목표</th>
          <th style="${thS}">3개월</th>
          <th style="${thS}">연간</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="${td1S}">도달</td>
          <td style="${tdS}">${fmt(r.monthly)}</td>
          <td style="${tdS}">${fmt(r.q3)}</td>
          <td style="${tdHl}">${fmt(r.annual)}</td>
        </tr>
        <tr>
          <td style="${td1S}">인터랙션</td>
          <td style="${tdS}">${fmt(i.monthly)}</td>
          <td style="${tdS}">${fmt(i.q3)}</td>
          <td style="${tdHl}">${fmt(i.annual)}</td>
        </tr>
        <tr>
          <td style="${td1S}" colspan="3" style="padding:4px 6px;font-size:14px;font-weight:700;color:#936435;border:1px solid #E7DCD5;background:#FAFAF8;">평균 IPP</td>
          <td style="${tdHl}">${fmt(i.ipp)}</td>
        </tr>
      </tbody>
    </table>
  </div>`;
}

function _tmplKpi(d, num) {
  const metrics = d.metrics || [];
  const trend   = d.monthly_trend || [];

  let currentMonth = '';
  try {
    const m = parseInt((d.report_month || '').split('-')[1]);
    currentMonth = m + '월';
  } catch(e) {}

  // ── 팔로워 + 도달 + 인터랙션 3행 테이블 ──
  const kpiTable = trend.length > 0 ? (() => {
    const thS = 'padding:6px 8px;font-size:18px;font-weight:700;color:#371704;text-align:center;border:1px solid #C8B9B0;white-space:nowrap;';
    const tdS = 'padding:5px 8px;font-size:18px;color:#371704;text-align:center;border:1px solid #EDE5DF;white-space:nowrap;';

    const mh = trend.map(t =>
      `<th style="${thS}background:#E7DCD5;color:#371704;">${t.label}</th>`
    ).join('');

    function row(label, key) {
      return `<tr><td style="${tdS}font-weight:700;font-size:18px;background:#FAFAF8;">${label}</td>` +
        trend.map(t => {
          const v = t[key] || 0;
          return `<td style="${tdS}">${v > 0 ? v.toLocaleString() : '-'}</td>`;
        }).join('') + '</tr>';
    }

    return `<div style="margin-bottom:12px;">
      <table style="width:100%;border-collapse:collapse;table-layout:fixed;">
        <thead><tr><th style="${thS}background:#E7DCD5;width:80px;">지표</th>${mh}</tr></thead>
        <tbody>${row('팔로워','followers')}${row('도달','reach')}${row('인터랙션','interactions')}</tbody>
      </table></div>`;
  })() : '';

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'KPI Summary')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;gap:0;padding:0;">

      <!-- 왼쪽: 테이블 + 도달/인터랙션 그래프 + 오버뷰 -->
      <div style="flex:1;padding:24px 40px 24px 80px;display:flex;flex-direction:column;gap:10px;min-height:0;">
        ${_secHead('KPI', d.section_title || 'KPI 대비 채널 운영 성과', d.table_caption || '', 'section_title')}
        ${kpiTable}
        ${trend.length > 0 ? `
        <div style="flex-shrink:0;">
          <div style="font-size:13px;font-weight:700;letter-spacing:0.12em;color:#936435;
            text-transform:uppercase;margin-bottom:4px;">도달 · 인터랙션 월간 추이</div>
          <div style="display:flex;align-items:flex-end;">
            ${_svgDualLineChart(trend, 820, 220, currentMonth)}
          </div>
        </div>` : ''}

        <!-- Overall 오버뷰 -->
        <div style="flex-shrink:0;margin-top:26px;">
          <div style="font-size:13px;font-weight:700;letter-spacing:0.14em;color:#C00000;
            text-transform:uppercase;margin-bottom:5px;">OVERALL · ${currentMonth} 운영 개요</div>
          <div data-field="overview" style="border-left:4px solid #936435;background:#F5F0EB;padding:10px 16px;
            outline:none;font-size:18px;color:#371704;font-weight:400;line-height:1.75;word-break:keep-all;">
            ${(d.overview || d.summary_sentence)
              ? (d.overview || d.summary_sentence)
              : `<p style="color:#936435;font-style:italic;margin:0;">운영 개요를 입력하세요</p>`}
          </div>
        </div>
      </div>

      <div style="width:2px;background:#E7DCD5;flex-shrink:0;margin:44px 0;"></div>

      <!-- 오른쪽: 요약 메트릭 카드 + 목표 KPI 테이블 -->
      <div style="width:480px;flex-shrink:0;padding:28px 48px 28px 36px;
        display:flex;flex-direction:column;gap:10px;justify-content:center;">
        ${_kpiTargetTable(d.kpi_targets)}
        ${metrics.map(m => {
          const noDir = m.delta_direction === 'none' || m.delta == null;
          const isUp = m.delta_direction === 'up';
          const tc   = noDir ? '#936435' : (isUp ? '#2E7D32' : '#C00000');
          const bgc  = isUp ? '#E8F5E9' : '#FFEBEE';
          const delta = m.delta || 0;
          const subs  = m.sub_items || [];
          return `
          <div style="background:#FAFAF8;border-left:4px solid ${tc};padding:10px 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
              <div>
                <div style="font-size:15px;font-weight:700;letter-spacing:0.1em;
                  color:#936435;margin-bottom:2px;">${m.label}</div>
                <div style="font-size:26px;font-weight:900;color:#371704;line-height:1;">
                  ${(m.current || 0).toLocaleString()}</div>
              </div>
              ${(!noDir && delta !== 0) ? `
              <div style="font-size:15px;font-weight:700;color:${tc};
                background:${bgc};padding:3px 8px;white-space:nowrap;">
                ${isUp ? '▲' : '▼'} ${Math.abs(delta).toLocaleString()}
              </div>` : ''}
            </div>
            ${subs.length ? `
            <div style="margin-top:6px;padding-top:5px;border-top:1px solid #E7DCD5;display:flex;gap:10px;">
              ${subs.map(s => `
              <div style="flex:1;">
                <div style="font-size:11px;color:#936435;font-weight:600;letter-spacing:0.05em;">${s.label}</div>
                <div style="font-size:14px;font-weight:700;color:#371704;">${(s.value || 0).toLocaleString()}</div>
              </div>`).join('')}
            </div>` : ''}
          </div>`;
        }).join('')}
      </div>
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplEngagement(d, num) {
  const rows      = d.content_table    || [];
  const mom       = d.mom_comparison   || [];
  const breakdown = d.content_breakdown || [];

  if (rows.length > 0) {
    return _tmplEngagementTable(d, num, rows);
  }

  const typeColors = { '피드': '#371704', '스토리': '#936435', '릴스': '#FFC000' };
  const maxInteractions = Math.max(...breakdown.map(b => b.interactions || 0), 1);

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Engagement')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;flex-direction:column;padding:44px 80px;">
      ${_secHead('ENGAGEMENT', d.section_title || '인게이지먼트 분석', '', 'section_title')}

      <div style="display:flex;gap:72px;flex:1;">

        <div style="flex:1;display:flex;flex-direction:column;">
          <div style="font-size:18px;font-weight:700;letter-spacing:0.12em;color:#936435;
            text-transform:uppercase;padding-bottom:12px;border-bottom:2px solid #371704;">
            전월 대비 지표 변화</div>
          <table style="width:100%;border-collapse:collapse;flex:1;">
            ${mom.map(item => `
            <tr style="border-bottom:1.5px solid #EDE5DF;">
              <td style="padding:24px 0;font-size:17px;color:#936435;font-weight:500;">
                ${item.metric}</td>
              <td style="padding:24px 0;font-size:32px;font-weight:800;color:#371704;text-align:right;">
                ${(item.current || 0).toLocaleString()}</td>
              <td style="padding:24px 0;padding-left:16px;text-align:right;width:150px;">
                <span style="font-size:15px;font-weight:700;padding:4px 10px;
                  background:${item.direction === 'up' ? '#E8F5E9' : '#FFEBEE'};
                  color:${item.direction === 'up' ? '#2E7D32' : '#C00000'};">
                  ${item.direction === 'up' ? '▲' : '▼'} ${Math.abs(item.delta_pct || 0).toFixed(1)}%
                </span>
              </td>
            </tr>`).join('')}
          </table>
        </div>

        <div style="width:2px;background:#E7DCD5;flex-shrink:0;"></div>

        <div style="flex:1;display:flex;flex-direction:column;">
          <div style="font-size:18px;font-weight:700;letter-spacing:0.12em;color:#936435;
            text-transform:uppercase;padding-bottom:12px;border-bottom:2px solid #371704;">
            콘텐츠 유형별 인터랙션</div>
          <div style="padding-top:24px;flex:1;display:flex;flex-direction:column;justify-content:space-around;">
            ${breakdown.map(b => {
              const color  = typeColors[b.type] || '#936435';
              const barPct = Math.round((b.interactions / maxInteractions) * 100);
              return `
              <div>
                <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:10px;">
                  <span style="font-size:17px;font-weight:600;color:#371704;">${b.type}</span>
                  <div style="display:flex;align-items:baseline;gap:12px;">
                    <span style="font-size:18px;color:#936435;">${(b.interactions||0).toLocaleString()}</span>
                    <span style="font-size:26px;font-weight:800;color:${color};">${b.pct}%</span>
                  </div>
                </div>
                <div style="height:14px;background:#EDE5DF;">
                  <div style="height:100%;width:${barPct}%;background:${color};"></div>
                </div>
              </div>`;
            }).join('')}
          </div>
        </div>
      </div>

      ${d.summary_sentence ? `
      <div style="border-left:4px solid #936435;background:#F5F0EB;margin-top:24px;padding:16px 22px;">
        <p style="font-size:17px;color:#371704;font-weight:500;margin:0;">${d.summary_sentence}</p>
      </div>` : ''}
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplEngagementTable(d, num, rows) {
  // NO / 발행일 / 소재 / 유형 / 게재위치 / 노출 / 도달 / 좋아요 / 댓글 / 공유 / 리포스트 / 저장 / 총인터랙션 / 프로필방문 / 팔로우 / 광고예산
  const cols = [
    {key:'no',            label:'NO',        w:'38px',  num:false},
    {key:'date',          label:'발행일',    w:'62px',  num:false},
    {key:'title',         label:'소재',      w:'220px', num:false},
    {key:'type',          label:'유형',      w:'58px',  num:false},
    {key:'placement',     label:'게재위치',  w:'80px',  num:false},
    {key:'impressions',   label:'노출',      w:'72px',  num:true},
    {key:'reach',         label:'도달',      w:'72px',  num:true},
    {key:'likes',         label:'좋아요',    w:'62px',  num:true},
    {key:'comments',      label:'댓글',      w:'62px',  num:true},
    {key:'shares',        label:'공유',      w:'52px',  num:true},
    {key:'reposts',       label:'리포스트',  w:'62px',  num:true},
    {key:'saves',         label:'저장',      w:'52px',  num:true},
    {key:'interactions',  label:'총인터랙션',w:'80px',  num:true},
    {key:'profile_visits',label:'프로필방문',w:'72px',  num:true},
    {key:'follows',       label:'팔로우',    w:'60px',  num:true},
    {key:'ad_spend',      label:'광고예산',  w:'68px',  num:true},
  ];

  const SUM_KEYS = new Set(['impressions','reach','likes','comments','shares','reposts',
                            'saves','interactions','profile_visits','follows','ad_spend']);

  const BD  = '1px solid #AAAAAA';   // 일반 셀 경계선
  const BDH = '1.5px solid #888888'; // 헤더/TOTAL 경계선

  const thead = cols.map(c =>
    `<th style="padding:7px 6px;background:#E7DCD5;font-size:15px;font-weight:700;
      letter-spacing:0.04em;color:#371704;text-align:center;
      border:${BDH};white-space:nowrap;width:${c.w};">${c.label}</th>`
  ).join('');

  const tbody = rows.map((r, i) =>
    `<tr>
      ${cols.map(c => {
        if (c.key === 'date'  && r.date_rowspan  === 0) return '';
        if (c.key === 'title' && r.title_rowspan === 0) return '';

        const rs = c.key === 'date'  && r.date_rowspan  > 1 ? ` rowspan="${r.date_rowspan}"` :
                   c.key === 'title' && r.title_rowspan > 1 ? ` rowspan="${r.title_rowspan}"` : '';
        const v = r[c.key];
        const isNum = c.num && typeof v === 'number';
        const txt = isNum ? (v > 0 ? v.toLocaleString() : '-') : (v || '-');
        const isTitle = c.key === 'title';
        return `<td${rs}${isTitle ? ` data-field="content_table.${i}.title" contenteditable="true"` : ''}
          style="padding:6px 6px;font-size:15px;color:#371704;background:#FFFFFF;
          text-align:${isNum ? 'right' : 'center'};vertical-align:middle;
          border:${BD};outline:none;
          ${isNum ? 'white-space:nowrap;' : isTitle ? 'word-break:keep-all;line-height:1.4;' : 'white-space:nowrap;'}">${txt}</td>`;
      }).join('')}
    </tr>`
  ).join('');

  const labelCols = cols.filter(c => !SUM_KEYS.has(c.key));
  const sumCols   = cols.filter(c =>  SUM_KEYS.has(c.key));
  const totalLabelCell = `<td colspan="${labelCols.length}"
    style="padding:7px 6px;font-size:15px;font-weight:700;color:#371704;
      text-align:center;background:#E7DCD5;border:${BDH};letter-spacing:0.1em;">TOTAL</td>`;
  const totalSumCells = sumCols.map(c => {
    const sum = rows.reduce((a,r) => a + (r[c.key] || 0), 0);
    return `<td style="padding:7px 6px;font-size:15px;font-weight:700;color:#371704;
      text-align:right;background:#E7DCD5;border:${BDH};">${sum > 0 ? sum.toLocaleString() : '-'}</td>`;
  }).join('');
  const totals = totalLabelCell + totalSumCells;

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Content Performance')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;flex-direction:column;padding:28px 60px 24px;overflow:hidden;">

      <div style="margin-bottom:16px;">
        <div style="font-size:13px;font-weight:700;letter-spacing:0.18em;color:#C00000;
          text-transform:uppercase;margin-bottom:4px;">ENGAGEMENT</div>
        <h2 data-field="section_title" style="font-size:32px;font-weight:900;color:#371704;
          line-height:1.1;margin:0;outline:none;">${d.section_title || '운영 현황'}</h2>
      </div>

      <div data-field="summary_sentence" contenteditable="true"
        style="border-left:4px solid #936435;background:#F5F0EB;margin-bottom:14px;
          padding:10px 16px;outline:none;min-height:28px;flex-shrink:0;">
        <div style="font-size:18px;color:#371704;font-weight:500;margin:0;line-height:1.8;">${d.summary_sentence || ''}</div>
      </div>

      <div style="flex:1;min-height:0;">
        <table style="width:100%;border-collapse:collapse;border:${BDH};table-layout:fixed;">
          <thead><tr>${thead}</tr></thead>
          <tbody>${tbody}</tbody>
          <tfoot><tr>${totals}</tr></tfoot>
        </table>
      </div>
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplPopular(d, num) {
  const posts      = d.top_posts || [];
  const rankColors = ['#371704', '#371704', '#371704'];

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Top Content')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;flex-direction:column;padding:44px 80px;">
      ${_secHead('POPULAR CONTENT', d.section_title || '인기 콘텐츠 분석', '', 'section_title')}

      <div style="display:flex;gap:20px;flex:1;">
        ${posts.map((p, idx) => {
          const rankColor = rankColors[idx] || '#C8B9B0';
          const hasImg    = !!p.image_url;
          return `
          <div style="flex:1;display:flex;flex-direction:column;border:1.5px solid #EDE5DF;">
            <div style="background:${rankColor};padding:12px 20px;
              display:flex;align-items:center;gap:12px;">
              <span style="font-size:32px;font-weight:900;color:rgba(255,255,255,0.9);line-height:1;">
                ${p.rank}</span>
              <div>
                <div style="font-size:18px;color:rgba(255,255,255,0.8);">${p.date || ''}</div>
                ${p.badge === '도달·인터랙션'
                  ? `<span style="font-size:12px;background:#C47B28;color:#fff;
                      padding:2px 8px;border-radius:999px;font-weight:700;letter-spacing:0.06em;">도달·인터랙션 TOP</span>`
                  : p.badge === '도달'
                  ? `<span style="font-size:12px;background:#A06830;color:#fff;
                      padding:2px 8px;border-radius:999px;font-weight:700;letter-spacing:0.06em;">도달 TOP</span>`
                  : `<span style="font-size:12px;background:#936435;color:#fff;
                      padding:2px 8px;border-radius:999px;font-weight:700;letter-spacing:0.06em;">인터랙션 TOP</span>`}
              </div>
            </div>

            <div class="slide-dropzone" data-drop-field="top_posts.${idx}.image_url"
              style="flex:1;position:relative;overflow:hidden;cursor:pointer;"
              title="이미지를 드래그하여 놓거나 클릭하세요">
              ${hasImg ? `
              <img src="${p.image_url}" style="width:100%;height:100%;object-fit:cover;"
                onerror="this.style.display='none';"/>
              <button class="slide-img-remove" style="position:absolute;top:8px;right:8px;z-index:20;
                background:rgba(0,0,0,0.55);color:#fff;border:none;border-radius:50%;
                width:28px;height:28px;line-height:28px;text-align:center;cursor:pointer;font-size:16px;
                opacity:0;transition:opacity 0.15s;padding:0;" title="이미지 제거">×</button>` : `
              <div style="position:absolute;inset:0;background:#F5F0EB;"></div>`}
              <div style="position:absolute;top:12px;left:12px;right:12px;
                border-left:4px solid #936435;background:rgba(245,240,235,0.95);padding:10px 14px;">
                <p data-field="top_posts.${idx}.description" style="font-size:18px;color:#371704;font-weight:600;margin:0;line-height:1.4;outline:none;">
                  ${(p.description || '').split(' — ')[0]}</p>
              </div>
            </div>

            <div style="display:flex;border-top:1.5px solid #EDE5DF;margin-top:auto;">
              <div style="flex:1;padding:14px 0;text-align:center;border-right:1.5px solid #EDE5DF;">
                <div style="font-size:18px;color:#936435;font-weight:600;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:4px;">인터랙션</div>
                <div style="font-size:28px;font-weight:900;color:#371704;">
                  ${(p.interactions || 0).toLocaleString()}</div>
              </div>
              <div style="flex:1;padding:14px 0;text-align:center;">
                <div style="font-size:18px;color:#936435;font-weight:600;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:4px;">도달</div>
                <div style="font-size:28px;font-weight:900;color:#371704;">
                  ${(p.reach || 0).toLocaleString()}</div>
              </div>
            </div>
            ${p.analysis ? `
            <div data-field="top_posts.${idx}.analysis" contenteditable="true"
              style="border-top:1.5px solid #EDE5DF;padding:12px 16px;background:#FAFAF8;outline:none;
                height:160px;overflow:hidden;flex-shrink:0;">
              <p style="font-size:18px;color:#371704;font-weight:400;margin:0;line-height:1.7;">
                ${p.analysis}</p>
            </div>` : ''}
          </div>`;
        }).join('')}
      </div>

      ${d.insight_line ? `
      <div style="display:flex;align-items:center;gap:14px;margin-top:16px;">
        <div style="width:4px;height:18px;background:#936435;flex-shrink:0;"></div>
        <span style="font-size:16px;color:#371704;font-weight:500;">${d.insight_line}</span>
      </div>` : ''}
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplStory(d, num) {
  const contentAds    = d.content_ads || [];
  const totals        = d.content_ad_totals || {};
  const contentSpend  = d.content_ad_spend || 0;
  const darkSpend     = d.dark_ad_spend || 0;
  const totalSpend    = d.total_ad_spend || (contentSpend + darkSpend);
  const darkAds       = d.dark_posting_ads || [];
  const insights      = d.insights || [];

  const BD  = '1px solid #AAAAAA';
  const BDH = '1.5px solid #888888';

  function _th(h, w) {
    const html = String(h).replace(/\n/g, '<br>');
    const wrapStyle = h.includes('\n') ? 'white-space:normal;line-height:1.35;' : 'white-space:nowrap;';
    return `<th style="padding:7px 6px;background:#E7DCD5;color:#371704;font-size:15px;font-weight:700;
      text-align:center;border:${BDH};${wrapStyle}${w?'width:'+w+';':''}"">${html}</th>`;
  }
  function _td(v, bg, right=false, isLeft=false) {
    return `<td style="padding:5px 8px;font-size:15px;color:#371704;background:${bg};
      border:${BD};text-align:${isLeft?'left':right?'right':'center'};white-space:nowrap;">${v ?? '-'}</td>`;
  }
  function _tdTot(v, right=false) {
    return `<td style="padding:6px 8px;font-size:15px;font-weight:700;color:#371704;background:#E7DCD5;
      border:${BDH};text-align:${right?'right':'center'};">${v ?? '-'}</td>`;
  }
  function _n(v)  { return v ? Number(v).toLocaleString() : '-'; }
  function _badge(label, bg) {
    return `<span style="display:inline-block;background:${bg};color:#fff;font-size:10px;
      font-weight:700;padding:2px 6px;border-radius:3px;letter-spacing:0.03em;">${label}</span>`;
  }

  // ── 콘텐츠 광고 테이블 ──
  // 컬럼: 발행일|소재|유형|노출|도달|좋아요|댓글|공유|리포스트|저장|총 인터랙션|광고기간|광고 목표|타겟
  const cThRow = [
    _th('발행일','50px'), _th('소재','210px'), _th('유형','62px'),
    _th('노출','82px'), _th('도달','82px'),
    _th('좋아요','54px'), _th('댓글','50px'), _th('공유','50px'), _th('리포스트','62px'), _th('저장','50px'),
    _th('총 인터랙션','88px'), _th('광고기간','124px'), _th('광고 목표','64px'), _th('타겟','280px'),
  ].join('');

  const cTbRows = contentAds.map((r, i) => {
    const bg = i % 2 === 0 ? '#FAFAF8' : '#F5F0EB';
    const objBg = (r.campaign_type || '') === '참여' ? '#C47B28' : '#7B5230';
    const tdWrap = (v, isLeft=false) =>
      `<td style="padding:5px 8px;font-size:15px;color:#371704;background:${bg};
        border:${BD};text-align:${isLeft?'left':'center'};word-break:keep-all;line-height:1.4;">${v ?? '-'}</td>`;
    return `<tr>
      ${_td(r.date || '-', bg)}
      ${_td(r.title || '-', bg, false, true)}
      ${_td(r.format || '-', bg)}
      ${_td(_n(r.impressions), bg, true)}
      ${_td(_n(r.reach), bg, true)}
      ${_td(_n(r.likes), bg, true)}
      ${_td(_n(r.comments), bg, true)}
      ${_td(_n(r.shares), bg, true)}
      ${_td(_n(r.reposts), bg, true)}
      ${_td(_n(r.saves), bg, true)}
      ${_td(_n(r.interactions), bg, true)}
      ${_td(r.ad_period || '-', bg)}
      ${_td(_badge(r.campaign_type || '인지도', objBg), bg)}
      ${tdWrap(r.ad_target || '-', true)}
    </tr>`;
  }).join('');

  const totImp  = totals.impressions || contentAds.reduce((s,r)=>s+(r.impressions||0),0);
  const totRch  = totals.reach || contentAds.reduce((s,r)=>s+(r.reach||0),0);
  const totIntr = totals.interactions || contentAds.reduce((s,r)=>s+(r.interactions||0),0);
  const totLikes= contentAds.reduce((s,r)=>s+(r.likes||0),0);
  const totCmt  = contentAds.reduce((s,r)=>s+(r.comments||0),0);
  const totShr  = contentAds.reduce((s,r)=>s+(r.shares||0),0);
  const totRep  = contentAds.reduce((s,r)=>s+(r.reposts||0),0);
  const totSav  = contentAds.reduce((s,r)=>s+(r.saves||0),0);

  const cTfRow = `<tr>
    ${_tdTot('합계')}${_tdTot('')}${_tdTot('')}
    ${_tdTot(_n(totImp),true)}${_tdTot(_n(totRch),true)}
    ${_tdTot(_n(totLikes),true)}${_tdTot(_n(totCmt),true)}
    ${_tdTot(_n(totShr),true)}${_tdTot(_n(totRep),true)}
    ${_tdTot(_n(totSav),true)}${_tdTot(_n(totIntr),true)}
    ${_tdTot('')}${_tdTot('')}${_tdTot('')}
  </tr>`;

  // ── 다크포스팅 테이블 (Excel 컬럼 구성 그대로) ──
  // 소재|유형|광고기간|광고목표|타겟|집행비용|노출|도달|CPM|Action(참여)|ATR|CPA|Click(링크클릭)|CPC|CTR
  let darkSection = '';
  if (darkAds.length > 0) {
    const dThRow = [
      _th('소재','140px'), _th('유형','72px'), _th('광고기간','128px'), _th('광고 목표','62px'),
      _th('집행 비용','96px'),
      _th('노출','76px'), _th('도달','76px'), _th('CPM','60px'),
      _th('Action\n(참여)','66px'), _th('ATR','48px'), _th('CPA','58px'),
      _th('Click\n(링크클릭)','66px'), _th('CPC','52px'), _th('CTR','48px'),
      _th('타겟','260px'),
    ].join('');

    const dTbRows = darkAds.map((r, i) => {
      const bg = i % 2 === 0 ? '#FAFAF8' : '#F5F0EB';
      const tdWrap = (v, right=false) =>
        `<td style="padding:4px 7px;font-size:15px;color:#371704;background:${bg};
          border:${BD};text-align:${right?'right':'left'};word-break:keep-all;line-height:1.4;overflow:hidden;">${v ?? '-'}</td>`;
      const tdC = (v, right=false) =>
        `<td style="padding:4px 7px;font-size:15px;color:#371704;background:${bg};
          border:${BD};text-align:${right?'right':'center'};white-space:nowrap;overflow:hidden;">${v ?? '-'}</td>`;
      return `<tr>
        ${tdWrap(r.title || '-')}
        ${tdC(r.ad_type || '-')}
        ${tdC(r.ad_period || '-')}
        ${tdC(r.objective || '-')}
        ${tdC(r.spend ? _n(r.spend)+'원' : '-', true)}
        ${tdC(r.impressions ? _n(r.impressions) : '-', true)}
        ${tdC(r.reach ? _n(r.reach) : '-', true)}
        ${tdC(r.cpm || '-', true)}
        ${tdC(r.action ? _n(r.action) : '-', true)}
        ${tdC(r.atr || '-', true)}
        ${tdC(r.cpa || '-', true)}
        ${tdC(r.clicks ? _n(r.clicks) : '-', true)}
        ${tdC(r.cpc || '-', true)}
        ${tdC(r.ctr || '-', true)}
        ${tdWrap(r.target || '-')}
      </tr>`;
    }).join('');

    darkSection = `
    <div style="flex-shrink:0;margin-top:22px;">
      <div style="font-size:18px;font-weight:700;color:#936435;letter-spacing:0.08em;
        text-transform:uppercase;margin-bottom:8px;">다크포스팅 (${darkAds.length}건)</div>
      <table style="width:100%;border-collapse:collapse;border:${BDH};table-layout:fixed;">
        <colgroup>
          <col style="width:140px"><col style="width:72px"><col style="width:128px"><col style="width:62px">
          <col style="width:96px">
          <col style="width:76px"><col style="width:76px"><col style="width:60px">
          <col style="width:66px"><col style="width:48px"><col style="width:58px">
          <col style="width:66px"><col style="width:52px"><col style="width:48px">
          <col style="width:260px">
        </colgroup>
        <thead><tr>${dThRow}</tr></thead>
        <tbody>${dTbRows}</tbody>
      </table>
    </div>`;
  }

  // ── 인사이트 카드 (3개, contenteditable) ──
  const accentColors = ['#936435', '#936435', '#936435'];
  const bgColors     = ['#F5F0EB', '#F5F0EB', '#F5F0EB'];
  const insightCards = insights.slice(0, 3).map((ins, i) => {
    const raw   = typeof ins === 'object' ? (ins.full_sentence || ins.headline || '') : String(ins);
    const parts = raw.split(/\r?\n<br>/).map(s => s.trim()).filter(Boolean);
    const line1 = parts[0] || '';
    const line2raw = parts[1] ? parts[1].replace(/^[→>-]+\s*/, '') : '';
    const arrowSpan = `<span style="color:#936435;font-weight:600;">→</span>`;
    const line2 = line2raw.replace(/\s*→\s*/g, `<br>${arrowSpan} `);
    const built = line1 + (line2 ? `<br>${arrowSpan} ${line2}` : '');
    // <br>→ 직접 포맷(사용자 편집 저장 방식)도 동일하게 색상 처리
    const displayHtml = built.replace(/<br>\s*→\s*/g, `<br>${arrowSpan} `);
    return `
    <div style="border-left:4px solid ${accentColors[i]};background:${bgColors[i]};
      padding:14px 18px;border-radius:0 8px 8px 0;flex:1;min-width:0;">
      <div style="font-size:14px;font-weight:800;color:${accentColors[i]};letter-spacing:0.12em;
        text-transform:uppercase;margin-bottom:6px;">INSIGHT ${i + 1}</div>
      <p contenteditable="true" data-field="insights.${i}"
        style="font-size:18px;color:#371704;line-height:1.65;margin:0;word-break:keep-all;
          outline:none;cursor:text;min-height:1em;">
        ${displayHtml}
      </p>
    </div>`;
  }).join('');

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Ad Performance')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;flex-direction:column;padding:28px 64px 20px;">

      <!-- 상단: 제목 + 광고비 배지 -->
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-shrink:0;">
        <div>
          <div style="font-size:18px;font-weight:700;color:#C00000;letter-spacing:0.18em;
            text-transform:uppercase;margin-bottom:6px;">AD PERFORMANCE</div>
          <h2 style="font-size:36px;font-weight:900;color:#371704;margin:0;line-height:1.1;">
            ${d.section_title || '광고 성과'}</h2>
        </div>
        <div style="display:flex;gap:10px;">
          <div style="background:#F5F0EB;border-radius:8px;padding:8px 18px;text-align:center;">
            <div style="font-size:13px;color:#936435;font-weight:700;letter-spacing:0.05em;margin-bottom:2px;">콘텐츠 광고</div>
            <div style="font-size:22px;font-weight:900;color:#371704;">${contentSpend ? contentSpend.toLocaleString()+'원' : '-'}</div>
          </div>
          <div style="background:#F5F0EB;border-radius:8px;padding:8px 18px;text-align:center;">
            <div style="font-size:13px;color:#936435;font-weight:700;letter-spacing:0.05em;margin-bottom:2px;">다크포스팅</div>
            <div style="font-size:22px;font-weight:900;color:#371704;">${darkSpend ? darkSpend.toLocaleString()+'원' : '-'}</div>
          </div>
          <div style="background:#E7DCD5;border:2px solid #888888;border-radius:8px;padding:8px 18px;text-align:center;">
            <div style="font-size:13px;color:#936435;font-weight:700;letter-spacing:0.05em;margin-bottom:2px;">총 광고비</div>
            <div style="font-size:22px;font-weight:900;color:#371704;">${totalSpend ? totalSpend.toLocaleString()+'원' : '-'}</div>
          </div>
        </div>
      </div>

      <!-- Summary -->
      ${d.summary ? `
      <div data-field="summary" contenteditable="true"
        style="border-left:4px solid #936435;background:#F5F0EB;padding:10px 16px;
          flex-shrink:0;margin-bottom:14px;outline:none;
          font-size:18px;color:#371704;font-weight:400;line-height:1.75;word-break:keep-all;">
        ${d.summary}
      </div>` : ''}

      <!-- 콘텐츠 광고 테이블 -->
      <div style="flex-shrink:0;">
        <div style="font-size:18px;font-weight:700;color:#936435;letter-spacing:0.08em;
          text-transform:uppercase;margin-bottom:8px;">
          콘텐츠 광고 (${contentAds.length}건)</div>
        <table style="width:100%;border-collapse:collapse;border:${BDH};table-layout:fixed;">
          <thead><tr>${cThRow}</tr></thead>
          <tbody>${cTbRows}</tbody>
          <tfoot><tr>${cTfRow}</tr></tfoot>
        </table>
      </div>

      ${darkSection}

      <!-- 인사이트 카드 -->
      ${insightCards ? `<div style="display:flex;gap:16px;margin-top:36px;flex-shrink:0;align-items:flex-start;">${insightCards}</div>` : ''}
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplReview(d, num) {
  const insights = d.insights || [];

  // full_sentence의 \n<br> 구분자로 2줄 분리 → 각각 렌더링
  function renderBody(ins, idx) {
    const raw = ins.full_sentence || ins.headline || '';
    const parts = raw.split(/\r?\n<br>|\r?\n/).map(s => s.trim()).filter(Boolean);
    const line1 = parts[0] || '';
    const line2 = parts[1] || '';
    return `
      <p data-field="insights.${idx}.full_sentence"
        contenteditable="true"
        style="font-size:22px;color:#371704;font-weight:400;margin:0;line-height:1.65;outline:none;word-break:keep-all;">
        ${line1}${line2 ? `<br><span style="color:#936435;">→</span> ${line2.replace(/^[→⟶>-]+\s*/,'')}` : ''}
      </p>`;
  }

  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num, 'Operation Review')}

    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;flex-direction:column;padding:44px 80px;">
      ${_secHead('OPERATION', d.section_title || '운영 리뷰', '', 'section_title')}

      <div style="display:flex;flex-direction:column;gap:28px;flex:1;margin-top:8px;">
        ${insights.map((ins, idx) => `
          <div style="background:#F5F0EB;padding:36px 56px;border-left:none;
            border-top:2px solid #E7DCD5;flex:1;display:flex;flex-direction:column;justify-content:center;">
            <div style="display:flex;align-items:baseline;gap:16px;margin-bottom:14px;">
              <span style="font-size:28px;color:#371704;font-weight:900;line-height:1;">◆</span>
              <span data-field="insights.${idx}.headline"
                contenteditable="true"
                style="font-size:26px;font-weight:800;color:#371704;line-height:1.2;outline:none;">
                ${ins.headline || ''}</span>
            </div>
            ${renderBody(ins, idx)}
          </div>`
        ).join('')}
      </div>
    </div>

    ${_ftr('')}
  </div>`;
}

function _tmplClosing(d) {
  // Slide 9 = Slide 1과 동일한 레이아웃
  return _tmplTitle(d);
}

function _tmplFallback(d, num, template) {
  return `
  <div style="width:1920px;height:1080px;background:#FFFFFF;
    font-family:'Pretendard Variable',Pretendard,sans-serif;position:relative;overflow:hidden;color-scheme:light;">
    ${_hdr(num || 0, template || 'Slide')}
    <div style="position:absolute;top:84px;left:0;right:0;bottom:52px;
      display:flex;align-items:center;justify-content:center;">
      <div style="text-align:center;">
        <p style="font-size:18px;color:#936435;">템플릿: ${template}</p>
        <pre style="font-size:18px;color:#371704;text-align:left;background:#FAFAF8;
          padding:24px;max-width:900px;overflow:auto;border:1px solid #E7DCD5;">
${JSON.stringify(d, null, 2)}</pre>
      </div>
    </div>
    ${_ftr('')}
  </div>`;
}
