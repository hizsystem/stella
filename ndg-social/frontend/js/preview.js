/**
 * preview.js — 슬라이드 미리보기 페이지 (preview.html)
 */

let currentSlideNum = 1;
const TOTAL_SLIDES = 9;
const reportId = getReportIdFromUrl();
let reportStructure = null;

async function initPreview() {
  document.getElementById('btn-edit').href = `/report/${reportId}`;

  try {
    let data = await apiGetReportData(reportId, 'user_edited').catch(() => null);
    if (!data) data = await apiGetReportData(reportId, 'agent_e_output').catch(() => null);
    if (data) {
      reportStructure = data;
      renderFilmstrip();
      goToSlide(1);
    }
  } catch (e) {
    showToast('보고서 데이터를 불러올 수 없습니다', 'error');
  }
}

function goToSlide(num) {
  currentSlideNum = Math.max(1, Math.min(TOTAL_SLIDES, num));
  document.getElementById('slide-counter').textContent = `${currentSlideNum} / ${TOTAL_SLIDES}`;

  // 필름스트립 활성화
  document.querySelectorAll('.filmstrip-item').forEach((el, i) => {
    el.classList.toggle('active', i + 1 === currentSlideNum);
  });

  // 슬라이드 렌더링
  if (reportStructure) {
    const slide = (reportStructure.slides || []).find(s => s.slide_number === currentSlideNum);
    if (slide && typeof buildSlideHtml === 'function') {
      document.getElementById('slide-canvas').innerHTML = buildSlideHtml(slide);
    }
  }
  scalePreviewCanvas();
}

function scalePreviewCanvas() {
  const wrapper = document.getElementById('slide-wrapper');
  const canvas = document.getElementById('slide-canvas');
  if (!wrapper || !canvas) return;
  const scale = wrapper.offsetWidth / 1920;
  canvas.style.transform = `scale(${scale})`;
  wrapper.style.height = `${1080 * scale}px`;
}

function renderFilmstrip() {
  const strip = document.getElementById('filmstrip');
  if (!strip) return;
  const SLIDE_NAMES = ['Title', 'Calendar', 'KPI', '피드&릴스', 'Story', 'Popular', '광고성과', 'Review', 'Closing'];
  strip.innerHTML = Array.from({ length: TOTAL_SLIDES }, (_, i) => `
    <div class="filmstrip-item${i + 1 === currentSlideNum ? ' active' : ''}"
      onclick="goToSlide(${i + 1})"
      style="display:flex;align-items:center;justify-content:center;
        background:var(--color-brand-secondary);color:rgba(255,255,255,0.7);
        font-size:11px;flex-direction:column;gap:4px">
      <span style="font-weight:700">${i + 1}</span>
      <span>${SLIDE_NAMES[i]}</span>
    </div>`).join('');
}

function prevSlide() { goToSlide(currentSlideNum - 1); }
function nextSlide() { goToSlide(currentSlideNum + 1); }

// 키보드 단축키
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); nextSlide(); }
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp')  { e.preventDefault(); prevSlide(); }
  if (e.key === 'Escape') { window.location.href = `/report/${reportId}`; }
});

window.addEventListener('resize', scalePreviewCanvas);

initPreview();
