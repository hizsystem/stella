/**
 * export.js — PDF 내보내기
 */

async function exportPdf() {
  const btn = document.getElementById('btn-export');
  if (btn) { btn.disabled = true; btn.textContent = 'PDF 생성 중...'; }

  try {
    const blob = await apiExportPdf(reportId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `NDG_${reportId}_보고서.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('PDF 다운로드 완료', 'success');
  } catch (e) {
    showToast('PDF 생성 실패: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'PDF 내보내기'; }
  }
}

async function exportPptx() {
  const btn = document.getElementById('btn-export-pptx');
  if (btn) { btn.disabled = true; btn.textContent = 'PPT 생성 중...'; }

  try {
    const blob = await apiExportPptx(reportId);
    downloadBlob(blob, `NDG_${reportId}_보고서.pptx`);
    showToast('PPT 다운로드 완료', 'success');
  } catch (e) {
    showToast('PPT 생성 실패: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'PPT 내보내기'; }
  }
}

async function approveAndExport() {
  const btn = document.getElementById('btn-approve');
  if (btn) { btn.disabled = true; btn.textContent = '처리 중...'; }

  try {
    await apiApproveReport(reportId);
    showToast('승인 완료. PDF를 생성합니다...', 'success');
    await exportPdf();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '승인 & PDF 저장'; }
  }
}
