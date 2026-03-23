import os, streamlit as st, folium, pandas as pd, numpy as np
import plotly.express as px, plotly.graph_objects as go
from streamlit_folium import st_folium

st.set_page_config(page_title="MSF 고위험 지역 2026", page_icon="🆘", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans KR',sans-serif;background:#0a0e1a;color:#e8e8e8;}
.msf-header{background:linear-gradient(135deg,#1a0505,#1e1e2e 60%,#0d1a2e);border-left:6px solid #e63946;padding:28px 36px 22px;margin-bottom:24px;border-radius:0 10px 10px 0;box-shadow:0 4px 24px rgba(230,57,70,0.15);}
.msf-header h1{font-size:2.1rem;font-weight:700;color:#fff;margin:0 0 6px;letter-spacing:-0.5px;}
.msf-header p{color:#9a9ab0;font-size:0.82rem;font-family:'IBM Plex Mono',monospace;margin:0;}
.kpi-card{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;border-top:3px solid #e63946;border-radius:10px;padding:18px 20px;text-align:center;}
.kpi-label{color:#94a3b8;font-size:0.7rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.kpi-value{color:#e63946;font-size:1.9rem;font-weight:700;font-family:'IBM Plex Mono',monospace;line-height:1.1;}
.kpi-unit{color:#64748b;font-size:0.75rem;margin-top:4px;}
.detail-panel{background:linear-gradient(135deg,#16213e,#0f172a);border:1px solid #e63946;border-radius:12px;padding:24px;margin-top:10px;}
.detail-panel h2{font-size:1.4rem;font-weight:700;color:#fff;margin:0 0 4px;}
.crisis-type{font-size:0.75rem;color:#e63946;font-family:'IBM Plex Mono',monospace;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px;}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:14px;}
.stat-box{background:#0a0e1a;border-radius:8px;padding:12px;text-align:center;border:1px solid #1e293b;}
.stat-box .number{font-size:1.1rem;font-weight:700;color:#e63946;font-family:'IBM Plex Mono',monospace;}
.stat-box .label{font-size:0.66rem;color:#9a9ab0;margin-top:3px;}
.risk-factors{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}
.risk-tag-pill{background:#1e1e2e;border:1px solid #3a3a5a;border-radius:20px;padding:3px 11px;font-size:0.72rem;color:#c0c0d8;}
.source-note{font-size:0.68rem;color:#5a5a7a;font-family:'IBM Plex Mono',monospace;margin-top:12px;padding-top:10px;border-top:1px solid #1e293b;}
.notes-box{background:#0f172a;border-left:3px solid #334155;border-radius:0 6px 6px 0;padding:10px 14px;font-size:0.79rem;color:#94a3b8;line-height:1.6;margin-bottom:12px;font-style:italic;}
.legend-box{background:#16213e;border:1px solid #2a2a4a;border-radius:8px;padding:12px 16px;margin-bottom:14px;font-size:0.78rem;color:#9a9ab0;}
.legend-box span{color:#e63946;font-weight:700;}
.section-title{font-size:1rem;font-weight:700;color:#e2e8f0;border-left:4px solid #e63946;padding-left:10px;margin:20px 0 12px;}
.period-badge{display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:4px;padding:2px 8px;font-size:0.68rem;color:#64748b;font-family:'IBM Plex Mono',monospace;margin-bottom:12px;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1rem;}
</style>
""", unsafe_allow_html=True)

BASE = os.path.dirname(os.path.abspath(__file__))
SHORT = {"Sudan":"수단","Democratic Republic of the Congo":"DR콩고",
         "South Sudan":"남수단","Gaza Strip":"가자지구","Haiti":"아이티"}
RISK_LABEL = {"conflict":"분쟁·전쟁","displacement":"대규모 이동","flooding":"홍수",
    "wash_breakdown":"상하수도 붕괴","health_system_strain":"보건체계 붕괴",
    "food_insecurity":"식량 불안","overcrowding":"과밀","low_vaccination":"낮은 예방접종"}
COLORS = ["#e63946","#f4a261","#e9c46a","#2a9d8f","#457b9d"]
RED = "#e63946"
BG = "#0a0e1a"
PLOT_BG = "#16213e"

@st.cache_data
def load_csvs():
    c = pd.read_csv(os.path.join(BASE,"msf_dashboard_country_summary.csv"))
    e = pd.read_csv(os.path.join(BASE,"msf_dashboard_events.csv"))
    r = pd.read_csv(os.path.join(BASE,"msf_dashboard_risk_factors.csv"))
    for col in ["cases_reported","deaths_reported","injuries_reported",
                "fatality_rate_pct","risk_score","people_in_need","displaced_people"]:
        c[col] = pd.to_numeric(c[col], errors="coerce")
    for col in ["metric_cases","metric_deaths","metric_injuries"]:
        e[col] = pd.to_numeric(e[col], errors="coerce")
    e["start_date"] = pd.to_datetime(e["start_date"])
    e["end_date"]   = pd.to_datetime(e["end_date"])
    r["present"]    = pd.to_numeric(r["present"], errors="coerce").fillna(0)
    return c, e, r

country_df, events_df, risk_df = load_csvs()

COUNTRIES = {
    "Sudan":{"kr":"수단","lat":15.5,"lon":32.5,"crisis":"콜레라 대유행","icon":"💊",
      "stats":[{"number":"124,418명","label":"감염자"},{"number":"3,573명","label":"사망자"},{"number":"2.87%","label":"치명률"}],
      "risks":["상하수도 붕괴","대규모 이동","홍수","의료 접근 제한"],
      "desc":"2024년 8월 이후 전국 18개 주로 콜레라가 확산됐습니다. 내전으로 인한 인프라 붕괴·의료시스템 마비·홍수와 대규모 인구이동이 복합 작용, 2026년 3월 종식 선언.",
      "source":"WHO EMRO (2026-03-08)","period":"2024-07 ~ 2026-03"},
    "Democratic Republic of the Congo":{"kr":"DR콩고","lat":-4.0,"lon":21.8,"crisis":"다중 전염병 동시 발생","icon":"🦠",
      "stats":[{"number":"450,000+","label":"유행 건수"},{"number":"8,700+명","label":"사망자"},{"number":"5종+","label":"동시 질병"}],
      "risks":["콜레라","mpox","홍역","에볼라","폴리오"],
      "desc":"WHO 2026 긴급호소 대상국. 콜레라·mpox·홍역·에볼라·폴리오 5종 이상의 전염병이 동시 유행 중. 분쟁·극빈·보건 인프라 부재가 복합적으로 작용.",
      "source":"WHO / ReliefWeb (2026-02-01)","period":"2025~2026 Appeal"},
    "South Sudan":{"kr":"남수단","lat":6.9,"lon":31.3,"crisis":"사상 최대 콜레라 확산","icon":"🌊",
      "stats":[{"number":"96,000+건","label":"콜레라 케이스"},{"number":"~1,600명","label":"사망자"},{"number":"630만명","label":"지원 필요"}],
      "risks":["홍수","국경 유입","취약 보건체계","mpox 동시","간염 E"],
      "desc":"2025년 11월 말 기준 역대 최대 콜레라 유행. 홍수·국경유입·취약 보건체계가 주요 위험요인. 콜레라 외 간염 E·mpox 동시 유행, 630만 명이 의료지원 필요.",
      "source":"UNOCHA / WHO (2026-01-01)","period":"2025-11-30 기준"},
    "Gaza Strip":{"kr":"가자지구","lat":31.5,"lon":34.47,"crisis":"전쟁·기아·감염병 위험 중첩","icon":"⚔️",
      "stats":[{"number":"63,000+명","label":"사망자"},{"number":"161,000+명","label":"부상자"},{"number":"210만명","label":"지원 필요"}],
      "risks":["오염수","하수시설 파괴","극심 과밀","폐기물 축적","낮은 예방접종"],
      "desc":"군사 충돌로 의료 인프라 거의 전멸. 210만 명이 인도적 지원 필요, 140만 명이 긴급 주거 필요. 오염수·파괴된 하수시스템이 감염병 확산의 직접 위험요인.",
      "source":"WHO (2025-09-10)","period":"2025-09-10 기준"},
    "Haiti":{"kr":"아이티","lat":18.97,"lon":-72.3,"crisis":"치안붕괴 속 콜레라 재확산","icon":"🚨",
      "stats":[{"number":"4,864명","label":"갱단 폭력 사망"},{"number":"17명","label":"콜레라 사망"},{"number":"104만명","label":"실향민"}],
      "risks":["갱 폭력","성폭력","대규모 이동","병원 운영 중단","불안정 식수·위생"],
      "desc":"갱단 수도권 장악으로 치안 붕괴 가운데 2025년 페티옹빌에서 콜레라 재확산. 420만 명이 인도적 지원 필요, 104만 명이 실향민.",
      "source":"PAHO / OHCHR / WHO (2025-11-09)","period":"2024-10 ~ 2025-11"},
}

if "selected" not in st.session_state:
    st.session_state.selected = None

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="msf-header">
  <h1>🆘 MSF 활동 고위험 지역 2026</h1>
  <p>전염병 · 위험요소 · 사망 통계 인포그래픽 &nbsp;|&nbsp; 출처: WHO / PAHO / OHCHR / OCHA / ReliefWeb</p>
</div>
""", unsafe_allow_html=True)

# ── KPI 6개 ───────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
total_cases   = int(country_df['cases_reported'].sum())
total_deaths  = int(country_df['deaths_reported'].sum())
total_inj     = int(country_df['injuries_reported'].fillna(0).sum())
total_pin     = country_df['people_in_need'].fillna(0).sum()
total_disp    = country_df['displaced_people'].fillna(0).sum()
avg_risk      = round(country_df['risk_score'].mean(), 1)

pin_str  = f"{total_pin/1e6:.1f}M"
disp_str = f"{total_disp/1e6:.2f}M"

for col, label, value, unit in [
    (k1,"총 감염·케이스",  f"{total_cases:,}","건"),
    (k2,"총 사망자",       f"{total_deaths:,}","명"),
    (k3,"총 부상자",       f"{total_inj:,}","명"),
    (k4,"지원 필요 인구",  pin_str,"명"),
    (k5,"실향민",          disp_str,"명"),
    (k6,"평균 위험 점수",  str(avg_risk),"/ 10"),
]:
    col.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-unit">{unit}</div></div>',
        unsafe_allow_html=True)

st.markdown("")

# ── 탭 ───────────────────────────────────────────────────────────────────────
tab_map, tab_overview, tab_charts, tab_risk, tab_timeline, tab_data = st.tabs([
    "🗺️ 인터랙티브 지도", "📋 국가별 개요", "📊 통계 그래프",
    "⚠️ 위험요인 분석", "📅 타임라인", "📄 원시 데이터"])

# ════════════ TAB 1: 지도 ════════════════════════════════════════════════════
with tab_map:
    col_map, col_panel = st.columns([3, 2], gap="large")
    with col_map:
        st.markdown(
            '<div class="legend-box"><span>● 빨간 마커</span> = MSF 의료 개입 필요성이 큰 복합위기 지역'
            ' &nbsp;|&nbsp; 마커 클릭 또는 우측 버튼으로 상세 정보 확인</div>',
            unsafe_allow_html=True)
        m = folium.Map(location=[10, 20], zoom_start=2,
                       tiles="CartoDB dark_matter", prefer_canvas=True)
        for en, info in COUNTRIES.items():
            icon_html = (
                f'<div style="background:#e63946;border-radius:50%;width:38px;height:38px;'
                f'display:flex;align-items:center;justify-content:center;font-size:17px;'
                f'box-shadow:0 0 16px rgba(230,57,70,0.9);border:2px solid #fff;">'
                f'{info["icon"]}</div>')
            marker_icon = folium.DivIcon(html=icon_html, icon_size=(38,38), icon_anchor=(19,19))
            stat_rows = "".join(
                f'<span style="font-size:0.79rem;color:#ccc;">• {s["label"]}: '
                f'<b style="color:#e63946">{s["number"]}</b></span><br>'
                for s in info["stats"])
            popup_html = (
                f'<div style="font-family:sans-serif;background:#16213e;color:#fff;'
                f'padding:14px;border-radius:8px;min-width:210px;border:1px solid #e63946;">'
                f'<b style="font-size:1rem">{info["kr"]}</b><br>'
                f'<span style="color:#e63946;font-size:0.72rem;letter-spacing:1px">'
                f'{info["crisis"].upper()}</span><br><br>{stat_rows}'
                f'<span style="font-size:0.66rem;color:#5a5a7a">{info["period"]}</span></div>')
            popup = folium.Popup(
                folium.IFrame(popup_html, width=240, height=175), max_width=260)
            folium.Marker(
                location=[info["lat"], info["lon"]],
                popup=popup,
                tooltip=f"<b style='color:#e63946'>{info['kr']}</b> — {info['crisis']}",
                icon=marker_icon
            ).add_to(m)
            folium.CircleMarker(
                location=[info["lat"], info["lon"]],
                radius=24, color=RED, weight=1,
                fill=True, fill_color=RED, fill_opacity=0.07
            ).add_to(m)
        map_data = st_folium(m, width="100%", height=480,
                             returned_objects=["last_object_clicked_tooltip"])
        if map_data and map_data.get("last_object_clicked_tooltip"):
            tip = map_data["last_object_clicked_tooltip"]
            for en, info in COUNTRIES.items():
                if info["kr"] in tip:
                    st.session_state.selected = en
                    break

    with col_panel:
        st.markdown("### 🌍 국가 선택")
        for en, info in COUNTRIES.items():
            row = country_df[country_df["country"] == en]
            score = int(row["risk_score"].values[0]) if len(row) else 0
            if st.button(
                f'{info["icon"]}  {info["kr"]}  |  위험점수 {score}/10',
                key=f"btn_{en}", use_container_width=True):
                st.session_state.selected = en

        sel = st.session_state.selected
        if sel and sel in COUNTRIES:
            info = COUNTRIES[sel]
            row = country_df[country_df["country"] == sel]
            notes = row["notes"].values[0] if len(row) else ""
            st.markdown("---")
            stat_boxes = "".join(
                f'<div class="stat-box"><div class="number">{s["number"]}</div>'
                f'<div class="label">{s["label"]}</div></div>'
                for s in info["stats"])
            risk_pills = "".join(
                f'<span class="risk-tag-pill">{r}</span>' for r in info["risks"])
            st.markdown(
                f'<div class="detail-panel">'
                f'<h2>{info["icon"]} {info["kr"]}</h2>'
                f'<div class="crisis-type">⚠ {info["crisis"]}</div>'
                f'<div class="period-badge">📅 {info["period"]}</div>'
                f'<div class="stat-grid">{stat_boxes}</div>'
                f'<p style="font-size:0.84rem;color:#c0c0d8;line-height:1.7;margin-bottom:12px;">{info["desc"]}</p>'
                f'<div class="notes-box">💬 {notes}</div>'
                f'<div style="font-size:0.74rem;color:#9a9ab0;font-weight:600;margin-bottom:8px;">주요 위험요인</div>'
                f'<div class="risk-factors">{risk_pills}</div>'
                f'<div class="source-note">📎 {info["source"]}</div>'
                f'</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="background:#16213e;border:1px dashed #2a2a4a;border-radius:10px;'
                'padding:36px;text-align:center;color:#5a5a7a;margin-top:8px;line-height:2.2;">'
                '← 지도 마커 또는<br>위 버튼을 클릭하면<br>상세 정보가 표시됩니다</div>',
                unsafe_allow_html=True)

# ════════════ TAB 2: 국가별 개요 ═════════════════════════════════════════════
with tab_overview:
    st.markdown('<div class="section-title">국가별 위기 현황 카드</div>', unsafe_allow_html=True)
    ov_cols = st.columns(len(COUNTRIES))
    for i, (en, info) in enumerate(COUNTRIES.items()):
        row = country_df[country_df["country"] == en]
        score = int(row["risk_score"].values[0]) if len(row) else 0
        pin   = row["people_in_need"].values[0] if len(row) else np.nan
        disp  = row["displaced_people"].values[0] if len(row) else np.nan
        period = row["reporting_period"].values[0] if len(row) else ""
        pin_s  = f"{pin/1e6:.1f}M" if not np.isnan(pin) else "—"
        disp_s = f"{disp/1e6:.2f}M" if not np.isnan(disp) else "—"
        dots   = "🔴"*score + "⚪"*(10-score)
        with ov_cols[i]:
            st.markdown(
                f'<div style="background:linear-gradient(180deg,#16213e,#0a0e1a);'
                f'border:1px solid #2a2a4a;border-top:3px solid {COLORS[i]};'
                f'border-radius:10px;padding:16px;min-height:300px;">'
                f'<div style="font-size:1.6rem;margin-bottom:6px;">{info["icon"]}</div>'
                f'<div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:4px;">{info["kr"]}</div>'
                f'<div style="font-size:0.65rem;color:{COLORS[i]};letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;">{info["crisis"]}</div>'
                f'<div style="font-size:0.7rem;color:#9a9ab0;margin-bottom:3px;">위험점수</div>'
                f'<div style="font-size:0.72rem;margin-bottom:10px;">{dots}</div>'
                f'<div style="font-size:0.7rem;color:#9a9ab0;">지원 필요</div>'
                f'<div style="font-size:1rem;font-weight:700;color:#e2e8f0;font-family:IBM Plex Mono,monospace;">{pin_s}</div>'
                f'<div style="font-size:0.7rem;color:#9a9ab0;margin-top:8px;">실향민</div>'
                f'<div style="font-size:1rem;font-weight:700;color:#e2e8f0;font-family:IBM Plex Mono,monospace;">{disp_s}</div>'
                f'<div style="font-size:0.62rem;color:#5a5a7a;margin-top:10px;font-family:IBM Plex Mono,monospace;">{period}</div>'
                f'</div>',
                unsafe_allow_html=True)

    st.markdown('<div class="section-title">국가별 종합 위험점수 (10점 만점)</div>', unsafe_allow_html=True)
    df_score = country_df[["country","risk_score"]].dropna().copy()
    df_score["name_kr"] = df_score["country"].map(SHORT)
    df_score = df_score.sort_values("risk_score")
    bar_colors = [RED if s>=6 else "#f59e0b" if s>=4 else "#22c55e" for s in df_score["risk_score"]]
    fig_g = go.Figure()
    fig_g.add_trace(go.Bar(
        x=df_score["risk_score"], y=df_score["name_kr"], orientation="h",
        marker_color=bar_colors, text=df_score["risk_score"], textposition="outside",
        hovertemplate="%{y}: %{x}/10<extra></extra>"))
    fig_g.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        height=240, margin=dict(l=10,r=60,t=10,b=10),
        xaxis=dict(range=[0,11], gridcolor="#1e293b", title="위험점수"),
        yaxis=dict(gridcolor="#1e293b"))
    st.plotly_chart(fig_g, use_container_width=True)

# ════════════ TAB 3: 통계 그래프 ═════════════════════════════════════════════
with tab_charts:
    LO = dict(template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
              margin=dict(l=10,r=10,t=10,b=10), height=300,
              xaxis=dict(gridcolor="#1e293b"), yaxis=dict(gridcolor="#1e293b"))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">1️⃣ 국가별 사망자 수</div>', unsafe_allow_html=True)
        df_d = country_df[["country","deaths_reported"]].dropna().copy()
        df_d["name_kr"] = df_d["country"].map(SHORT)
        df_d = df_d.sort_values("deaths_reported")
        fig1 = px.bar(df_d, x="deaths_reported", y="name_kr", orientation="h",
            color="deaths_reported", color_continuous_scale="Reds",
            labels={"deaths_reported":"사망자 수","name_kr":"국가"})
        fig1.update_layout(**LO, coloraxis_showscale=False)
        fig1.update_traces(hovertemplate="%{y}<br>사망자: %{x:,}명<extra></extra>")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">2️⃣ 국가별 감염·케이스 수</div>', unsafe_allow_html=True)
        df_c = country_df[["country","cases_reported"]].dropna().copy()
        df_c["name_kr"] = df_c["country"].map(SHORT)
        df_c = df_c.sort_values("cases_reported")
        fig2 = px.bar(df_c, x="cases_reported", y="name_kr", orientation="h",
            color="cases_reported", color_continuous_scale="OrRd",
            labels={"cases_reported":"케이스 수","name_kr":"국가"})
        fig2.update_layout(**LO, coloraxis_showscale=False)
        fig2.update_traces(hovertemplate="%{y}<br>케이스: %{x:,}건<extra></extra>")
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="section-title">3️⃣ 치명률 비교 (%)</div>', unsafe_allow_html=True)
        df_f = country_df[["country","fatality_rate_pct"]].dropna().copy()
        df_f["name_kr"] = df_f["country"].map(SHORT)
        df_f = df_f.sort_values("fatality_rate_pct")
        fig3 = px.bar(df_f, x="fatality_rate_pct", y="name_kr", orientation="h",
            color="fatality_rate_pct", color_continuous_scale="YlOrRd",
            labels={"fatality_rate_pct":"치명률 (%)","name_kr":"국가"})
        fig3.update_layout(**LO, coloraxis_showscale=False)
        fig3.update_traces(hovertemplate="%{y}<br>치명률: %{x:.2f}%<extra></extra>")
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.markdown('<div class="section-title">4️⃣ 감염 vs 사망 (버블: 위험점수)</div>', unsafe_allow_html=True)
        df_s = country_df.dropna(subset=["cases_reported","deaths_reported","risk_score"]).copy()
        df_s["name_kr"] = df_s["country"].map(SHORT)
        fig4 = px.scatter(df_s, x="cases_reported", y="deaths_reported", size="risk_score",
            color="region_group", hover_name="name_kr",
            labels={"cases_reported":"감염·케이스","deaths_reported":"사망자","region_group":"지역"})
        fig4.update_layout(**LO, legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-title">5️⃣ 지원 필요 인구 & 실향민 규모</div>', unsafe_allow_html=True)
    df_h = country_df[["country","people_in_need","displaced_people"]].copy()
    df_h["name_kr"] = df_h["country"].map(SHORT)
    df_hm = df_h.melt(id_vars=["name_kr"], value_vars=["people_in_need","displaced_people"],
                      var_name="구분", value_name="인원")
    df_hm["구분"] = df_hm["구분"].map({"people_in_need":"지원 필요 인구","displaced_people":"실향민"})
    df_hm = df_hm.dropna()
    fig5 = px.bar(df_hm, x="name_kr", y="인원", color="구분", barmode="group",
        color_discrete_map={"지원 필요 인구":RED,"실향민":"#457b9d"},
        labels={"name_kr":"국가","인원":"인원 수 (명)"})
    fig5.update_layout(**LO, legend=dict(orientation="h", y=1.08))
    fig5.update_traces(hovertemplate="%{x}<br>%{y:,}명<extra></extra>")
    st.plotly_chart(fig5, use_container_width=True)

# ════════════ TAB 4: 위험요인 분석 ═══════════════════════════════════════════
with tab_risk:
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown('<div class="section-title">국가 × 위험요인 히트맵</div>', unsafe_allow_html=True)
        rdf2 = risk_df.copy()
        rdf2["risk_label"]  = rdf2["risk_factor"].map(lambda x: RISK_LABEL.get(x, x))
        rdf2["country_kr"]  = rdf2["country"].map(SHORT).fillna(rdf2["country"])
        hm = rdf2.pivot_table(index="risk_label", columns="country_kr",
                              values="present", aggfunc="max").fillna(0)
        hover_hm = [
            [f"{hm.index[r]} | {hm.columns[c]}<br>{'✓ 존재' if hm.values[r,c]==1 else '해당 없음'}"
             for c in range(len(hm.columns))]
            for r in range(len(hm.index))]
        fig_hm = go.Figure(data=go.Heatmap(
            z=hm.values, x=hm.columns.tolist(), y=hm.index.tolist(),
            colorscale=[[0,"#16213e"],[0.5,"#7f1d1d"],[1,"#e63946"]],
            showscale=False,
            text=[["✓" if v==1 else "" for v in row] for row in hm.values],
            texttemplate="%{text}", textfont=dict(size=18, color="white"),
            hovertext=hover_hm, hovertemplate="%{hovertext}<extra></extra>"))
        fig_hm.update_layout(
            paper_bgcolor=BG, plot_bgcolor=PLOT_BG, height=380,
            margin=dict(l=10,r=10,t=10,b=10),
            xaxis=dict(tickangle=-15, tickfont=dict(size=11)),
            yaxis=dict(tickfont=dict(size=11)))
        st.plotly_chart(fig_hm, use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">위험요인 빈도</div>', unsafe_allow_html=True)
        rf_c = risk_df[risk_df["present"]==1].copy()
        rf_c["risk_label"] = rf_c["risk_factor"].map(lambda x: RISK_LABEL.get(x, x))
        rf_agg = rf_c.groupby("risk_label").size().reset_index(name="국가 수").sort_values("국가 수")
        fig_rf = px.bar(rf_agg, x="국가 수", y="risk_label", orientation="h",
            color="국가 수",
            color_continuous_scale=[[0,"#334155"],[1,"#e63946"]],
            labels={"risk_label":"위험요인"})
        fig_rf.update_layout(
            template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
            height=380, margin=dict(l=10,r=10,t=10,b=10),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor="#1e293b", dtick=1),
            yaxis=dict(gridcolor="#1e293b"))
        fig_rf.update_traces(hovertemplate="%{y}<br>%{x}개국에서 확인<extra></extra>")
        st.plotly_chart(fig_rf, use_container_width=True)

    st.markdown('<div class="section-title">국가별 위험요인 레이더</div>', unsafe_allow_html=True)
    risk_cols = [c for c in country_df.columns if c.startswith("risk_") and c != "risk_score"]
    risk_labels_r = [RISK_LABEL.get(c.replace("risk_",""), c) for c in risk_cols]
    fig_r = go.Figure()
    for i, (_, row) in enumerate(country_df.iterrows()):
        vals = [row[c] for c in risk_cols] + [row[risk_cols[0]]]
        kr_name = SHORT.get(row["country"], row["country"])
        fig_r.add_trace(go.Scatterpolar(
            r=vals, theta=risk_labels_r + risk_labels_r[:1],
            fill="toself", name=kr_name,
            line_color=COLORS[i % len(COLORS)], opacity=0.75))
    fig_r.update_layout(
        polar=dict(bgcolor=PLOT_BG,
            radialaxis=dict(visible=True, range=[0,1], showticklabels=False, gridcolor="#334155"),
            angularaxis=dict(gridcolor="#334155")),
        paper_bgcolor=BG, height=420, margin=dict(l=20,r=20,t=20,b=20),
        legend=dict(orientation="h", y=-0.12, font=dict(size=11)),
        template="plotly_dark")
    st.plotly_chart(fig_r, use_container_width=True)

# ════════════ TAB 5: 타임라인 ════════════════════════════════════════════════
with tab_timeline:
    COLOR_MAP = {"disease_outbreak":RED,"multi_epidemic":"#f4a261","conflict_health_crisis":"#457b9d"}
    LABEL_MAP = {"disease_outbreak":"전염병 발생","multi_epidemic":"복합 전염병","conflict_health_crisis":"분쟁·보건 위기"}
    ev = events_df.copy()
    ev["event_label"] = ev["event_type"].map(LABEL_MAP)
    ev["country_kr"]  = ev["country"].map(SHORT).fillna(ev["country"])

    st.markdown('<div class="section-title">위기 이벤트 타임라인</div>', unsafe_allow_html=True)
    fig6 = px.timeline(ev, x_start="start_date", x_end="end_date", y="country_kr",
        color="event_label",
        color_discrete_map={v: COLOR_MAP[k] for k, v in LABEL_MAP.items()},
        hover_name="event_name",
        hover_data={"metric_cases":True,"metric_deaths":True,"disease":True,"event_label":False},
        labels={"event_label":"이벤트 유형","country_kr":"국가",
                "metric_cases":"케이스","metric_deaths":"사망자","disease":"질병"})
    fig6.update_yaxes(autorange="reversed")
    fig6.update_layout(
        template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=PLOT_BG,
        height=400, margin=dict(l=10,r=10,t=10,b=10),
        xaxis=dict(gridcolor="#1e293b", title=""),
        yaxis=dict(gridcolor="#1e293b"),
        legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown('<div class="section-title">이벤트별 사망자 비중</div>', unsafe_allow_html=True)
    ev_d = ev[ev["metric_deaths"].notna()].copy()
    ev_d["label"] = ev_d["country_kr"] + " · " + ev_d["event_name"].str[:22]
    fig_donut = px.pie(ev_d, names="label", values="metric_deaths", hole=0.45,
        color_discrete_sequence=COLORS + ["#7c3aed","#0891b2"])
    fig_donut.update_layout(
        template="plotly_dark", paper_bgcolor=BG,
        height=360, margin=dict(l=10,r=10,t=10,b=10),
        legend=dict(orientation="v", x=1.01, font=dict(size=10)))
    fig_donut.update_traces(
        textinfo="percent+label",
        hovertemplate="%{label}<br>사망자: %{value:,}명<extra></extra>")
    st.plotly_chart(fig_donut, use_container_width=True)

# ════════════ TAB 6: 원시 데이터 ════════════════════════════════════════════
with tab_data:
    st.markdown('<div class="section-title">📄 국가 요약 데이터</div>', unsafe_allow_html=True)
    show_cols = ["country","region_group","primary_crisis","reporting_period",
                 "cases_reported","deaths_reported","injuries_reported",
                 "people_in_need","displaced_people","fatality_rate_pct",
                 "risk_score","data_as_of","source_org","notes"]
    st.dataframe(
        country_df[show_cols].style.format(
            {"cases_reported":"{:,.0f}","deaths_reported":"{:,.0f}",
             "injuries_reported":"{:,.0f}","people_in_need":"{:,.0f}",
             "displaced_people":"{:,.0f}","fatality_rate_pct":"{:.2f}%",
             "risk_score":"{:.0f}"}, na_rep="—"),
        use_container_width=True, height=280)

    st.markdown('<div class="section-title">📄 이벤트 데이터</div>', unsafe_allow_html=True)
    st.dataframe(
        events_df[["country","event_type","event_name","disease",
                   "metric_cases","metric_deaths","metric_injuries",
                   "start_date","end_date"]],
        use_container_width=True, height=240)

    st.markdown('<div class="section-title">📄 위험요인 데이터</div>', unsafe_allow_html=True)
    st.dataframe(risk_df, use_container_width=True, height=240)

st.markdown("---")
st.markdown(
    '<div style="font-size:0.68rem;color:#5a5a7a;font-family:IBM Plex Mono,monospace;line-height:1.9;">'
    '📎 WHO Sudan Cholera Update (2026-03-08) &nbsp;|&nbsp; '
    'WHO DRC Health Emergency Appeal 2026 &nbsp;|&nbsp; '
    'South Sudan HNRP 2026 &nbsp;|&nbsp; '
    'WHO Gaza PHSA (2025-09-10) &nbsp;|&nbsp; '
    'PAHO Haiti Cholera Story (2025-11) &nbsp;|&nbsp; '
    'OHCHR Haiti Violence Update (2025-07)'
    '</div>',
    unsafe_allow_html=True)
