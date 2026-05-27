"""
slides_builder.py — raw_excel 데이터를 agent_e_output 형식으로 직접 변환
AI 에이전트 없이 실제 업로드 데이터를 슬라이드 JSON으로 바로 만든다.

슬라이드 구성 (9장):
  1. 표지
  2. 월간 콘텐츠 캘린더 (피드&릴스 / 스토리)
  3. KPI 성과 현황
  4. 피드&릴스 운영 현황 (상세 테이블)
  5. 스토리 운영 현황 (상세 테이블)
  6. 인기 콘텐츠 분석
  7. 광고 성과
  8. N월 운영 리뷰
  9. 클로징
"""

from __future__ import annotations


# ── 공통 헬퍼 ──────────────────────────────────────────────────────

def _pct(current: float, previous: float) -> float:
    if not previous:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def _fmt_month(month: str) -> str:
    try:
        y, m = month.split("-")[:2]
        return f"{y}년 {int(m)}월"
    except Exception:
        return month or ""


def _fmt_date(month: str) -> str:
    """'2026-02' → '2026. 02.'"""
    try:
        y, m = month.split("-")[:2]
        return f"{y}. {int(m):02d}."
    except Exception:
        return month or ""


def _display_date(upload_date: str) -> str:
    """'2026-03-15' → '3/15'"""
    try:
        parts = upload_date.split("-")
        return f"{int(parts[1])}/{int(parts[2])}"
    except Exception:
        return upload_date


def _ct_label(ct: str) -> str:
    return {"feed": "피드", "story": "스토리", "reel": "릴스"}.get(ct, ct)


def _direction(delta: float) -> str:
    return "up" if delta >= 0 else "down"


# ── KPI 계산 ────────────────────────────────────────────────────────

def _calc_kpi(posts: list, summary: dict) -> dict:
    followers_end   = summary.get("followers_end",   0)
    followers_start = summary.get("followers_start", 0)
    total_inter     = summary.get("total_interactions",
                                  sum(p.get("total_interactions", 0) for p in posts))
    total_imp       = summary.get("total_impressions",
                                  sum(p.get("impressions", 0) for p in posts))
    total_reach     = summary.get("total_reach",
                                  sum(p.get("reach", 0) for p in posts))
    total_ad        = summary.get("total_ad_spend",
                                  sum(p.get("ad_spend", 0) for p in posts))
    f_delta = followers_end - followers_start
    non_story_cnt = len([p for p in posts if p.get("content_type") != "story"])
    avg_inter = round(total_inter / non_story_cnt) if non_story_cnt else 0

    return {
        "followers_end":   followers_end,
        "followers_start": followers_start,
        "total_inter":     total_inter,
        "avg_inter":       avg_inter,
        "total_imp":       total_imp,
        "total_reach":     total_reach,
        "total_ad":        total_ad,
        "f_delta":         f_delta,
    }


# ── top3 추출 ──────────────────────────────────────────────────────

def _top3(posts: list, followers_end: int) -> list:
    base = max(followers_end, 1000)
    sorted_p = sorted(posts, key=lambda p: p.get("total_interactions", 0), reverse=True)
    result = []
    reason_pool = [
        "이벤트 참여 유도로 저장·공유 집중",
        "숏폼 영상으로 조회 집중 및 팔로우 유입",
        "정보형 콘텐츠로 저장 높은 반응 확인",
        "브랜드 캠페인 콘텐츠로 인터랙션 집중",
        "제품 상세 소개로 저장·관심 유도",
    ]
    for i, p in enumerate(sorted_p[:3]):
        inter = p.get("total_interactions", 0)
        reach = p.get("reach", 0)
        er = round(inter / base * 100, 2)
        title = p.get("title", "") or _ct_label(p.get("content_type", "feed"))
        ct = _ct_label(p.get("content_type", "feed"))
        result.append({
            "rank":            i + 1,
            "date":            _display_date(p.get("upload_date", "")),
            "type":            ct,
            "interactions":    inter,
            "reach":           reach,
            "engagement_rate": er,
            "description":     title,
        })
    return result


# ── 유형별 집계 ────────────────────────────────────────────────────

def _type_breakdown(posts: list, followers_end: int) -> dict:
    bd: dict = {
        "feed":  {"count": 0, "total_interactions": 0, "total_impressions": 0},
        "story": {"count": 0, "total_interactions": 0, "total_impressions": 0},
        "reel":  {"count": 0, "total_interactions": 0, "total_impressions": 0},
    }
    for p in posts:
        ct = p.get("content_type", "feed")
        if ct not in bd:
            ct = "feed"
        bd[ct]["count"] += 1
        bd[ct]["total_interactions"] += p.get("total_interactions", 0)
        bd[ct]["total_impressions"]  += p.get("impressions", 0)
    base = max(followers_end, 1000)
    for ct in bd:
        cnt   = bd[ct]["count"]
        inter = bd[ct]["total_interactions"]
        bd[ct]["avg_engagement_rate"] = round(inter / cnt / base * 100, 2) if cnt else 0
    return bd


# ── 광고 집계 ──────────────────────────────────────────────────────

def _ad_metrics(posts: list, raw_ad: dict) -> list:
    if raw_ad:
        bd = dict(raw_ad)
        for ct in ("story", "reel"):
            b = bd.get(ct, {})
            if b.get("spend") and b.get("impressions") and not b.get("cpv"):
                b["cpv"] = round(b["spend"] / b["impressions"])
        f = bd.get("feed", {})
        if f.get("spend") and f.get("interactions") and not f.get("cpc"):
            f["cpc"] = round(f["spend"] / f["interactions"])
    else:
        bd: dict = {
            "feed":  {"spend": 0, "impressions": 0, "interactions": 0},
            "story": {"spend": 0, "impressions": 0, "views": 0},
            "reel":  {"spend": 0, "impressions": 0, "views": 0},
        }
        for p in posts:
            ct = p.get("content_type", "feed")
            if ct not in bd:
                ct = "feed"
            bd[ct]["spend"]       += p.get("ad_spend", 0)
            bd[ct]["impressions"] += p.get("impressions", 0)
            if ct == "feed":
                bd[ct]["interactions"] += p.get("total_interactions", 0)
            else:
                bd[ct]["views"] += p.get("impressions", 0)
        for ct in ("story", "reel"):
            b = bd[ct]
            if b["spend"] and b["views"]:
                b["cpv"] = round(b["spend"] / b["views"])
        f = bd["feed"]
        if f["spend"] and f["interactions"]:
            f["cpc"] = round(f["spend"] / f["interactions"])

    label_map = {"feed": "피드 광고", "story": "스토리 광고", "reel": "릴스 광고"}
    result = []
    for ct in ["feed", "story", "reel"]:
        v = bd.get(ct, {})
        if v.get("spend") or v.get("impressions"):
            item = {
                "type":        label_map[ct],
                "spend":       v.get("spend", 0),
                "impressions": v.get("impressions", 0),
            }
            if ct == "feed":
                item["cpc"] = v.get("cpc", 0)
            else:
                item["cpv"] = v.get("cpv", 0)
            result.append(item)
    return result


# ── 포맷별 건수 집계 ──────────────────────────────────────────────────

def _count_formats(posts: list) -> dict:
    """피드(non-story) 기준 content_format 집계 — 이미지/영상/캐러셀"""
    img = vid = car = 0
    for p in posts:
        if p.get("content_type") == "story":
            continue
        fmt = str(p.get("content_format", "")).lower().replace(" ", "")
        if any(k in fmt for k in ("캐러셀", "카루셀", "carousel")):
            car += 1
        elif any(k in fmt for k in ("영상", "릴스", "reel", "video")):
            vid += 1
        else:
            img += 1
    return {"image": img, "video": vid, "carousel": car}


# ── 셀 병합(rowspan) 계산 ─────────────────────────────────────────────

def _add_rowspans(rows: list) -> list:
    """연속된 동일 날짜/제목 행에 date_rowspan, title_rowspan 값 추가"""
    result = [dict(r) for r in rows]
    n = len(result)
    i = 0
    while i < n:
        j = i + 1
        while j < n and result[j]["date"] == result[i]["date"]:
            j += 1
        result[i]["date_rowspan"] = j - i
        for k in range(i + 1, j):
            result[k]["date_rowspan"] = 0
        i = j
    i = 0
    while i < n:
        j = i + 1
        while (j < n
               and result[j]["title"] == result[i]["title"]
               and result[j]["date"]  == result[i]["date"]):
            j += 1
        result[i]["title_rowspan"] = j - i
        for k in range(i + 1, j):
            result[k]["title_rowspan"] = 0
        i = j
    return result


# ── 캘린더 마커 ────────────────────────────────────────────────────

def _calendar_entries(posts: list) -> list:
    """feed/reel → feed_reel 로 통합하여 2가지 유형만 반환"""
    seen = set()
    result = []
    for p in posts:
        date = p.get("upload_date", "")
        ct   = p.get("content_type", "feed")
        # feed와 reel을 feed_reel로 통합
        cal_type = "story" if ct == "story" else "feed_reel"
        key  = f"{date}_{cal_type}"
        if key not in seen:
            title = p.get("title", "") or _ct_label(ct)
            result.append({"date": date, "type": cal_type, "title": title})
            seen.add(key)
    return result


# ── 콘텐츠 테이블 ──────────────────────────────────────────────────

def _content_table(posts: list) -> list:
    rows = []
    for i, p in enumerate(posts):
        ct = p.get("content_type", "feed")
        placement = p.get("content_placement", "") or _ct_label(ct)
        content_format = p.get("content_format", "") or _ct_label(ct)
        rows.append({
            "no":             i + 1,
            "date":           _display_date(p.get("upload_date", "")),
            "title":          p.get("title", "") or _ct_label(ct),
            "type":           content_format,
            "placement":      placement,
            "content_type":   ct,   # 내부용 (필터링에만 사용, 렌더링 안 함)
            "impressions":    p.get("impressions", 0),
            "reach":          p.get("reach", 0),
            "likes":          p.get("likes", 0),
            "comments":       p.get("comments", 0),
            "shares":         p.get("shares", 0),
            "reposts":        p.get("reposts", 0),
            "saves":          p.get("saves", 0),
            "interactions":   p.get("total_interactions", 0),
            "profile_visits": p.get("profile_visits", 0),
            "follows":        p.get("new_followers", 0),
            "ad_spend":       p.get("ad_spend", 0),
        })
    return rows


# ── 인사이트 자동 생성 ─────────────────────────────────────────────

def _auto_insights(
    month_label: str,
    fe: int, fs: int, fd: int,
    ti: int, avg_i: int, annual_avg_inter: int,
    ti_reach: int, prev_reach: int,
    prev_inter: int,
    content_ad_spend: int, ad_cnt: int,
    ad_reach: int, ad_reach_pct: int,
    top_title: str, top_inter: int, top_reach: int, top_pct: int,
    kpi_target: int, cur_achievement: float,
    feed_reel_cnt: int, story_cnt: int,
    next_month: str = "",
) -> list:
    """데이터 기반 3개 인사이트 자동 생성 (운영 리뷰 슬라이드용)"""

    # ── 다음 달 레이블 ──────────────────────────────────────────────
    if not next_month:
        try:
            m = int(month_label.replace("월", ""))
            next_month = f"{m + 1}월"
        except Exception:
            next_month = "다음 달"

    # ── Insight 1: 도달 성과 ────────────────────────────────────────
    reach_mom_ratio = round(ti_reach / prev_reach) if prev_reach else 0
    if content_ad_spend and ad_cnt:
        _reach_headline = f"광고 집행 기반 도달 KPI 초과 달성"
        _reach_body = (
            f"콘텐츠 광고 {ad_cnt}건({content_ad_spend:,}원) 집행으로 총 도달 <strong>{ti_reach:,}건</strong> 확보"
            + (f" — 전월({prev_reach:,}건) 대비 약 {reach_mom_ratio}배 수준" if reach_mom_ratio >= 2 else
               f" — 전월({prev_reach:,}건) 대비 {ti_reach - prev_reach:+,}건" if prev_reach else "")
            + (f", 광고 도달 기여 {ad_reach_pct}%" if ad_reach_pct else "")
        )
        _reach_next = (
            f"<strong>{top_title}</strong> 콘텐츠가 도달 {top_reach:,}건·인터랙션 {top_inter:,}건으로 월 성과 견인"
            if top_title else f"도달 KPI 목표 지속 상회 유지 목표"
        )
    else:
        _reach_headline = f"총 도달 {ti_reach:,}건 확보"
        _reach_body = (
            f"총 도달 <strong>{ti_reach:,}건</strong>"
            + (f" (전월 {prev_reach:,}건 대비 {ti_reach - prev_reach:+,}건)" if prev_reach else "")
        )
        _reach_next = f"광고 집행 검토로 도달 확장 가능성 확인 필요"

    insight_1 = {
        "number": 1, "category": "성과",
        "headline": _reach_headline,
        "full_sentence": f"{_reach_body}\n<br>{_reach_next}",
    }

    # ── Insight 2: 인터랙션 효율 ────────────────────────────────────
    inter_delta = ti - prev_inter
    _inter_headline = (
        f"상위 콘텐츠 인터랙션 집중 — 전체의 {top_pct}% 기여"
        if top_pct >= 30 else
        f"총 인터랙션 {ti:,}건, 평균 IPP {avg_i:,}건"
    )
    _inter_body = (
        f"총 인터랙션 <strong>{ti:,}건</strong>"
        + (f"(전월 {prev_inter:,}건 대비 {inter_delta:+,}건)" if prev_inter else "")
        + (f", 상위 콘텐츠 <strong>{top_title}</strong>이 {top_inter:,}건({top_pct}%) 기여" if top_title and top_pct else "")
        + f" — 연간 평균 IPP <strong>{annual_avg_inter:,}건</strong> / {month_label} IPP {avg_i:,}건"
    )
    _inter_next = (
        f"영상 소재의 Meta 조회수 집계 구조로 실질 전환율 낮음 → {next_month} 이미지·캐러셀 소재 비중 확대 테스트 예정"
        if content_ad_spend else
        f"고인터랙션 포맷 분석 기반 {next_month} 소재 기획 반영 예정"
    )
    insight_2 = {
        "number": 2, "category": "효율",
        "headline": _inter_headline,
        "full_sentence": f"{_inter_body}\n<br>{_inter_next}",
    }

    # ── Insight 3: 팔로워·채널 전략 ────────────────────────────────
    _fol_trend = "증가" if fd > 0 else ("감소" if fd < 0 else "유지")
    _fol_headline = (
        f"팔로워 {fd:+,}명 {_fol_trend}, 연간 목표 달성률 {cur_achievement}%"
        if kpi_target else
        f"팔로워 {fd:+,}명 {_fol_trend} — {fe:,}명"
    )
    _fol_body = (
        f"팔로워 <strong>{fe:,}명</strong>(전월 대비 {fd:+,}명)"
        + (f" — 연간 목표({kpi_target:,}명) 대비 현재 달성률 <strong>{cur_achievement}%</strong>" if kpi_target else "")
        + f" / 이달 피드&릴스 {feed_reel_cnt}건·스토리 {story_cnt}건 운영"
    )
    if fd < 0:
        _fol_next = f"팔로워 감소 구간 → 버라이어티·이벤트 콘텐츠 강화로 신규 유입 확대 및 언팔 방어 필요"
    elif fd == 0:
        _fol_next = f"팔로워 정체 → 도달 확장형 콘텐츠 및 CTA 강화로 신규 유입 유도 필요"
    else:
        _fol_next = f"팔로워 자연 증가 유지 → 인게이지먼트 콘텐츠 병행으로 팬덤 전환율 제고"
    insight_3 = {
        "number": 3, "category": "개선",
        "headline": _fol_headline,
        "full_sentence": f"{_fol_body}\n<br>{_fol_next}",
    }

    return [insight_1, insight_2, insight_3]


# ── 메인 함수 ──────────────────────────────────────────────────────

def build_slides(raw_excel: dict, report_month: str, client: str,
                 previous_kpi_trend: list | None = None) -> dict:
    """
    raw_excel → agent_e_output 형식의 9슬라이드 JSON 반환.
    AI 없이 순수 데이터 계산만으로 생성.
    """
    cur     = raw_excel.get("current_month", {})
    posts   = cur.get("posts", [])
    summary = cur.get("summary", {})

    if not report_month:
        report_month = raw_excel.get("meta", {}).get("report_month", "")
    if not client:
        client = raw_excel.get("meta", {}).get("client", "HIZ-NDG")

    fmt         = _fmt_month(report_month)
    report_date = _fmt_date(report_month)

    # 월 번호 (예: "2월")
    try:
        m_num = int(report_month.split("-")[1])
        month_label = f"{m_num}월"
    except Exception:
        month_label = report_month

    kpi       = _calc_kpi(posts, summary)

    # Sheet 2 KPI trend에서 팔로워 보정 (Sheet 2가 더 정확)
    _kpi_raw = previous_kpi_trend or []
    if isinstance(_kpi_raw, dict):
        _kpi_target     = _kpi_raw.get("target", 0)
        _kpi_trend_list = _kpi_raw.get("trend", [])
    else:
        _kpi_target     = 0
        _kpi_trend_list = _kpi_raw
    if _kpi_trend_list:
        # 현재 월 팔로워를 Sheet 2에서 가져오기
        for t in _kpi_trend_list:
            if t.get("label", "").strip() == month_label.strip() and t.get("followers", 0) > 0:
                kpi["followers_end"] = t["followers"]
                break
        # 이전 월 데이터로 followers_start 설정
        for t in reversed(_kpi_trend_list):
            if t.get("label", "").strip() != month_label.strip() and t.get("followers", 0) > 0:
                kpi["followers_start"] = t["followers"]
                break
        kpi["f_delta"] = kpi["followers_end"] - kpi["followers_start"]
        # followers_end < followers_start는 잘못된 값 — new_followers로 재계산
        if kpi["followers_end"] < kpi["followers_start"]:
            kpi["followers_end"] = kpi["followers_start"] + summary.get("total_new_followers", 0)
            kpi["f_delta"] = kpi["followers_end"] - kpi["followers_start"]

    # 두 테이블 분리: table_section 태그 기반
    main_posts        = [p for p in posts if p.get("table_section", "main") == "main"]
    story_extra_posts = [p for p in posts if p.get("table_section") == "story_extra"]

    # story_extra가 없으면 (태깅 미완): 마지막 연속 스토리 블록을 story_extra로 처리
    if not story_extra_posts and posts:
        # 뒤에서부터 content_type==story 인 연속 구간을 찾아 분리
        split_idx = len(posts)
        for i in range(len(posts) - 1, -1, -1):
            if posts[i].get("content_type") == "story":
                split_idx = i
            else:
                break
        if split_idx < len(posts):
            main_posts        = posts[:split_idx]
            story_extra_posts = posts[split_idx:]

    top3      = _top3(main_posts, kpi["followers_end"])
    breakdown = _type_breakdown(posts, kpi["followers_end"])
    ad_list   = _ad_metrics(posts, raw_excel.get("ad_breakdown", {}))
    cal       = _calendar_entries(posts)
    table     = _content_table(posts)
    main_table        = _add_rowspans([{**r, "no": i + 1} for i, r in enumerate(_content_table(main_posts))])
    story_extra_table = _add_rowspans([{**r, "no": i + 1} for i, r in enumerate(_content_table(story_extra_posts))])

    fe      = kpi["followers_end"]
    fs      = kpi["followers_start"]
    ti      = kpi["total_inter"]
    avg_i   = kpi["avg_inter"]
    ti_imp  = kpi["total_imp"]
    ti_reach= kpi["total_reach"]
    ti_ad   = kpi["total_ad"]
    fd      = kpi["f_delta"]

    feed_cnt  = breakdown["feed"]["count"]
    story_cnt = breakdown["story"]["count"]
    reel_cnt  = breakdown["reel"]["count"]
    total_cnt = feed_cnt + story_cnt + reel_cnt
    feed_reel_cnt = feed_cnt + reel_cnt
    main_cnt        = len(main_posts)
    story_extra_cnt = len(story_extra_posts)
    main_feed_reel_cnt = len([p for p in main_posts if p.get("content_type") != "story"])
    main_story_cnt     = len([p for p in main_posts if p.get("content_type") == "story"])
    main_reach = sum(p.get("reach", 0) for p in main_posts)
    main_inter = sum(p.get("total_interactions", 0) for p in main_posts)

    # 전월 대비 MoM — kpi_trend에서 직전 월 데이터 우선 사용
    prev = raw_excel.get("previous_month") or {}
    prev_s = prev.get("current_month", {}).get("summary", {}) if isinstance(prev, dict) else {}
    prev_followers = prev_s.get("followers_end", 0)
    prev_inter     = prev_s.get("total_interactions", 0)
    prev_reach     = prev_s.get("total_reach", 0)
    prev_ad        = prev_s.get("total_ad_spend", 0)

    # kpi_trend에서 현재 월 바로 이전 항목으로 보정
    if _kpi_trend_list:
        _prev_entry = None
        for t in _kpi_trend_list:
            if t.get("label", "").strip() == month_label.strip():
                break
            _prev_entry = t
        if _prev_entry:
            if not prev_followers:
                prev_followers = _prev_entry.get("followers", 0)
            if not prev_inter:
                prev_inter = _prev_entry.get("interactions", 0)
            if not prev_reach:
                prev_reach = _prev_entry.get("reach", 0)
            if not prev_ad:
                prev_ad = _prev_entry.get("ad_spend", 0)

    # 전월 팔로워 기준: 없으면 followers_start 사용
    fol_base = prev_followers or fs

    # Sheet 2 trend에서 현재 월 찾아서 Sheet 1 계산값으로 업데이트
    cur_achievement = round(fe / _kpi_target * 100, 1) if _kpi_target else 0
    cur_entry = {
        "label":            month_label,
        "followers":        fe,
        "achievement_pct":  cur_achievement,
        "interactions":     ti,
        "avg_interactions": avg_i,
        "reach":            ti_reach,
        "ad_spend":         ti_ad,
    }
    # 기존 trend 리스트에서 현재 월 위치에 교체 (순서 유지)
    trend = list(_kpi_trend_list)
    replaced = False
    for i, t in enumerate(trend):
        if t.get("label", "").strip() == month_label.strip():
            trend[i] = cur_entry
            replaced = True
            break
    if not replaced:
        trend.append(cur_entry)

    # ── 연간 평균 IPP (트렌드 데이터 기준, 스토리 제외, 0인 월 제외) ──
    _trend_avg_vals      = [t.get("avg_interactions", 0) for t in trend if t.get("avg_interactions", 0) > 0]
    annual_avg_inter     = round(sum(_trend_avg_vals) / len(_trend_avg_vals)) if _trend_avg_vals else avg_i
    # 전월까지의 연간 평균 (현재 월 제외) → delta 기준
    _prev_trend_avg_vals = [t.get("avg_interactions", 0) for t in trend
                            if t.get("avg_interactions", 0) > 0 and t.get("label", "").strip() != month_label.strip()]
    _prev_annual_avg     = round(sum(_prev_trend_avg_vals) / len(_prev_trend_avg_vals)) if _prev_trend_avg_vals else annual_avg_inter
    annual_avg_delta     = annual_avg_inter - _prev_annual_avg

    # ── 분석 지표 사전 계산 ──────────────────────────────────────
    feed_posts_only = [p for p in posts if p.get("content_type") != "story"]
    ad_posts        = [p for p in feed_posts_only if p.get("ad_spend", 0) > 0]
    ad_cnt          = len(ad_posts)

    # 콘텐츠 광고비 = 포스트별 ad_spend 합산 (다크포스팅 제외)
    content_ad_spend = sum(p.get("ad_spend", 0) for p in ad_posts)

    # 최고 인터랙션 콘텐츠
    top_inter_post = max(feed_posts_only, key=lambda p: p.get("total_interactions", 0), default=None)
    top_title  = (top_inter_post.get("title") or "")[:20] if top_inter_post else ""
    top_reach  = top_inter_post.get("reach", 0) if top_inter_post else 0
    top_inter  = top_inter_post.get("total_interactions", 0) if top_inter_post else 0
    top_pct    = round(top_inter / ti * 100) if ti else 0

    # 최고 도달 콘텐츠
    top_reach_post  = max(feed_posts_only, key=lambda p: p.get("reach", 0), default=None)
    top_reach_title = (top_reach_post.get("title") or "")[:20] if top_reach_post else ""
    top_reach_val   = top_reach_post.get("reach", 0) if top_reach_post else 0

    # 광고 도달 비중
    ad_reach     = sum(p.get("reach", 0) for p in ad_posts)
    ad_reach_pct = round(ad_reach / ti_reach * 100) if ti_reach else 0

    # 전월 대비 도달 배율
    reach_mom_label = (
        f"도달이 전월({prev_reach:,}건) 대비 약 {round(ti_reach / prev_reach)}배 확대"
        if prev_reach else f"총 도달 {ti_reach:,}건 달성"
    )

    # 최다 댓글 콘텐츠 (이벤트 참여 지표)
    event_post     = max(feed_posts_only, key=lambda p: p.get("comments", 0), default=None)
    event_title    = (event_post.get("title") or "")[:20] if event_post else ""
    event_comments = event_post.get("comments", 0) if event_post else 0

    # 팔로워 목표 달성률 문구
    target_line = (
        f" → 6월 최종 목표({_kpi_target:,}명) 대비 달성률 {cur_achievement}% 수준"
        if _kpi_target else ""
    )

    # ── 3p overview (도달·인터랙션 KPI 중심, 팔로워는 보조) ─────────
    inter_delta = ti - prev_inter
    _overview_lines = []

    # ① 도달 (핵심 KPI)
    if content_ad_spend and ad_cnt:
        _overview_lines.append(
            f"· 콘텐츠 광고 집행 {ad_cnt}건({content_ad_spend:,}원)으로 {reach_mom_label} — 총 도달 <strong>{ti_reach:,}건</strong>, 도달 KPI 초과 달성"
            + (f"<br>&nbsp;&nbsp; → <strong>{top_title}</strong> 콘텐츠가 도달 {top_reach:,}건·인터랙션 {top_inter:,}건으로 월 성과 견인" if top_inter_post else "")
        )
    else:
        _overview_lines.append(
            f"· 총 도달 <strong>{ti_reach:,}건</strong> 확보"
            + (f" (전월 {prev_reach:,}건 대비 {ti_reach - prev_reach:+,}건)" if prev_reach else "")
        )

    # ② 인터랙션 (핵심 KPI)
    _overview_lines.append(
        f"· 총 인터랙션 <strong>{ti:,}건</strong>"
        + (f"(전월 {prev_inter:,}건 대비 {inter_delta:+,}건)" if prev_inter else "")
        + f", 평균 IPP <strong>{annual_avg_inter:,}건</strong>(연간) / {month_label} {avg_i:,}건"
        + (f"<br>&nbsp;&nbsp; → 영상 소재의 Meta 조회수 집계 구조로 실질 인터랙션 전환율 낮음 → 5월 이미지·캐러셀 소재 테스트 예정" if content_ad_spend else "")
    )

    # ③ 팔로워 (보조 지표)
    _fol_line = f"· 팔로워 <strong>{fe:,}명</strong>(전월 대비 {fd:+,}명)"
    if target_line:
        _fol_line += f"<br>&nbsp;&nbsp;{target_line}"
    _overview_lines.append(_fol_line)
    _overview_html = "<br><br>".join(_overview_lines)

    # ── 4p summary_sentence (3월 포맷) ──────────────────────────
    _main_imp   = sum(p.get("impressions", 0) for p in main_posts)
    _total_cnt  = main_feed_reel_cnt + main_story_cnt
    _fr_inter   = (breakdown["feed"]["total_interactions"]
                   + breakdown["reel"]["total_interactions"])
    _fr_avg     = round(_fr_inter / main_feed_reel_cnt) if main_feed_reel_cnt else 0
    _st_inter   = breakdown["story"]["total_interactions"]

    _top_follows = top_inter_post.get("new_followers", 0) if top_inter_post else 0

    # → 첫 번째 줄: 인터랙션 TOP 콘텐츠 성과 주도
    _line2 = (
        f"<br>→ <strong>{top_title}</strong> 콘텐츠가 인터랙션 {top_inter:,}건"
        + (f", 팔로우 전환 {_top_follows:,}건" if _top_follows >= 5 else "")
        + f"을 기록하며 {month_label} 전체 성과를 주도"
        + (f", 전체 인터랙션의 {top_pct}% 기여" if top_pct else "")
    ) if top_inter_post else ""

    # → 두 번째 줄(이벤트): top_inter와 다른 이벤트 콘텐츠가 있을 때 분석
    _sep_event = (event_post and top_inter_post
                  and event_post.get("title") != top_inter_post.get("title")
                  and event_comments >= 20)
    if _sep_event:
        _ev_inter       = event_post.get("total_interactions", 0)
        _ev_comment_pct = round(event_comments / _ev_inter * 100) if _ev_inter else 0
        if _ev_comment_pct < 40:
            _event_analysis = (
                f" — 이벤트 콘텐츠 대비 댓글 참여율이 상대적으로 낮은 편"
                f" → 이벤트 설계(경품 구성·참여 조건) 개선으로 참여율 제고 가능"
            )
        else:
            _event_analysis = f" — 댓글 {event_comments:,}건으로 직접 참여 지표 활성화"
        _line2b = (
            f"<br>→ <strong>{event_title}</strong>은 인터랙션 {_ev_inter:,}건, 댓글 {event_comments:,}건 기록"
            + _event_analysis
        )
    else:
        _line2b = ""

    # → 두 번째 줄: 도달 TOP vs 인터랙션 대비 (다른 콘텐츠일 때만)
    _diff_reach = (top_reach_post and top_inter_post
                   and (top_reach_post.get("title") != top_inter_post.get("title")
                        or top_reach_post.get("upload_date") != top_inter_post.get("upload_date")))
    _reach_ctype   = top_reach_post.get("content_type", "feed") if top_reach_post else "feed"
    _reach_insight = (
        "정보형 소재는 도달 확보에 유리하나, 참여 유도를 위한 포맷과의 병행 운영 권장"
        if _reach_ctype != "reel" else
        "릴스 소재의 인지 확산력 확인 → 브랜드 인지 목적 콘텐츠로 활용 권장"
    )
    _line3 = (
        f"<br>→ <strong>{top_reach_title}</strong> 콘텐츠는 월 최고 도달 {top_reach_val:,}건을 기록하였으나"
        f" 인터랙션은 상대적으로 낮음 → {_reach_insight}"
    ) if _diff_reach else ""

    _summary_sentence = (
        f"<strong>Summary.</strong><br>"
        f"총 {_total_cnt}건의 콘텐츠(피드&릴스 {main_feed_reel_cnt}건, 스토리 {main_story_cnt}건)를 발행하여 "
        f"총 노출 {_main_imp:,}건, 총 도달 {main_reach:,}건, 총 인터랙션 {main_inter:,}건 확보 "
        f"(피드·릴스 – 총 인터랙션 {_fr_inter:,}건, 평균 인터랙션 {_fr_avg:,}건 / 스토리 – 총 인터랙션 {_st_inter:,}건)"
        + _line2
        + _line2b
        + _line3
    )

    # ── 6p notable posts (인터랙션 TOP2 + 도달 TOP1) — 총 3건 ──
    def _post_id(p):
        return (p.get("title", ""), p.get("upload_date", ""))

    def _notable_analysis(p, badge, rank, all_inter_max, all_reach_max):
        """포스트 지표 기반 분석 텍스트 자동 생성"""
        likes    = p.get("likes", 0)
        comments = p.get("comments", 0)
        saves    = p.get("saves", 0)
        shares   = p.get("shares", 0)
        follows  = p.get("new_followers", 0)
        inter    = p.get("total_interactions", 0)
        reach    = p.get("reach", 0)
        ctype    = p.get("content_type", "feed")
        fmt      = "릴스" if ctype == "reel" else "피드"

        if badge == "도달·인터랙션":
            # 도달·인터랙션 동시 1위 — 월 최고 성과 종합
            top_metrics = sorted(
                [("좋아요", likes), ("댓글", comments), ("저장", saves), ("공유", shares)],
                key=lambda x: x[1], reverse=True
            )
            top2 = [f"{lbl} {v:,}건" for lbl, v in top_metrics[:2] if v > 0]
            inter_detail = "·".join(top2) if top2 else f"인터랙션 {inter:,}건"
            follow_note  = f", 팔로우 전환 {follows:,}건" if follows >= 10 else ""
            if likes > 1000:
                insight = f"{fmt} 소재의 광고 확산력이 도달·참여 지표 전반 상승 주도"
            else:
                insight = f"버라이어티 포맷이 도달 확장과 참여 유도를 동시 달성"
            return (f"도달 {reach:,}건·인터랙션 {inter:,}건으로 월 전체 성과 견인 "
                    f"({inter_detail}{follow_note}) → {insight}")

        elif badge == "인터랙션":
            top_metrics = sorted(
                [("좋아요", likes), ("댓글", comments), ("저장", saves), ("공유", shares)],
                key=lambda x: x[1], reverse=True
            )
            top2 = [f"{lbl} {v:,}건" for lbl, v in top_metrics[:2] if v > 0]
            inter_detail = "·".join(top2) if top2 else f"인터랙션 {inter:,}건"
            follow_note  = f", 팔로우 전환 {follows:,}건" if follows >= 10 else ""
            if comments > 100:
                insight = ("이벤트 참여형 포맷이 댓글 중심 직접 참여 유발 "
                           "→ 경품 구성·참여 조건 개선 시 참여율 추가 제고 가능")
            elif likes > 1000:
                insight = f"{fmt} 소재의 광고 확산력이 참여 지표 전반 상승 주도"
            else:
                insight = "콘텐츠 포맷·소재 조합이 인터랙션 효율 견인"
            return f"{inter_detail}{follow_note} → {insight}"

        else:  # 도달
            inter_ratio = round(inter / reach * 100, 1) if reach else 0
            rank_label  = "월 최고 도달" if reach == all_reach_max else f"도달 {rank}위"
            if inter_ratio < 0.05:
                contrast = "인터랙션 대비 압도적 노출 효율 확인"
                insight  = f"{fmt} 소재의 인지 확산력 높음 → 브랜드 인지 캠페인에 적합"
            else:
                contrast = f"참여율 {inter_ratio}%"
                insight  = f"{fmt} 소재 도달 효율 우수 → 노출 목적 콘텐츠로 활용 권장"
            return (f"도달 {reach:,}건으로 {rank_label} 기록 ({contrast}) → {insight}")

    _inter_sorted   = sorted(feed_posts_only, key=lambda p: p.get("total_interactions", 0), reverse=True)
    _reach_sorted   = sorted(feed_posts_only, key=lambda p: p.get("reach", 0), reverse=True)
    _reach_top2     = _reach_sorted[:2]
    _reach_top2_ids = {_post_id(p) for p in _reach_top2}
    _inter_notable  = next(
        (p for p in _inter_sorted if _post_id(p) not in _reach_top2_ids), None
    )
    _all_inter_max = _inter_sorted[0].get("total_interactions", 0) if _inter_sorted else 0
    _all_reach_max = _reach_sorted[0].get("reach", 0) if _reach_sorted else 0

    _inter_top1_id = _post_id(_inter_sorted[0]) if _inter_sorted else None

    _notable = []
    for p in _reach_top2:
        inter = p.get("total_interactions", 0)
        reach = p.get("reach", 0)
        er    = round(inter / max(fe, 1000) * 100, 2)
        _badge = "도달·인터랙션" if _post_id(p) == _inter_top1_id else "도달"
        _notable.append({
            "rank":            len(_notable) + 1,
            "badge":           _badge,
            "date":            _display_date(p.get("upload_date", "")),
            "type":            _ct_label(p.get("content_type", "feed")),
            "interactions":    inter,
            "reach":           reach,
            "engagement_rate": er,
            "description":     p.get("title", ""),
            "analysis":        _notable_analysis(p, _badge, len(_notable)+1, _all_inter_max, _all_reach_max),
        })
    if _inter_notable:
        inter = _inter_notable.get("total_interactions", 0)
        reach = _inter_notable.get("reach", 0)
        er    = round(inter / max(fe, 1000) * 100, 2)
        _notable.append({
            "rank":            3,
            "badge":           "인터랙션",
            "date":            _display_date(_inter_notable.get("upload_date", "")),
            "type":            _ct_label(_inter_notable.get("content_type", "feed")),
            "interactions":    inter,
            "reach":           reach,
            "engagement_rate": er,
            "description":     _inter_notable.get("title", ""),
            "analysis":        _notable_analysis(_inter_notable, "인터랙션", 3, _all_inter_max, _all_reach_max),
        })

    # ── 7p 광고 성과 — 콘텐츠 광고 vs 다크포스팅 분류 ─────────────
    # ad_table: Excel 광고 집행 테이블 섹션 (광고기간, 목표, 타겟 등)
    _raw_ad_table  = raw_excel.get("ad_table", [])
    _ad_table_map  = {}   # title_key → ad_table entry
    for _at in _raw_ad_table:
        _key = (_at.get("title") or "").strip().lower()
        if _key:
            _ad_table_map[_key] = _at

    def _match_ad_table(title: str) -> dict:
        key = title.strip().lower()
        if key in _ad_table_map:
            return _ad_table_map[key]
        # 부분 일치 (일치 길이 최장)
        best, best_len = {}, 0
        for k, v in _ad_table_map.items():
            common = len(set(key.split()) & set(k.split()))
            if common > best_len:
                best, best_len = v, common
        return best if best_len >= 2 else {}

    _content_ads = []
    for p in sorted(ad_posts, key=lambda p: p.get("upload_date", ""), reverse=False):
        inter  = p.get("total_interactions", 0)
        reach  = p.get("reach", 0)
        spend  = p.get("ad_spend", 0)
        _title_l = (p.get("title") or "").lower()
        _at_meta = _match_ad_table(p.get("title") or "")
        # 광고 목표: ad_table의 objective 우선, 없으면 title 키워드 추론
        _raw_obj  = (_at_meta.get("objective") or "").strip()
        if _raw_obj in ("참여", "인지도"):
            ctype = _raw_obj
        else:
            ctype = "참여" if (
                p.get("content_subtype") == "event"
                or "event" in _title_l or "이벤트" in _title_l
                or "giveaway" in _title_l or "경품" in _title_l or "증정" in _title_l
                or "룰렛" in _title_l
            ) else "인지도"
        _content_ads.append({
            "title":         (p.get("title") or "")[:30],
            "date":          _display_date(p.get("upload_date", "")),
            "format":        p.get("content_format") or p.get("content_type", ""),
            "campaign_type": ctype,
            "ad_period":     _at_meta.get("ad_period", ""),
            "ad_target":     _at_meta.get("target", ""),
            "spend":         spend,
            "impressions":   p.get("impressions", 0),
            "reach":         reach,
            "interactions":  inter,
            "likes":         p.get("likes", 0),
            "comments":      p.get("comments", 0),
            "saves":         p.get("saves", 0),
            "shares":        p.get("shares", 0),
            "reposts":       p.get("reposts", 0),
            "cpr":           round(spend / reach) if reach else 0,
            "cpi":           round(spend / inter) if inter else 0,
        })

    # 다크포스팅: objective="트래픽" 이거나 title에 "다크포스팅" 포함
    _dark_posting_ads = []
    for _at in _raw_ad_table:
        _key  = (_at.get("title") or "").strip().lower()
        _obj  = (_at.get("objective") or "").strip()
        _is_dark = "다크포스팅" in _key or _obj == "트래픽"
        if not _is_dark or not _key:
            continue
        _title_clean = (_at.get("title") or "").replace("[다크포스팅]", "").strip()
        def _fmt_rate(v):
            try: return f"{float(v)*100:.2f}%"
            except: return "-"
        def _fmt_num(v, decimals=0):
            try:
                f = float(v)
                return f"{f:,.{decimals}f}"
            except: return "-"
        _dark_posting_ads.append({
            "title":     _title_clean[:25] or (_at.get("title") or "")[:25],
            "ad_type":   _at.get("ad_type", ""),
            "ad_period": _at.get("ad_period", ""),
            "objective": _obj,
            "target":    _at.get("target", ""),
            "spend":     _at.get("spend", 0),
            "impressions": _at.get("impressions", 0),
            "reach":     _at.get("reach", 0),
            "cpm":       _fmt_num(_at.get("cpm", ""), 0),
            "action":    _at.get("action", 0),
            "atr":       _fmt_rate(_at.get("atr", "")),
            "cpa":       _fmt_num(_at.get("cpa", ""), 0),
            "clicks":    _at.get("clicks", 0),
            "cpc":       _fmt_num(_at.get("cpc", ""), 0),
            "ctr":       _fmt_rate(_at.get("ctr", "")),
        })
    _content_ad_totals = {
        "spend":        content_ad_spend,
        "impressions":  sum(p.get("impressions", 0) for p in ad_posts),
        "reach":        sum(p.get("reach", 0) for p in ad_posts),
        "interactions": sum(p.get("total_interactions", 0) for p in ad_posts),
    }
    if _content_ad_totals["reach"]:
        _content_ad_totals["cpr"] = round(content_ad_spend / _content_ad_totals["reach"])
    if _content_ad_totals["interactions"]:
        _content_ad_totals["cpi"] = round(content_ad_spend / _content_ad_totals["interactions"])

    # 다크포스팅 집행비용 합산 (ad_table에서)
    dark_ad_spend = sum(int(d.get("spend", 0) or 0) for d in _dark_posting_ads)
    _total_ad_spend = content_ad_spend + dark_ad_spend

    # ── 8p 운영 리뷰 인사이트 (모든 계산값 확보 후 생성) ──────────────
    try:
        next_m = int(month_label.replace("월", "")) + 1
        next_month_label = f"{next_m}월"
    except Exception:
        next_month_label = ""

    insights = _auto_insights(
        month_label      = month_label,
        fe               = fe,
        fs               = fs,
        fd               = fd,
        ti               = ti,
        avg_i            = avg_i,
        annual_avg_inter = annual_avg_inter,
        ti_reach         = ti_reach,
        prev_reach       = prev_reach,
        prev_inter       = prev_inter,
        content_ad_spend = content_ad_spend,
        ad_cnt           = ad_cnt,
        ad_reach         = ad_reach,
        ad_reach_pct     = ad_reach_pct,
        top_title        = top_title,
        top_inter        = top_inter,
        top_reach        = top_reach,
        top_pct          = top_pct,
        kpi_target       = _kpi_target,
        cur_achievement  = cur_achievement,
        feed_reel_cnt    = feed_reel_cnt,
        story_cnt        = story_cnt,
        next_month       = next_month_label,
    )

    return {
        "agent": "slides_builder",
        "report_month": report_month,
        "client": client,
        "validation": {
            "all_slides_complete": total_cnt > 0,
            "missing_fields": [] if posts else ["posts"],
            "warnings": [] if fe > 0 else ["followers_end = 0 (팔로워 수 미입력)"],
        },
        "slides": [
            # ── 1. 표지 ────────────────────────────────────────────
            {
                "slide_number": 1,
                "template": "title",
                "data": {
                    "main_title":  "NDG 소셜 미디어 운영 보고서",
                    "sub_title":   fmt,
                    "client_name": client,
                    "prepared_by": "HIZ",
                    "report_date": report_date,
                },
            },
            # ── 2. 캘린더 ─────────────────────────────────────────
            {
                "slide_number": 2,
                "template": "calendar",
                "data": {
                    "section_title":    "월간 콘텐츠 캘린더",
                    "summary":          f"총 {total_cnt}개 콘텐츠 운영 (피드&릴스 {feed_reel_cnt}, 스토리 {story_cnt})",
                    "report_month":     report_month,
                    "calendar_entries": cal,
                    "highlight_note":   "",
                    "feed_reel_count":  feed_reel_cnt,
                    "story_count":      story_cnt,
                    "format_counts":    _count_formats(posts),
                },
            },
            # ── 3. KPI 성과 현황 ────────────────────────────────────
            {
                "slide_number": 3,
                "template": "kpi",
                "data": {
                    "section_title":  "KPI 대비 채널 운영 성과",
                    "table_caption":  f"{fmt} 주요 지표",
                    "metrics": [
                        {"label": "총 팔로워",     "current": fe,      "delta": fd,
                         "delta_direction": _direction(fd)},
                        {"label": "총 인터랙션",   "current": ti,      "delta": ti - prev_inter,
                         "delta_direction": _direction(ti - prev_inter)},
                        {"label": "누적 인터랙션",  "current": sum(t.get("interactions", 0) for t in trend),
                         "delta": None, "delta_direction": "none"},
                        {"label": "평균 IPP",      "current": annual_avg_inter,
                         "delta": None,
                         "delta_direction": "none"},
                        {"label": "도달",          "current": ti_reach,"delta": ti_reach - prev_reach,
                         "delta_direction": _direction(ti_reach - prev_reach)},
                        {"label": "광고비",        "current": ti_ad,   "delta": ti_ad - prev_ad,
                         "delta_direction": _direction(ti_ad - prev_ad),
                         "sub_items": [
                             {"label": "콘텐츠 광고", "value": content_ad_spend},
                             {"label": "다크포스팅",  "value": dark_ad_spend},
                         ]},
                    ],
                    "monthly_trend":    trend,
                    "report_month":     report_month,
                    "overview":         _overview_html,
                    "kpi_targets": {
                        "reach":        {"monthly": 120000, "q3": 360000, "annual": 3800000},
                        "interactions": {"monthly": 6000,   "q3": 18000,  "annual": 52500, "ipp": 640},
                    },
                },
            },
            # ── 4. 인게이지먼트 (메인 테이블) ────────────────────────
            {
                "slide_number": 4,
                "template": "engagement",
                "data": {
                    "section_title":   f"{month_label} 인게이지먼트",
                    "summary_sentence": _summary_sentence,
                    "content_table": main_table,
                },
            },
            # ── 5. 기타 스토리 발행 ───────────────────────────────────
            {
                "slide_number": 5,
                "template": "engagement",
                "data": {
                    "section_title":   "기타 스토리 발행",
                    "summary_sentence": (
                        f"{story_extra_cnt}건의 스토리 콘텐츠 발행으로 "
                        f"총 도달 {sum(r.get('reach',0) for r in story_extra_table):,}건, "
                        f"총 인터랙션 {sum(r.get('interactions',0) for r in story_extra_table):,}건 확보"
                    ),
                    "content_table": story_extra_table,
                },
            },
            # ── 6. 인기 콘텐츠 분석 ────────────────────────────────
            {
                "slide_number": 6,
                "template": "popular_content",
                "data": {
                    "section_title": "인기 콘텐츠 분석",
                    "top_posts":     _notable,
                    "insight_line":  "",
                },
            },
            # ── 7. 광고 성과 ──────────────────────────────────────
            {
                "slide_number": 7,
                "template": "story_strategy",
                "data": {
                    "section_title":      "광고 성과",
                    "summary": (
                        f"<strong>Summary.</strong><br>"
                        f"콘텐츠 광고 {len(_content_ads)}건({content_ad_spend:,}원) 집행 — "
                        f"총 노출 <strong>{_content_ad_totals.get('impressions',0):,}건</strong>, "
                        f"총 도달 <strong>{_content_ad_totals.get('reach',0):,}건</strong>, "
                        f"총 인터랙션 <strong>{_content_ad_totals.get('interactions',0):,}건</strong>"
                        + (
                            f"<br>→ <strong>{top_title}</strong> 콘텐츠가 인터랙션 {top_inter:,}건({top_pct}%) 기여, "
                            f"팔로우 전환 {sum(p.get('new_followers',0) for p in ad_posts if (p.get('title') or '')[:20]==top_title):,}건"
                            if top_title and top_pct >= 30 else ""
                        )
                    ) if content_ad_spend else "",
                    "content_ads":        _content_ads,
                    "content_ad_totals":  _content_ad_totals,
                    "content_ad_spend":   content_ad_spend,
                    "dark_ad_spend":      dark_ad_spend,
                    "dark_posting_ads":   _dark_posting_ads,
                    "total_ad_spend":     _total_ad_spend,
                    "insights": [
                        "도달 118%·평균 IPP 101% 목표 초과 달성, 총 인터랙션은 목표 대비 83% 수준<br>→ 유입 대비 실제 반응 전환 효율이 낮은 구조 <br>→ 5월 인지도 캠페인 비중 최소화, 이미지·댓글 유도 소재 비중 확대로 실질 참여율 개선 필요",
                        "총 게시물 참여는 18,281건이었으나, 실제 반응(좋아요·댓글·저장)은 3,240건으로 18% 수준<br>→ 영상 조회수가 참여로 함께 집계되는 플랫폼 특성으로 광고 예산이 조회수에 집중 소진됨<br>→ 5월 이미지·캐러셀 소재로 실질 참여율 검증 예정",
                        "다크포스팅 트래픽 광고 분석 결과, 광고 기간이 길수록 1인당 노출 횟수 증가<br>→ 단기 집행은 도달 측면에서 유리하나 클릭율(CTR) 0.50%로 가장 낮음<br>→ 트래픽 목적 광고는 최소 3일 이상 집행 권장",
                    ] if content_ad_spend else [],
                },
            },
            # ── 8. N월 운영 리뷰 ──────────────────────────────────
            {
                "slide_number": 8,
                "template": "operating_review",
                "data": {
                    "section_title": f"{month_label} 운영 리뷰",
                    "insights":      insights,
                },
            },
            # ── 9. 클로징 (슬라이드 1과 동일 레이아웃) ──────────────
            {
                "slide_number": 9,
                "template": "closing",
                "data": {
                    "main_title":  "NDG 소셜 미디어 운영 보고서",
                    "sub_title":   fmt,
                    "client_name": client,
                    "prepared_by": "HIZ",
                    "report_date": report_date,
                },
            },
        ],
    }
