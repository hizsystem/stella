"""
Mock 응답 데이터 — MOCK_AGENTS=true 일 때 Claude API 호출 대신 사용
입력 raw_excel 데이터를 실제로 읽어 맥락 있는 응답을 반환.
데이터가 부족하면 현실적인 NDG 스타일 기본값으로 보완.
"""

from __future__ import annotations
import random


# ── 진입점 ─────────────────────────────────────────────────────────

def build_mock_response(data_type: str, input_data: dict) -> dict:
    if data_type == "agent_a_output":
        return _mock_agent_a(input_data)
    if data_type == "agent_b_output":
        return _mock_agent_b(input_data)
    if data_type == "agent_c_output":
        return _mock_agent_c(input_data)
    if data_type == "agent_d_output":
        return _mock_agent_d(input_data)
    if data_type == "agent_e_output":
        return _mock_agent_e(input_data)
    return {"agent": "unknown", "mock": True}


# ── 공통 헬퍼 ──────────────────────────────────────────────────────

def _pct(current: float, previous: float) -> float:
    if not previous:
        return 0.0
    return round((current - previous) / previous * 100, 2)


def _fmt_month(month: str) -> str:
    try:
        y, m = month.split("-")
        return f"{y}년 {int(m)}월"
    except Exception:
        return month


def _ct_label(ct: str) -> str:
    return {"feed": "피드", "story": "스토리", "reel": "릴스"}.get(ct, ct)


# ── 기본값 보완 헬퍼 ───────────────────────────────────────────────

# 제목이 없을 때 날짜+유형으로 자연스러운 제목 생성
_FEED_TITLES = [
    "브랜드 스토리", "신제품 소개", "라이프스타일 컷",
    "비하인드 컷", "제품 상세 컷", "캠페인 피드",
]
_REEL_TITLES = [
    "브랜드 릴스", "제품 사용법", "숏폼 영상",
    "하이라이트 영상", "언박싱 영상",
]
_STORY_TITLES = [
    "스토리 공지", "이벤트 알림", "일상 스토리",
    "제품 소개 스토리", "브랜드 스토리",
]

def _make_title(post: dict, idx: int) -> str:
    t = post.get("title", "")
    if t:
        return t
    ct = post.get("content_type", "feed")
    pool = {"feed": _FEED_TITLES, "reel": _REEL_TITLES, "story": _STORY_TITLES}.get(ct, _FEED_TITLES)
    return pool[idx % len(pool)]


def _make_display_date(upload_date: str) -> str:
    """'2026-03-15' → '3/15'"""
    try:
        parts = upload_date.split("-")
        return f"{int(parts[1])}/{int(parts[2])}"
    except Exception:
        return upload_date


# ── 데이터가 없을 때 쓰는 현실적인 기본 게시물 세트 ─────────────────

def _default_posts(report_month: str) -> list:
    """업로드 데이터가 없을 때 쓰는 NDG 스타일 샘플 게시물"""
    y, m = (report_month + "-02").split("-")[:2]
    m_int = int(m)
    y_int = int(y)

    def d(day): return f"{y_int}-{m_int:02d}-{day:02d}"

    return [
        {"upload_date": d(6),  "title": "브랜드 위클리 피드",          "content_type": "feed",  "content_subtype": "organic",  "content_placement": "피드", "likes": 98,   "comments": 12, "saves": 21,  "shares": 0, "reposts": 0, "total_interactions": 131,  "impressions": 2840, "reach": 2310, "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(11), "title": "[EVENT] 신제품 런칭 피드",      "content_type": "feed",  "content_subtype": "event",    "content_placement": "피드", "likes": 939,  "comments": 48, "saves": 328, "shares": 0, "reposts": 0, "total_interactions": 1315, "impressions": 12255,"reach": 9840, "profile_visits": 0, "new_followers": 567, "ad_spend": 200000, "is_boosted": True},
        {"upload_date": d(11), "title": "[EVENT] 신제품 런칭 스토리",    "content_type": "story", "content_subtype": "event",    "content_placement": "스토리","likes": 16,   "comments": 0,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 16,   "impressions": 842,  "reach": 790,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(13), "title": "라이프스타일 릴스",              "content_type": "reel",  "content_subtype": "organic",  "content_placement": "릴스", "likes": 54,   "comments": 8,  "saves": 12,  "shares": 0, "reposts": 0, "total_interactions": 74,   "impressions": 3880, "reach": 3210, "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(13), "title": "라이프스타일 스토리",            "content_type": "story", "content_subtype": "organic",  "content_placement": "스토리","likes": 9,    "comments": 0,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 9,    "impressions": 441,  "reach": 420,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(18), "title": "이벤트 안내 스토리",             "content_type": "story", "content_subtype": "event",    "content_placement": "스토리","likes": 11,   "comments": 2,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 13,   "impressions": 954,  "reach": 890,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(20), "title": "체크리스트 피드·릴스",           "content_type": "reel",  "content_subtype": "organic",  "content_placement": "릴스", "likes": 46,   "comments": 5,  "saves": 14,  "shares": 0, "reposts": 0, "total_interactions": 65,   "impressions": 3200, "reach": 2650, "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(20), "title": "체크리스트 스토리",              "content_type": "story", "content_subtype": "organic",  "content_placement": "스토리","likes": 8,    "comments": 0,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 8,    "impressions": 485,  "reach": 460,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(24), "title": "위클리 하이라이트 릴스",         "content_type": "reel",  "content_subtype": "organic",  "content_placement": "릴스", "likes": 51,   "comments": 7,  "saves": 18,  "shares": 0, "reposts": 0, "total_interactions": 76,   "impressions": 4100, "reach": 3560, "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(24), "title": "위클리 하이라이트 스토리",       "content_type": "story", "content_subtype": "organic",  "content_placement": "스토리","likes": 1,    "comments": 0,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 1,    "impressions": 628,  "reach": 600,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(25), "title": "[EVENT] 당첨자 발표 스토리",     "content_type": "story", "content_subtype": "event",    "content_placement": "스토리","likes": 3,    "comments": 1,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 4,    "impressions": 609,  "reach": 580,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(27), "title": "제품 상세 피드",                  "content_type": "feed",  "content_subtype": "organic",  "content_placement": "피드", "likes": 37,   "comments": 5,  "saves": 18,  "shares": 0, "reposts": 0, "total_interactions": 60,   "impressions": 3374, "reach": 2840, "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
        {"upload_date": d(27), "title": "제품 상세 스토리",                "content_type": "story", "content_subtype": "organic",  "content_placement": "스토리","likes": 5,    "comments": 0,  "saves": 0,   "shares": 0, "reposts": 0, "total_interactions": 5,    "impressions": 443,  "reach": 420,  "profile_visits": 0, "new_followers": 0,   "ad_spend": 0,      "is_boosted": False},
    ]


def _default_summary(posts: list, followers_start: int = 41278, followers_end: int = 41845) -> dict:
    return {
        "followers_start":     followers_start,
        "followers_end":       followers_end,
        "total_likes":         sum(p.get("likes", 0) for p in posts),
        "total_comments":      sum(p.get("comments", 0) for p in posts),
        "total_saves":         sum(p.get("saves", 0) for p in posts),
        "total_interactions":  sum(p.get("total_interactions", 0) for p in posts),
        "total_impressions":   sum(p.get("impressions", 0) for p in posts),
        "total_reach":         sum(p.get("reach", 0) for p in posts),
        "total_profile_visits": 0,
        "total_new_followers": followers_end - followers_start,
        "total_ad_spend":      sum(p.get("ad_spend", 0) for p in posts),
    }


def _ensure_data(raw_data: dict, report_month: str) -> tuple[list, dict]:
    """raw_excel에서 posts와 summary 추출. 없으면 기본값 사용."""
    cur = raw_data.get("current_month", {})
    posts = cur.get("posts", [])
    summary = cur.get("summary", {})

    if not posts:
        posts = _default_posts(report_month)
        summary = _default_summary(posts)
    else:
        # followers 값이 0이면 합리적인 기본값 보완
        if not summary.get("followers_end"):
            total_inter = sum(p.get("total_interactions", 0) for p in posts)
            summary["followers_start"] = summary.get("followers_start", 41000)
            summary["followers_end"] = summary.get("followers_start", 41000) + max(50, total_inter // 40)
        if not summary.get("total_interactions"):
            summary["total_interactions"] = sum(p.get("total_interactions", 0) for p in posts)
        if not summary.get("total_impressions"):
            summary["total_impressions"] = sum(p.get("impressions", 0) for p in posts)
        if not summary.get("total_ad_spend"):
            summary["total_ad_spend"] = sum(p.get("ad_spend", 0) for p in posts)

    return posts, summary


# ── top3 추출 ─────────────────────────────────────────────────────

def _top3_posts(posts: list, followers_end: int) -> list:
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
        er = round(inter / base * 100, 2)
        title = _make_title(p, i)
        ct = _ct_label(p.get("content_type", "feed"))
        result.append({
            "rank": i + 1,
            "upload_date": p.get("upload_date", ""),
            "content_type": p.get("content_type", "feed"),
            "content_subtype": p.get("content_subtype", "organic"),
            "title": title,
            "total_interactions": inter,
            "reach": p.get("reach", 0),
            "engagement_rate": er,
            "standout_reason": reason_pool[i % len(reason_pool)],
        })
    return result


# ── 콘텐츠 유형별 집계 ─────────────────────────────────────────────

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
        cnt  = bd[ct]["count"]
        inter = bd[ct]["total_interactions"]
        bd[ct]["avg_engagement_rate"] = round(inter / cnt / base * 100, 2) if cnt else 0
    return bd


# ── 광고 집계 ────────────────────────────────────────────────────

def _ad_breakdown(posts: list, raw_ad: dict) -> dict:
    if raw_ad:
        # 이미 집계된 값 있으면 cpv/cpc 계산만 보완
        bd = dict(raw_ad)
        for ct in ("story", "reel"):
            b = bd.get(ct, {})
            if b.get("spend") and b.get("impressions") and not b.get("cpv"):
                b["cpv"] = round(b["spend"] / b["impressions"])
        f = bd.get("feed", {})
        if f.get("spend") and f.get("interactions") and not f.get("cpc"):
            f["cpc"] = round(f["spend"] / f["interactions"])
        return bd

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
        if b["views"]:
            b["cpv"] = round(b["spend"] / b["views"]) if b["spend"] else 0
    f = bd["feed"]
    if f["interactions"]:
        f["cpc"] = round(f["spend"] / f["interactions"]) if f["spend"] else 0
    return bd


# ── 캘린더 마커 ──────────────────────────────────────────────────

def _calendar_entries(posts: list) -> list:
    seen = set()
    result = []
    for p in posts:
        date = p.get("upload_date", "")
        ct   = p.get("content_type", "feed")
        cal_type = "story" if ct == "story" else "feed_reel"
        key  = f"{date}_{cal_type}"
        if key not in seen:
            result.append({"date": date, "type": cal_type, "title": _make_title(p, 0)})
            seen.add(key)
    return result


# ── 콘텐츠 테이블 (슬라이드4) ────────────────────────────────────

def _content_table(posts: list) -> list:
    rows = []
    for i, p in enumerate(posts):
        ct = p.get("content_type", "feed")
        content_format = p.get("content_format", "") or _ct_label(ct)
        rows.append({
            "no":             i + 1,
            "date":           _make_display_date(p.get("upload_date", "")),
            "title":          _make_title(p, i),
            "type":           content_format,
            "content_type":   ct,
            "placement":      p.get("content_placement", "") or _ct_label(ct),
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


# ── 전월 대비 문장 생성 ──────────────────────────────────────────

def _direction(delta: float) -> str:
    return "up" if delta >= 0 else "down"


def _narrative(value: float, metric: str, direction: str) -> str:
    abs_v = abs(value)
    word = "증가" if direction == "up" else "감소"
    if abs_v < 1:
        return f"{metric} 전월 대비 유사 수준 유지"
    return f"전월 대비 {metric} {abs_v:.1f}% {word} 달성"


# ════════════════════════════════════════════════════════════════
# Agent A — 데이터 분석
# ════════════════════════════════════════════════════════════════

def _mock_agent_a(raw_data: dict) -> dict:
    meta         = raw_data.get("meta", {})
    report_month = meta.get("report_month", "2026-02")
    client       = meta.get("client", "HIZ-NDG")

    posts, summary = _ensure_data(raw_data, report_month)

    followers_end   = summary.get("followers_end",   41845)
    followers_start = summary.get("followers_start", 41278)
    total_inter     = summary.get("total_interactions", 0)
    total_imp       = summary.get("total_impressions",  0)
    total_ad        = summary.get("total_ad_spend",     0)

    # 전월 기본값 (약 8~15% 낮은 수준으로 추정)
    prev = raw_data.get("previous_month") or {}
    prev_s = prev.get("current_month", {}).get("summary", {}) if isinstance(prev, dict) else {}
    prev_followers = prev_s.get("followers_end",      int(followers_end  * 0.987))
    prev_inter     = prev_s.get("total_interactions", int(total_inter    * 0.874))
    prev_imp       = prev_s.get("total_impressions",  int(total_imp      * 0.901))
    prev_ad        = prev_s.get("total_ad_spend",     int(total_ad       * 0.923))

    breakdown = _type_breakdown(posts, followers_end)
    top3      = _top3_posts(posts, followers_end)
    ad_bd     = _ad_breakdown(posts, raw_data.get("ad_breakdown", {}))

    f_delta   = followers_end - prev_followers
    i_delta   = total_inter  - prev_inter

    highlight = _narrative(abs(_pct(total_inter, prev_inter)) if i_delta >= 0 else -abs(_pct(total_inter, prev_inter)),
                           "인터랙션", _direction(i_delta))
    caution   = "릴스 광고 CPV 추세 지속 모니터링 필요" if ad_bd.get("reel", {}).get("cpv", 0) > 10 else \
                "스토리 저장 수 추세 확인 권장"

    return {
        "agent": "data_analysis",
        "report_month": report_month,
        "client": client,
        "kpi_summary": {
            "followers":  {"current": followers_end,  "previous": prev_followers, "delta": f_delta,              "delta_pct": _pct(followers_end,  prev_followers)},
            "engagement": {"current": total_inter,    "previous": prev_inter,     "delta": total_inter - prev_inter, "delta_pct": _pct(total_inter, prev_inter)},
            "impressions":{"current": total_imp,      "previous": prev_imp,       "delta": total_imp  - prev_imp,   "delta_pct": _pct(total_imp,  prev_imp)},
            "ad_spend":   {"current": total_ad,       "previous": prev_ad,        "delta": total_ad   - prev_ad,    "delta_pct": _pct(total_ad,   prev_ad)},
        },
        "top_content": top3,
        "anomalies": _detect_anomalies(posts, total_inter),
        "content_type_breakdown": breakdown,
        "ad_breakdown": ad_bd,
        "mom_narrative_flags": {
            "highlight": highlight,
            "caution":   caution,
            "watch":     f"팔로워 순증 {f_delta:+,}명 — 목표 대비 추이 점검",
        },
    }


def _detect_anomalies(posts: list, total_inter: int) -> list:
    if not posts or not total_inter:
        return []
    avg = total_inter / len(posts)
    result = []
    for p in posts:
        v = p.get("total_interactions", 0)
        if v > avg * 3:
            result.append({
                "type": "spike", "metric": "engagement",
                "date": p.get("upload_date", ""),
                "value": v, "baseline": round(avg),
                "significance": "high",
                "note": f"{_make_title(p, 0)} — 평균 대비 {round(v/avg)}배 인터랙션",
            })
    return result[:2]


# ════════════════════════════════════════════════════════════════
# Agent B — 문장 생성
# ════════════════════════════════════════════════════════════════

def _mock_agent_b(b_input: dict) -> dict:
    analysis     = b_input.get("analysis", {})
    report_month = b_input.get("report_month", analysis.get("report_month", "2026-02"))
    client       = b_input.get("client", analysis.get("client", "HIZ-NDG"))
    fmt          = _fmt_month(report_month)

    kpi       = analysis.get("kpi_summary", {})
    followers = kpi.get("followers",  {})
    engagement= kpi.get("engagement", {})
    ad_spend  = kpi.get("ad_spend",   {})
    breakdown = analysis.get("content_type_breakdown", {})
    top3      = analysis.get("top_content", [])
    flags     = analysis.get("mom_narrative_flags", {})
    ad_bd     = analysis.get("ad_breakdown", {})

    feed_cnt  = breakdown.get("feed",  {}).get("count", 0)
    story_cnt = breakdown.get("story", {}).get("count", 0)
    reel_cnt  = breakdown.get("reel",  {}).get("count", 0)
    total_cnt = feed_cnt + story_cnt + reel_cnt

    f_delta    = followers.get("delta", 0)
    i_current  = engagement.get("current", 0)
    i_delta_p  = engagement.get("delta_pct", 0)
    i_dir      = "증가" if i_delta_p >= 0 else "감소"

    # 유형별 인터랙션 비율
    total_bd = sum(breakdown.get(ct, {}).get("total_interactions", 0) for ct in ["feed", "story", "reel"]) or 1
    feed_pct  = round(breakdown.get("feed",  {}).get("total_interactions", 0) / total_bd * 100)
    story_pct = round(breakdown.get("story", {}).get("total_interactions", 0) / total_bd * 100)
    reel_pct  = round(breakdown.get("reel",  {}).get("total_interactions", 0) / total_bd * 100)

    # 광고 성과 요약
    story_ad = ad_bd.get("story", {})
    reel_ad  = ad_bd.get("reel",  {})
    perf_summary = (
        f"스토리 광고 노출 {story_ad.get('impressions',0):,}회, CPV {story_ad.get('cpv',0)}원 유지"
        if story_ad.get("impressions") else f"총 광고비 {ad_spend.get('current',0):,}원 집행"
    )

    # top 콘텐츠 설명
    def top_desc(p: dict) -> str:
        if not p:
            return ""
        title = p.get("title", _make_title(p, 0))
        inter = p.get("total_interactions", 0)
        er    = p.get("engagement_rate", 0)
        ct    = _ct_label(p.get("content_type", "feed"))
        return f"{title} — {ct} 인터랙션 {inter:,}, 참여율 {er:.2f}% 달성"

    return {
        "agent": "sentence_generation",
        "report_month": report_month,
        "slides": {
            "slide_01_title": {
                "main_title": "NDG 소셜 미디어 운영 보고서",
                "sub_title":  fmt,
                "client_name": client,
                "prepared_by": "소셜 미디어 운영팀",
            },
            "slide_02_calendar": {
                "section_title": "월간 콘텐츠 캘린더",
                "summary":       f"총 {total_cnt}개 콘텐츠 운영 (피드 {feed_cnt}, 스토리 {story_cnt}, 릴스 {reel_cnt})",
                "highlight_note": flags.get("highlight", ""),
            },
            "slide_03_kpi": {
                "section_title": "KPI 성과 현황",
                "table_caption": f"{fmt} 주요 지표",
                "mom_note":      f"전월 대비 인터랙션 {abs(i_delta_p):.1f}% {i_dir}",
                "summary_sentence": f"팔로워 {f_delta:+,}명 변화 — 인터랙션 {i_current:,} 기록",
            },
            "slide_04_engagement": {
                "section_title": "인게이지먼트 분석",
                "top_content_intro": "이달의 주요 콘텐츠 성과",
                "mom_comparison_title": "전월 대비 지표 변화",
                "summary_sentence": f"총 {total_cnt}건 콘텐츠 발행 — 인터랙션 {i_current:,} 기록",
                "engagement_breakdown": f"피드 {feed_pct}%, 릴스 {reel_pct}%, 스토리 {story_pct}% 비중",
            },
            "slide_05_popular": {
                "section_title":     "인기 콘텐츠 분석",
                "rank1_label":       "이달의 1위 콘텐츠",
                "rank1_description": top_desc(top3[0]) if top3 else "",
                "rank2_label":       "이달의 2위 콘텐츠",
                "rank2_description": top_desc(top3[1]) if len(top3) > 1 else "",
                "rank3_label":       "이달의 3위 콘텐츠",
                "rank3_description": top_desc(top3[2]) if len(top3) > 2 else "",
                "insight_line":      "이벤트·정보형 콘텐츠 조합으로 참여율 상위 집중",
            },
            "slide_06_story": {
                "section_title":     "광고 성과",
                "performance_summary": perf_summary,
                "efficiency_note":   "광고비 대비 노출 효율 안정적 유지 확인",
                "caution_note":      flags.get("caution", ""),
            },
            "slide_07_review": {"section_title": "오퍼레이션 리뷰"},
            "slide_08_closing": {
                "closing_statement": "다음 달 운영 방향 및 개선 사항은 별도 전략 보고서에서 제공 예정",
                "prepared_by":       "NDG 소셜 미디어 운영팀",
            },
        },
    }


# ════════════════════════════════════════════════════════════════
# Agent C — 인사이트 생성
# ════════════════════════════════════════════════════════════════

def _mock_agent_c(c_input: dict) -> dict:
    analysis     = c_input.get("analysis", {})
    report_month = c_input.get("report_month", analysis.get("report_month", "2026-02"))
    kpi          = analysis.get("kpi_summary", {})
    flags        = analysis.get("mom_narrative_flags", {})
    ad_bd        = analysis.get("ad_breakdown", {})

    eng_pct  = kpi.get("engagement", {}).get("delta_pct", 0)
    eng_dir  = "증가" if eng_pct >= 0 else "감소"
    story_cpv = ad_bd.get("story", {}).get("cpv", 0)
    reel_cpv  = ad_bd.get("reel",  {}).get("cpv", 0)

    return {
        "agent": "insight_generation",
        "report_month": report_month,
        "insights": [
            {
                "number": 1, "category": "성과",
                "headline": flags.get("highlight", f"인터랙션 {abs(eng_pct):.1f}% {eng_dir}"),
                "full_sentence": f"콘텐츠 운영 최적화를 통한 인터랙션 {abs(eng_pct):.1f}% {eng_dir} 달성",
                "supporting_data": kpi.get("engagement", {}),
                "confidence": "high",
            },
            {
                "number": 2, "category": "효율",
                "headline": "이벤트 외 오가닉 참여 구조 점검",
                "full_sentence": "이벤트 콘텐츠 중심의 인터랙션 집중 구조로, 이벤트 외 일반 콘텐츠의 참여 기여도는 제한적 ⟶ 취향 선택·상황 공감 중심의 가벼운 참여 포맷을 병행해 상시 인게이지먼트 구조로의 전환 설계 필요",
                "supporting_data": {},
                "confidence": "high",
            },
            {
                "number": 3, "category": "개선",
                "headline": flags.get("caution", "채널별 광고 효율 점검"),
                "full_sentence": f"릴스 CPV {reel_cpv}원 수준 — 소재 다양화 및 타겟 재설정 검토 필요" if reel_cpv
                                 else "채널별 CPV 추세 지속 모니터링 및 소재 최적화 검토 필요",
                "supporting_data": ad_bd.get("reel", {}),
                "confidence": "medium",
            },
        ],
    }


# ════════════════════════════════════════════════════════════════
# Agent D — 검토/교정 (pass-through)
# ════════════════════════════════════════════════════════════════

def _mock_agent_d(d_input: dict) -> dict:
    return {
        "agent": "review_correction",
        "reviewed_slides":   d_input.get("slides_text", {}),
        "reviewed_insights": d_input.get("insights", []),
        "change_log": [],
        "quality_score": 90,
        "issues_found": 0,
    }


# ════════════════════════════════════════════════════════════════
# Agent E — 최종 구조 조립
# ════════════════════════════════════════════════════════════════

def _mock_agent_e(e_input: dict) -> dict:
    raw_data      = e_input.get("raw_data", {})
    analysis      = e_input.get("analysis", {})
    reviewed_text = e_input.get("reviewed_text", {})
    insights      = e_input.get("reviewed_insights", [])
    report_id     = str(e_input.get("report_id", "1"))
    report_month  = e_input.get("report_month", analysis.get("report_month", "2026-02"))
    client        = e_input.get("client", analysis.get("client", "HIZ-NDG"))
    fmt           = _fmt_month(report_month)

    # Slide 1/8용 report_date 포맷: "2026-02" → "2026. 02."
    try:
        _y, _m = report_month.split("-")[:2]
        report_date_fmt = f"{_y}. {int(_m):02d}."
    except Exception:
        report_date_fmt = report_month

    posts, summary = _ensure_data(raw_data, report_month)

    kpi           = analysis.get("kpi_summary", {})
    top3          = analysis.get("top_content", [])
    breakdown     = analysis.get("content_type_breakdown", {})
    ad_bd         = analysis.get("ad_breakdown", {})

    followers_end   = summary.get("followers_end",   kpi.get("followers", {}).get("current", 41845))
    followers_start = summary.get("followers_start", kpi.get("followers", {}).get("previous", 41278))
    total_inter     = summary.get("total_interactions", kpi.get("engagement", {}).get("current", 0))
    total_imp       = summary.get("total_impressions",  kpi.get("impressions", {}).get("current", 0))
    total_ad        = summary.get("total_ad_spend",     kpi.get("ad_spend",    {}).get("current", 0))

    f_delta   = kpi.get("followers",  {}).get("delta", followers_end - followers_start)
    i_delta   = kpi.get("engagement", {}).get("delta", 0)
    imp_delta = kpi.get("impressions",{}).get("delta", 0)
    ad_delta  = kpi.get("ad_spend",   {}).get("delta", 0)
    i_delta_p = kpi.get("engagement", {}).get("delta_pct", 0)

    # 유형 카운트
    feed_cnt  = breakdown.get("feed",  {}).get("count", sum(1 for p in posts if p.get("content_type") == "feed"))
    story_cnt = breakdown.get("story", {}).get("count", sum(1 for p in posts if p.get("content_type") == "story"))
    reel_cnt  = breakdown.get("reel",  {}).get("count", sum(1 for p in posts if p.get("content_type") == "reel"))

    # 전월 대비 (MoM)
    def safe_pct_delta(delta, current):
        prev = current - delta
        return round(delta / prev * 100, 1) if prev > 0 else 0.0

    mom_comparison = [
        {"metric": "인터랙션", "current": total_inter,    "previous": total_inter  - i_delta,
         "delta_pct": safe_pct_delta(i_delta, total_inter),   "direction": _direction(i_delta)},
        {"metric": "노출수",   "current": total_imp,      "previous": total_imp    - imp_delta,
         "delta_pct": safe_pct_delta(imp_delta, total_imp),   "direction": _direction(imp_delta)},
        {"metric": "팔로워",   "current": followers_end,  "previous": followers_start,
         "delta_pct": round(_pct(followers_end, followers_start), 2), "direction": _direction(f_delta)},
    ]

    # 유형별 비중
    total_bd = sum(breakdown.get(ct, {}).get("total_interactions", 0) for ct in ["feed","story","reel"]) or total_inter or 1
    content_breakdown = [
        {"type": "피드",   "interactions": breakdown.get("feed",  {}).get("total_interactions", 0),
         "pct": round(breakdown.get("feed",  {}).get("total_interactions", 0) / total_bd * 100)},
        {"type": "스토리", "interactions": breakdown.get("story", {}).get("total_interactions", 0),
         "pct": round(breakdown.get("story", {}).get("total_interactions", 0) / total_bd * 100)},
        {"type": "릴스",   "interactions": breakdown.get("reel",  {}).get("total_interactions", 0),
         "pct": round(breakdown.get("reel",  {}).get("total_interactions", 0) / total_bd * 100)},
    ]

    # 광고 지표 테이블
    ad_metrics = []
    label_map = {"feed": "피드 광고", "story": "스토리 광고", "reel": "릴스 광고"}
    for ct in ["feed", "story", "reel"]:
        v = ad_bd.get(ct, {})
        if v.get("spend") or v.get("impressions"):
            item = {"type": label_map[ct], "spend": v.get("spend", 0), "impressions": v.get("impressions", 0)}
            item["cpc" if ct == "feed" else "cpv"] = v.get("cpc" if ct == "feed" else "cpv", 0)
            ad_metrics.append(item)

    # 도달/평균 인터랙션 계산
    total_reach = summary.get("total_reach", sum(p.get("reach", 0) for p in posts))
    avg_inter   = round(total_inter / len(posts)) if posts else 0
    prev_reach  = round(total_reach * 0.9)   # 이전 데이터 없을 때 추정

    # top_posts 슬라이드용 포맷
    top_posts_slide = []
    for p in top3[:3]:
        top_posts_slide.append({
            "rank":             p.get("rank", 1),
            "date":             _make_display_date(p.get("upload_date", "")),
            "type":             _ct_label(p.get("content_type", "feed")),
            "interactions":     p.get("total_interactions", 0),
            "reach":            p.get("reach", 0),
            "engagement_rate":  p.get("engagement_rate", 0),
            "description":      f"{p.get('title', _make_title(p,0))} — 인터랙션 {p.get('total_interactions',0):,}, 참여율 {p.get('engagement_rate',0):.2f}% 달성",
        })

    # monthly_trend (전월 이력 포함 시)
    month_label   = f"{int(report_month.split('-')[1])}월"
    prev_trend    = analysis.get("previous_kpi_trend", [])
    # 현재 월 중복 방지
    monthly_trend = [t for t in prev_trend if t.get("label") != month_label]
    monthly_trend.append({
        "label":            month_label,
        "followers":        followers_end,
        "interactions":     total_inter,
        "avg_interactions": avg_inter,
        "reach":            total_reach,
        "ad_spend":         total_ad,
    })

    # 인사이트 기본값
    if not insights:
        i_dir = "증가" if i_delta >= 0 else "감소"
        insights = [
            {"number": 1, "category": "성과", "headline": f"인터랙션 {abs(i_delta_p):.1f}% {i_dir}",
             "full_sentence": f"월간 총 인터랙션 {total_inter:,} 기록 — 전월 대비 {abs(i_delta_p):.1f}% {i_dir} 달성"},
            {"number": 2, "category": "효율", "headline": "이벤트 외 오가닉 참여 구조 점검",
             "full_sentence": "이벤트 콘텐츠 중심의 인터랙션 집중 구조로, 이벤트 외 일반 콘텐츠의 참여 기여도는 제한적 ⟶ 취향 선택·상황 공감 중심의 가벼운 참여 포맷을 병행해 상시 인게이지먼트 구조로의 전환 설계 필요"},
            {"number": 3, "category": "개선", "headline": "채널 최적화 필요",
             "full_sentence": "채널별 CPV 편차 지속 모니터링 및 소재 최적화 검토 필요"},
        ]

    def _rt(key, fallback=""):
        return reviewed_text.get(key, {}) if reviewed_text else {}

    # 콘텐츠 테이블 사전 계산 (슬라이드 4, 5용)
    _all_table     = _content_table(posts)
    _fr_rows       = [{**r, "no": i + 1} for i, r in enumerate(r for r in _all_table if r.get("content_type") in ("feed", "reel"))]
    _story_rows    = [{**r, "no": i + 1} for i, r in enumerate(r for r in _all_table if r.get("content_type") == "story")]
    _fr_inter_sum  = sum(r["interactions"] for r in _fr_rows)
    _st_inter_sum  = sum(r["interactions"] for r in _story_rows)

    return {
        "agent": "structure_assembly",
        "report_id": report_id,
        "report_month": report_month,
        "client": client,
        "validation": {
            "all_slides_complete": True,
            "missing_fields": [],
            "warnings": ["monthly_trend 1개월만" ] if len(monthly_trend) <= 1 else [],
        },
        "slides": [
            {
                "slide_number": 1,
                "template": "title",
                "data": {
                    "main_title":  _rt("slide_01_title").get("main_title",  "NDG 소셜 미디어 운영 보고서"),
                    "sub_title":   _rt("slide_01_title").get("sub_title",   fmt),
                    "client_name": _rt("slide_01_title").get("client_name", client),
                    "prepared_by": _rt("slide_01_title").get("prepared_by", "소셜 미디어 운영팀"),
                    "report_date": report_date_fmt,
                },
            },
            {
                "slide_number": 2,
                "template": "calendar",
                "data": {
                    "section_title":    _rt("slide_02_calendar").get("section_title", "월간 콘텐츠 캘린더"),
                    "summary":          _rt("slide_02_calendar").get("summary",
                                           f"총 {feed_cnt+story_cnt+reel_cnt}개 콘텐츠 운영 (피드&릴스 {feed_cnt+reel_cnt}, 스토리 {story_cnt})"),
                    "feed_reel_count":  feed_cnt + reel_cnt,
                    "story_count":      story_cnt,
                    "report_month":     report_month,
                    "calendar_entries": _calendar_entries(posts),
                    "highlight_note":   _rt("slide_02_calendar").get("highlight_note", ""),
                },
            },
            {
                "slide_number": 3,
                "template": "kpi",
                "data": {
                    "section_title":  _rt("slide_03_kpi").get("section_title", "KPI 성과 현황"),
                    "table_caption":  _rt("slide_03_kpi").get("table_caption", f"{fmt} 주요 지표"),
                    "metrics": [
                        {"label": "총 팔로워",     "current": followers_end, "delta": f_delta,                        "delta_direction": _direction(f_delta)},
                        {"label": "총 인터랙션",   "current": total_inter,   "delta": i_delta,                        "delta_direction": _direction(i_delta)},
                        {"label": "평균 인터랙션", "current": avg_inter,     "delta": 0,                              "delta_direction": "up"},
                        {"label": "도달",          "current": total_reach,   "delta": total_reach - prev_reach,       "delta_direction": _direction(total_reach - prev_reach)},
                        {"label": "광고비",        "current": total_ad,      "delta": ad_delta,                       "delta_direction": _direction(ad_delta)},
                    ],
                    "monthly_trend":    monthly_trend,
                    "follower_target":  70000,
                    "report_month":     report_month,
                    "summary_sentence": _rt("slide_03_kpi").get("summary_sentence",
                        f"팔로워 {f_delta:+,}명 — 인터랙션 {total_inter:,} 달성"),
                },
            },
            {
                "slide_number": 4,
                "template": "engagement",
                "data": {
                    "section_title":    "피드&릴스 운영 현황",
                    "summary_sentence": _rt("slide_04_engagement").get("summary_sentence",
                        f"피드&릴스 {feed_cnt+reel_cnt}건 — 총 인터랙션 {_fr_inter_sum:,}"),
                    "content_table":    _fr_rows,
                    "mom_comparison":   mom_comparison,
                    "content_breakdown": content_breakdown,
                },
            },
            {
                "slide_number": 5,
                "template": "engagement",
                "data": {
                    "section_title":    "스토리 운영 현황",
                    "summary_sentence": f"스토리 {story_cnt}건 — 총 인터랙션 {_st_inter_sum:,}",
                    "content_table":    _story_rows,
                },
            },
            {
                "slide_number": 6,
                "template": "popular_content",
                "data": {
                    "section_title": _rt("slide_05_popular").get("section_title", "인기 콘텐츠 분석"),
                    "top_posts":     top_posts_slide,
                    "insight_line":  "",
                },
            },
            *([{
                "slide_number": 7,
                "template": "story_strategy",
                "data": {
                    "section_title":       _rt("slide_06_story").get("section_title", "광고 성과"),
                    "performance_summary": _rt("slide_06_story").get("performance_summary", ""),
                    "ad_metrics":          ad_metrics,
                    "efficiency_note":     _rt("slide_06_story").get("efficiency_note",
                        "광고비 대비 노출 효율 안정적 유지 확인"),
                    "caution_note":        _rt("slide_06_story").get("caution_note", ""),
                },
            }] if total_ad > 0 else []),
            {
                "slide_number": 8 if total_ad > 0 else 7,
                "template": "operating_review",
                "data": {
                    "section_title": _rt("slide_07_review").get("section_title", f"{month_label} 운영 리뷰"),
                    "insights":      insights,
                },
            },
            {
                "slide_number": 9 if total_ad > 0 else 8,
                "template": "closing",
                "data": {
                    "main_title":  "NDG 소셜 미디어 운영 보고서",
                    "sub_title":   fmt,
                    "client_name": client,
                    "prepared_by": _rt("slide_08_closing").get("prepared_by", "소셜 미디어 운영팀"),
                    "report_date": report_date_fmt,
                },
            },
        ],
    }


# ── 하위 호환 ─────────────────────────────────────────────────────
MOCK_BY_DATA_TYPE: dict = {}
