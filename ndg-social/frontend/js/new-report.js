/**
 * new-report.js — 새 보고서 생성 (엑셀 업로드 전용)
 */

let selectedFile = null;

// ── 파일 드롭존 ────────────────────────────────────────────────────

const dropzone  = document.getElementById('excel-dropzone');
const fileInput = document.getElementById('excel-file');

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelect(file);
});
fileInput.addEventListener('change', e => {
  if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});

async function handleFileSelect(file) {
  if (!file.name.match(/\.(xlsx|xls)$/i)) {
    showToast('Excel 파일(.xlsx, .xls)만 업로드 가능합니다', 'error');
    return;
  }
  selectedFile = file;
  document.getElementById('file-name').textContent = file.name;
  document.getElementById('file-row-count').textContent =
    `파일 크기: ${(file.size / 1024).toFixed(1)} KB`;
  document.getElementById('file-preview').style.display = 'block';
  dropzone.style.display = 'none';

  // 시트 목록 가져오기
  try {
    const formData = new FormData();
    formData.append('file', file);
    const resp = await apiFetch('/api/reports/sheet-list', {
      method: 'POST', body: formData, headers: {},
    });
    const sheets = resp.sheets || [];
    const options = sheets.map(s => `<option value="${s.index}">${s.name}</option>`).join('');
    document.getElementById('sheet-select').innerHTML = options;
    const kpiOptions = '<option value="none">없음</option>' + options;
    document.getElementById('kpi-sheet-select').innerHTML = kpiOptions;
    // 기본값: KPI 시트가 2개 이상이면 두 번째 시트를 KPI로 자동 선택
    if (sheets.length >= 2) {
      document.getElementById('kpi-sheet-select').value = sheets[1].index;
    }
    document.getElementById('sheet-selector').style.display =
      sheets.length > 0 ? 'block' : 'none';
  } catch (e) {
    document.getElementById('sheet-selector').style.display = 'none';
  }
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  document.getElementById('file-preview').style.display = 'none';
  document.getElementById('sheet-selector').style.display = 'none';
  dropzone.style.display = 'block';
}

// ── 월 입력 → 제목 자동완성 ───────────────────────────────────────

document.getElementById('report-month').addEventListener('change', function() {
  const month = this.value;
  if (!month) return;
  const [y, m] = month.split('-');
  const client = document.getElementById('client-name').value || 'NDG';
  document.getElementById('report-title').value =
    `${client} ${y}년 ${parseInt(m)}월 소셜 운영 보고서`;
});

// ── 폼 제출 ──────────────────────────────────────────────────────

document.getElementById('new-report-form').addEventListener('submit', async function(e) {
  e.preventDefault();

  if (!selectedFile) {
    showToast('Excel 파일을 업로드해주세요', 'error');
    return;
  }

  const btn = document.getElementById('create-btn');
  btn.disabled = true;

  const formData    = new FormData(this);
  const reportMonth = formData.get('report_month');
  const title       = formData.get('title');
  const clientName  = formData.get('client_name') || 'HIZ-NDG';
  const followersStart = parseInt(formData.get('followers_start')) || 0;
  const followersEnd   = parseInt(formData.get('followers_end'))   || 0;
  const sheetName      = formData.get('sheet_name') || '0';
  const kpiSheetName   = formData.get('kpi_sheet_name') || 'none';

  try {
    // 1. 보고서 생성
    btn.textContent = '보고서 생성 중...';
    const report = await apiCreateReport(title, clientName, reportMonth);

    // 2. Excel 업로드
    btn.textContent = 'Excel 분석 중...';
    const uploadResult = await apiUploadExcel(
      report.id, selectedFile, followersStart, followersEnd, sheetName, kpiSheetName
    );
    showToast(`${uploadResult.row_count}행 업로드 완료`, 'success');

    const unmapped = uploadResult.mapping_info?.unmapped || [];
    if (unmapped.length > 0) {
      document.getElementById('unmapped-cols').textContent =
        `인식 불가 컬럼: ${unmapped.join(', ')}`;
      document.getElementById('mapping-warning').style.display = 'block';
      await new Promise(r => setTimeout(r, 1500));
    }

    // 3. 보고서 생성 시작
    btn.textContent = '보고서 생성 중...';
    await apiStartPipeline(report.id, true);
    showToast('보고서 생성 중... 잠시 후 확인하세요', 'info');

    // 4. 편집 페이지로 이동
    window.location.href = `/report/${report.id}`;

  } catch (err) {
    showToast(err.message, 'error');
    btn.disabled = false;
    btn.textContent = '보고서 생성 시작 →';
  }
});
