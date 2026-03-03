import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from src.config import Config
from src.ui.layout import Layout
from src.ui.styles import Styles
from src.ui.themes import ThemeManager

# =========================================================
# Page: Home (Dashboard)
# =========================================================

class HomePage:
    def __init__(self, db, ai, analysis):
        self.db = db
        self.ai = ai
        self.analysis = analysis



    def render(self):
        Layout.render_manual("홈")
        
        # 타이틀에 애니메이션 효과 적용 (CSS Class 활용 가능)
        st.title("⛰️ 또닥또닥 산악회")
        
        # [PDF 출력 모드 설정]
        col_title, col_print = st.columns([3, 1])
        with col_print:
            pdf_mode = st.toggle("🖨️ PDF 출력 모드", key="pdf_mode_toggle", help="모든 인포그래픽을 한 화면에 표시하여 PDF로 저장하기 좋게 만듭니다.")
            if pdf_mode:
                st.button("📄 PDF 파일로 저장", on_click=lambda: st.components.v1.html("<script>window.print();</script>", height=0))
        
        # [데이터 로드]
        # v2.24.2 Hotfix: df_summary 정의 복구
        df_summary = self.db.query("SELECT * FROM v_member_attendance_summary")
        # v2.24.4 Hotfix: active_members 정의 복구
        active_members = df_summary[df_summary['회원상태'] != 'exmember']
        
        # [사이드바 AI 브리핑 버튼]
        with st.sidebar:
            st.divider()
            st.subheader("🤖 AI 비서")
            if st.button("✨ 월간 브리핑 생성", use_container_width=True):
                upcoming = self.analysis.get_upcoming_events()
                if upcoming.empty:
                    st.sidebar.warning("예정된 산행 데이터가 없습니다.")
                else:
                    self._show_ai_briefing(upcoming)

        # [탭 또는 전체 보기 구조]
        if not pdf_mode:
            tab_overview, tab_demo, tab_activity = st.tabs(["📊 대시보드 (Overview)", "👥 회원 구성 (Demographics)", "🏆 명예의 전당 (Hall of Fame)"])
            
            # --- [TAB 1] 종합 현황 (Overview) ---
            with tab_overview: self._render_overview(df_summary)

            # --- [TAB 2] 회원 통계 (Demographics) ---
            with tab_demo: self._render_demographics(df_summary)

            # --- [TAB 3] 명예의 전당 (Hall of Fame) ---
            with tab_activity: self._render_hall_of_fame(df_summary, active_members)
        else:
            # PDF 모드: 모든 내용을 위에서 아래로 순차적으로 렌더링
            st.info("💡 **PDF 출력 모드 활성화됨**: 모든 탭의 내용이 아래로 펼쳐집니다. 상단의 'PDF 파일로 저장' 버튼을 눌러주세요.")
            
            st.markdown("### 📊 [1] 종합 현황 (Overview)")
            self._render_overview(df_summary)
            
            st.divider()
            st.markdown("### 👥 [2] 회원 구성 (Demographics)")
            self._render_demographics(df_summary)
            
            st.divider()
            st.markdown("### 🏆 [3] 명예의 전당 (Hall of Fame)")
            self._render_hall_of_fame(df_summary, active_members)

    def _render_overview(self, df_summary):
        # 1. KPI Cards
        total_members, active_count, total_activity_score = self.analysis.get_overview_kpis()

        c = ThemeManager.current.colors

        # Compute active rate for trend display
        active_rate = round(active_count / total_members * 100) if total_members else 0
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(Styles.card_template(f"""
<span class="kpi-label">⛰️ 총 회원수</span><br>
<span class="kpi-value">{total_members}</span><br>
<span class="kpi-trend-up">👥 전체 등록 인원</span>
""", extra_classes="neon-border-cyan animate-fadein"), unsafe_allow_html=True)
        with c2:
            trend_color = "kpi-trend-up" if active_rate >= 50 else "kpi-trend-down"
            trend_icon  = "📈" if active_rate >= 50 else "📉"
            st.markdown(Styles.card_template(f"""
<span class="kpi-label">🔥 최근 활동 회원</span><br>
<span class="kpi-value">{active_count}</span><br>
<span class="{trend_color}">{trend_icon} 활동률 {active_rate}%</span>
""", extra_classes="neon-border-green animate-fadein"), unsafe_allow_html=True)
        with c3:
            st.markdown(Styles.card_template(f"""
<span class="kpi-label">🏅 누적 포인트</span><br>
<span class="kpi-value">{int(total_activity_score):,}</span><br>
<span class="kpi-trend-up">✨ 전체 획득 포인트</span>
""", extra_classes="neon-border-magenta animate-fadein"), unsafe_allow_html=True)
        
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # 2. Events & Weather
        c3, c4 = st.columns([1.2, 1])
        
        with c3:
            with st.container():
                st.subheader("📅 다가오는 산행")
                today = datetime.now().strftime("%Y-%m-%d")
                upcoming = self.analysis.get_upcoming_events()
                
                if not upcoming.empty:
                    for _, row in upcoming.iterrows():
                        d_day = (pd.to_datetime(row['date']) - pd.to_datetime(today)).days
                        badge = f"D-{d_day}" if d_day > 0 else "D-Day"
                        badge_color = "#ef4444" if d_day <= 3 else "#3b82f6"
                        badge_class = "badge-dday animate-badge" if d_day <= 3 else ""
                        
                        birth = str(int(row['birth_year']))[-2:] if pd.notna(row['birth_year']) else "??"
                        host_info = f"{birth}/{row['host_name'] or row['host']}/{row['area'] or '미상'}"
                        img_url = row['profile_image_url'] if pd.notna(row['profile_image_url']) and row['profile_image_url'] else "https://ui-avatars.com/api/?name=" + (row['host_name'] or "Host") + "&background=random"
                        display_date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
                        c = ThemeManager.current.colors
                        
                        st.markdown(f"""
                        <div style="background: {c.card_bg}; border-radius: 14px; margin-bottom: 12px; border: 1px solid {c.border}; display: flex; overflow: hidden; box-shadow: 0 6px 20px rgba(0,0,0,0.15); transition: transform 0.3s ease;" class="hover-3d animate-fadein">
                            <div style="width: 6px; background: linear-gradient(180deg, {badge_color}, {badge_color}88);"></div>
                            <div style="flex-grow: 1; padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                        <span class="{badge_class}" style="background-color: {badge_color}33; color: {badge_color}; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; border: 1px solid {badge_color}55;">{badge}</span>
                                        <span style="font-weight: bold; font-size: 16px; color: {c.text_primary};">{row['title']}</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <img src="{img_url}" style="width: 38px; height: 38px; border-radius: 50%; object-fit: cover; border: 2px solid {badge_color}66;">
                                        <div style="display: flex; flex-direction: column;">
                                            <div style="color: {c.text_secondary}; font-size: 13px; font-weight: 500;">📅 {display_date}</div>
                                            <div style="color: {c.text_secondary}; font-size: 12px; opacity: 0.8;">👑 {host_info}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("예정된 산행이 없습니다.")

        with c4:
            with st.container():
                st.subheader("🌤️ 서울 날씨")
                self._render_weather_forecast()

        # 4. 인포그래픽
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        self._render_infographics()
        
        # 5. 최근 공지 분석
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        self._render_event_analysis()

    def _render_demographics(self, df_summary):
        df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")

        # ── 성별 정규화 ───────────────────────────────────────────────
        if not df_dist.empty:
            df_dist['gender_norm'] = df_dist['gender'].astype(str).str.upper().str.strip()
            gender_map = {
                'M': '남', 'MALE': '남', 'MAN': '남', '남': '남', '남성': '남',
                'F': '여', 'FEMALE': '여', 'WOMAN': '여', 'W': '여', '여': '여', '여성': '여'
            }
            df_dist['gender_final'] = df_dist['gender_norm'].map(gender_map).fillna('U')
            gender_counts = df_dist['gender_final'].value_counts()
            total   = len(df_dist)
            m_count = gender_counts.get('남', 0)
            f_count = gender_counts.get('여', 0)
            u_count = gender_counts.get('U', 0)
        else:
            total = m_count = f_count = u_count = 0

        if not df_dist.empty:
            st.markdown("### 📊 회원 구성 및 성장 (Composition & Growth)")

            # ── 성별 요약 스탯 카드 ───────────────────────────────────
            m_pct = round(m_count / total * 100) if total else 0
            f_pct = round(f_count / total * 100) if total else 0
            u_pct = 100 - m_pct - f_pct

            st.markdown(f"""
<div style="display:flex; gap:12px; margin-bottom:20px;">
  <div style="flex:1; background:linear-gradient(135deg,rgba(59,130,246,0.18),rgba(59,130,246,0.04));
              border:1px solid rgba(59,130,246,0.4); border-radius:16px; padding:16px; text-align:center;">
    <div style="font-size:30px; font-weight:800; color:#60a5fa; letter-spacing:-1px;">♂ {m_count}</div>
    <div style="font-size:11px; color:#93c5fd; margin-top:5px; letter-spacing:2px; text-transform:uppercase;">남성 · {m_pct}%</div>
    <div style="background:rgba(59,130,246,0.2); border-radius:4px; height:5px; margin-top:10px;">
      <div style="background:linear-gradient(90deg,#3b82f6,#60a5fa); width:{m_pct}%; height:100%; border-radius:4px; transition:width 1s;"></div></div>
  </div>
  <div style="flex:1; background:linear-gradient(135deg,rgba(236,72,153,0.18),rgba(236,72,153,0.04));
              border:1px solid rgba(236,72,153,0.4); border-radius:16px; padding:16px; text-align:center;">
    <div style="font-size:30px; font-weight:800; color:#f472b6; letter-spacing:-1px;">♀ {f_count}</div>
    <div style="font-size:11px; color:#f9a8d4; margin-top:5px; letter-spacing:2px; text-transform:uppercase;">여성 · {f_pct}%</div>
    <div style="background:rgba(236,72,153,0.2); border-radius:4px; height:5px; margin-top:10px;">
      <div style="background:linear-gradient(90deg,#ec4899,#f472b6); width:{f_pct}%; height:100%; border-radius:4px;"></div></div>
  </div>
  <div style="flex:1; background:linear-gradient(135deg,rgba(148,163,184,0.12),rgba(148,163,184,0.02));
              border:1px solid rgba(148,163,184,0.25); border-radius:16px; padding:16px; text-align:center;">
    <div style="font-size:30px; font-weight:800; color:#cbd5e1; letter-spacing:-1px;">? {u_count}</div>
    <div style="font-size:11px; color:#94a3b8; margin-top:5px; letter-spacing:2px; text-transform:uppercase;">미확인 · {u_pct}%</div>
    <div style="background:rgba(148,163,184,0.15); border-radius:4px; height:5px; margin-top:10px;">
      <div style="background:#64748b; width:{u_pct}%; height:100%; border-radius:4px;"></div></div>
  </div>
</div>""", unsafe_allow_html=True)

            # ── 나비형 성별 피라미드 + 신규 유입 추이 ─────────────────
            c_pyramid, c_growth = st.columns([1.3, 1])

            with c_pyramid:
                st.markdown("###### 🦋 생년별 성별 피라미드 (Gender Pyramid by Birth Year)")
                try:
                    import plotly.graph_objects as go

                    df_py  = df_dist.groupby(['birth_year', 'gender_final']).size().reset_index(name='cnt')
                    years  = sorted(df_py['birth_year'].dropna().unique())

                    # 2자리 생년 그대로 표시 (70, 71...)
                    yr_lbl = [str(int(y)) for y in years]

                    male_v, female_v, unk_v = [], [], []
                    for yr in years:
                        sub = df_py[df_py['birth_year'] == yr]
                        male_v.append(  int(sub.loc[sub['gender_final'] == '남', 'cnt'].sum()))
                        female_v.append(int(sub.loc[sub['gender_final'] == '여', 'cnt'].sum()))
                        unk_v.append(   int(sub.loc[sub['gender_final'] == 'U',  'cnt'].sum()))

                    max_val = max(max(male_v or [1]), max(female_v or [1])) + 1
                    chart_h = max(400, len(years) * 50 + 100)

                    fig_pyr = go.Figure()

                    # ── 남성 (왼쪽, 음수) ──
                    fig_pyr.add_trace(go.Bar(
                        y=yr_lbl, x=[-v for v in male_v],
                        name='♂ 남성', orientation='h',
                        marker=dict(
                            color=[f'rgba(59,130,246,{0.45 + 0.55 * v / (max_val or 1):.2f})' for v in male_v],
                            line=dict(color='#3b82f6', width=1.2)
                        ),
                        text=[f' {v}명' if v > 0 else '' for v in male_v],
                        textposition='inside',
                        textfont=dict(color='white', size=12, family='Noto Sans KR'),
                        hovertemplate='<b>%{y}년생</b><br>♂ 남성: %{customdata}명<extra></extra>',
                        customdata=male_v
                    ))

                    # ── 여성 (오른쪽, 양수) ──
                    fig_pyr.add_trace(go.Bar(
                        y=yr_lbl, x=female_v,
                        name='♀ 여성', orientation='h',
                        marker=dict(
                            color=[f'rgba(236,72,153,{0.45 + 0.55 * v / (max_val or 1):.2f})' for v in female_v],
                            line=dict(color='#ec4899', width=1.2)
                        ),
                        text=[f'{v}명 ' if v > 0 else '' for v in female_v],
                        textposition='inside',
                        textfont=dict(color='white', size=12, family='Noto Sans KR'),
                        hovertemplate='<b>%{y}년생</b><br>♀ 여성: %{x}명<extra></extra>'
                    ))

                    # ── 미확인 (오른쪽 누적) ──
                    if any(v > 0 for v in unk_v):
                        fig_pyr.add_trace(go.Bar(
                            y=yr_lbl, x=unk_v,
                            name='? 미확인', orientation='h',
                            marker=dict(color='rgba(100,116,139,0.45)', line=dict(color='#475569', width=1)),
                            text=[f'{v}명' if v > 0 else '' for v in unk_v],
                            textposition='inside',
                            textfont=dict(color='#cbd5e1', size=10),
                            hovertemplate='<b>%{y}년생</b><br>? 미확인: %{x}명<extra></extra>'
                        ))

                    fig_pyr.update_layout(
                        barmode='relative',
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        xaxis=dict(
                            range=[-(max_val + 0.5), max_val + 0.5],
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.05)',
                            zeroline=True,
                            zerolinecolor='rgba(255,255,255,0.30)',
                            zerolinewidth=2,
                            tickvals=list(range(-max_val, max_val + 1)),
                            ticktext=[str(abs(v)) for v in range(-max_val, max_val + 1)],
                            tickfont=dict(color='#64748b', size=10),
                            title=None,
                        ),
                        yaxis=dict(
                            showgrid=False,
                            # 모든 연도 레이블 강제 표시
                            tickmode='array',
                            tickvals=yr_lbl,
                            ticktext=yr_lbl,
                            tickfont=dict(color='#e2e8f0', size=13, family='Noto Sans KR'),
                            title=None,
                            automargin=True,
                            categoryorder='array',
                            categoryarray=list(reversed(yr_lbl)),
                        ),
                        legend=dict(
                            orientation='h', yanchor='bottom', y=1.02,
                            xanchor='center', x=0.5,
                            font=dict(size=12, color='white'),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        height=chart_h,
                        margin=dict(t=50, b=20, l=10, r=10),
                        bargap=0.28,
                        hoverlabel=dict(bgcolor='rgba(10,15,30,0.92)', font_size=13, font_color='white')
                    )
                    st.plotly_chart(fig_pyr, use_container_width=True, config={
                        'displayModeBar': False,
                        'scrollZoom': False
                    })

                except Exception as e:
                    st.error(f"Gender Pyramid Error: {e}")

            # ── 신규 회원 유입 추이 (area fill 강화) ─────────────────
            with c_growth:
                st.markdown("###### 📈 신규 회원 유입 추이 (New Member Influx)")
                df_growth = self.analysis.get_member_growth_trend()
                if not df_growth.empty:
                    try:
                        import plotly.graph_objects as go
                        months_g = df_growth['month'].astype(str).tolist()
                        vals_g   = df_growth['new_members'].tolist()
                        chart_h2 = max(340, len(years) * 42) if years else 340

                        fig_growth = go.Figure()
                        fig_growth.add_trace(go.Scatter(
                            x=months_g, y=vals_g,
                            fill='tozeroy',
                            fillcolor='rgba(46,204,113,0.10)',
                            line=dict(color='#2ecc71', width=3, shape='spline'),
                            mode='lines+markers',
                            marker=dict(size=8, color='#2ecc71', line=dict(width=2, color='white')),
                            hovertemplate='<b>%{x}</b><br>신규: %{y}명<extra></extra>'
                        ))
                        fig_growth.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white', family='Noto Sans KR'),
                            xaxis=dict(showgrid=False, title=None,
                                       tickfont=dict(color='#64748b', size=10), tickangle=-35),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.06)', title=None,
                                       tickfont=dict(color='#64748b')),
                            margin=dict(t=44, l=10, r=10, b=40),
                            height=chart_h2,
                            hovermode='x unified',
                            showlegend=False,
                            hoverlabel=dict(bgcolor='rgba(10,15,30,0.92)', font_size=13)
                        )
                        st.plotly_chart(fig_growth, use_container_width=True, config={'displayModeBar': False})
                    except Exception as e:
                        st.error(f"Growth Chart Error: {e}")
                else:
                    st.info("데이터 부족")

        st.divider()
        
        # Map logic (Truncated for brevity, assuming standard map logic)
        self._render_map(df_summary)

    def _render_map(self, df_summary):
        # ... (Map coordinates logic)
        coords = {
                "서울": [37.5665, 126.9780], "경기": [37.4138, 127.5183], "인천": [37.4563, 126.7052],
                "광명": [37.4784, 126.8643], "안양": [37.3910, 126.9269], "고양": [37.6584, 126.8320], "일산": [37.6584, 126.8320],
                "부천": [37.5034, 126.7660], "시흥": [37.3801, 126.8031], "안산": [37.3195, 126.8308],
                "성남": [37.4200, 127.1265], "분당": [37.3827, 127.1189], "용인": [37.2410, 127.1775],
                "수원": [37.2636, 127.0286], "화성": [37.1995, 126.8315], "남양주": [37.6360, 127.2165],
                "구로": [37.4954, 126.8874], "금천": [37.4565, 126.8954], "관악": [37.4782, 126.9515], "서울관악": [37.4782, 126.9515],
                "동작": [37.5124, 126.9393], "사당": [37.4765, 126.9816], "영등포": [37.5264, 126.8962],
                "마포": [37.5636, 126.9019], "서대문": [37.5791, 126.9368], "은평": [37.6027, 126.9291],
                "강서": [37.5509, 126.8495], "양천": [37.5169, 126.8660],
                "강남": [37.5172, 127.0473], "서초": [37.4837, 127.0324], "송파": [37.5145, 127.1066], "강동": [37.5301, 127.1238],
                "노원": [37.6542, 127.0568], "도봉": [37.6688, 127.0471], "김포": [37.6152, 126.7157]
            }
        
        df_map = df_summary['지역'].value_counts().reset_index()
        df_map.columns = ['area', 'count']
        
        def get_coords(area_name):
            if area_name in coords: return coords[area_name]
            for k in coords:
                if k in area_name: return coords[k]
            return [37.5665, 126.9780]

        df_map['lat'] = df_map['area'].apply(lambda x: get_coords(x)[0])
        df_map['lon'] = df_map['area'].apply(lambda x: get_coords(x)[1])
        
        # [RESTORED] Visual Map (Minimalist/Outline Style)
        # 실제 지도 대신 그래픽화된 좌표 시스템 활용 - Grid 제거, 깔끔한 원형 분포
        fig_map = px.scatter(
            df_map, x="lon", y="lat", size="count", color="count",
            hover_name="area", size_max=60,
            text="area",
            color_continuous_scale=[[0, "rgba(255,255,255,0.2)"], [1, ThemeManager.current.colors.primary]], 
            # 투명한 화이트 -> 프라이머리 컬러 (미니멀)
            title='📍 지역별 멤버 분포'
        )
        
        fig_map.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)', # No background
            height=500,
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="", visible=False), # Hide ALL axis elements
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title="", visible=False),
            margin={"r":20,"t":50,"l":20,"b":20},
            title_font=dict(size=18, color=ThemeManager.current.colors.text_secondary, family="Inter, sans-serif"),
            font=dict(color="white", weight='bold'),
            coloraxis_showscale=False
        )
        
        # Add Korea Map Outline (Pseudo) or just keep it abstract
        # Just circles Clean
        fig_map.update_traces(
            textposition='top center', 
            marker=dict(
                line=dict(width=1, color='rgba(255,255,255,0.8)'),
                opacity=0.8,
                symbol='circle'
            ),
            textfont=dict(size=13, color=ThemeManager.current.colors.text_primary)
        )
        
        st.plotly_chart(fig_map, use_container_width=True, config={
            'displayModeBar': False, # Hide toolbar for cleaner look
            'staticPlot': False
        })  


    def _render_event_analysis(self):
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.subheader("📊 최근 공지 분석")
            try:
                df_trend, df_stats = self.analysis.get_event_analysis()
                
                if not df_trend.empty and not df_stats.empty:
                    max_count = df_trend['count'].max()
                    avg_v = df_stats['avg_cnt'].iloc[0] or 0
                    peak_v = df_stats['peak_cnt'].iloc[0] or 0
                    peak_m = df_stats['peak_month'].iloc[0] or "-"
                    low_v = df_stats['low_cnt'].iloc[0] or 0
                    low_m = df_stats['low_month'].iloc[0] or "-"
                    curr_v = df_stats['current_cnt'].iloc[0] or 0
                    
                    curr_v = df_stats['current_cnt'].iloc[0] or 0
                    
                    # [Plotly Restoration] Trend Bar
                    fig_trend = px.bar(
                        df_trend, x="month", y="count",
                        text="count",
                        title="📅 월별 활동 동향",
                        color="count",
                        color_continuous_scale="Tealgrn"
                    )
                    fig_trend.update_traces(textposition='outside')
                    fig_trend.update_layout(
                         paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         font=dict(color='white'),
                         xaxis=dict(showgrid=False, title=""),
                         yaxis=dict(showgrid=False, title=""),
                         height=300
                    )
                    st.plotly_chart(fig_trend, use_container_width=True)

            except Exception as e:
                st.error(f"Trend Load Error: {e}")

        with c2:
            st.markdown("<div style='height: 45px;'></div>", unsafe_allow_html=True)
            try:
                if not df_stats.empty:
                    # 통계 카드 2x2 그리드
                    stats_html = f"""
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<div style="font-size: 22px; margin-bottom: 8px;">📈</div>
<div style="font-size: 13px; color: #ddd; margin-bottom: 4px;">평균 (연간)</div>
<div style="font-size: 22px; font-weight: bold; color: #10b981;">{avg_v:.1f}회</div>
</div>
<div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<div style="font-size: 22px; margin-bottom: 8px;">🏆</div>
<div style="font-size: 13px; color: #ddd; margin-bottom: 4px;">최다 ({peak_m})</div>
<div style="font-size: 22px; font-weight: bold; color: #3b82f6;">{int(peak_v)}회</div>
</div>
<div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<div style="font-size: 22px; margin-bottom: 8px;">📉</div>
<div style="font-size: 13px; color: #ddd; margin-bottom: 4px;">최소 ({low_m})</div>
<div style="font-size: 22px; font-weight: bold; color: #f59e0b;">{int(low_v)}회</div>
</div>
<div style="background: rgba(236, 72, 153, 0.1); border: 1px solid rgba(236, 72, 153, 0.2); padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<div style="font-size: 22px; margin-bottom: 8px;">🔔</div>
<div style="font-size: 13px; color: #ddd; margin-bottom: 4px;">이번 달</div>
<div style="font-size: 22px; font-weight: bold; color: #ec4899;">{int(curr_v)}회</div>
</div>
</div>"""
                    st.markdown(stats_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Stats Load Error: {e}")




    def _render_podium(self, df, value_col, unit="", img_col="profile_image_url"):
        """Render a top-3 podium visualization."""
        podium_colors  = ["#FFD700", "#C0C0C0", "#CD7F32"]
        podium_heights = ["130px", "100px", "80px"]
        podium_order   = [1, 0, 2]  # display: 2nd, 1st, 3rd
        medals         = ["🥇", "🥈", "🥉"]
        rows = df.head(3).reset_index(drop=True)
        if rows.empty:
            return
        # pad to 3
        while len(rows) < 3:
            rows = rows._append({"name": "—", value_col: 0, img_col: None}, ignore_index=True)

        html = '<div class="podium-container">'
        for display_pos, rank in enumerate(podium_order):
            if rank >= len(rows): continue
            row = rows.iloc[rank]
            color  = podium_colors[rank]
            height = podium_heights[rank]
            medal  = medals[rank]
            name   = row.get('name', '—')
            val    = row.get(value_col, 0)
            img_url = row.get(img_col, None)
            if not img_url or str(img_url) == 'nan':
                img_url = f"https://ui-avatars.com/api/?name={name}&background=random&size=80"
            html += f"""
            <div class="podium-block" style="background: linear-gradient(180deg, {color}22, {color}11); border: 1.5px solid {color}66; height: {height}; justify-content: flex-end; padding-bottom: 10px;">
                <img src="{img_url}" style="width:44px;height:44px;border-radius:50%;border:2px solid {color};margin-bottom:6px;">
                <div style="font-size:20px;">{medal}</div>
                <div style="font-weight:bold;color:#fff;font-size:14px;">{name}</div>
                <div style="color:{color};font-size:13px;font-weight:700;">{int(val)}{unit}</div>
            </div>"""
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    def _render_hall_of_fame(self, df_summary, active_members):
        now = datetime.now(Config.KST)
        cur_month_str = now.strftime('%Y-%m')
        st.subheader(f"🏆 {now.month}월의 명예의 전당")
        
        # Summary text builer
        clip_hall_lines = [f"🏆 [{now.month}월의 명예의 전당]"]
        
        c_host, c_attend, c_event = st.columns(3)
        
        def get_rank_html(rank, text, subtext, img_url=None):
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"] 
            color = colors[rank] if rank < 3 else "rgba(128,128,128,0.5)"
            rank_num = rank + 1
            
            c = ThemeManager.current.colors
            
            # 이미지 URL이 없으면 기본 아바타 사용
            if not img_url:
                img_url = f"https://ui-avatars.com/api/?name={text}&background=random"
            
            border_style = f"border: 2px solid {color};" if rank < 3 else f"border: 1px solid {c.border};"
            
            return f"""
            <div class="glass-card hover-3d" style="{border_style} padding: 12px; margin-bottom: 10px; display: flex; align-items: center; background: {c.card_bg};">
                <div style="position: relative; margin-right: 15px;">
                    <img src="{img_url}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid {color if rank < 3 else c.border};">
                    <div style="position: absolute; bottom: -5px; right: -5px; width: 20px; height: 20px; background-color: {color}; color: #000; font-weight: bold; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{rank_num}</div>
                </div>
                <div style="flex-grow: 1;">
                    <div style="font-weight: bold; color: {c.text_primary}; font-size: 15px;">{text}</div>
                    <div style="font-size: 13px; color: {c.text_secondary}; font-weight: 500;">{subtext}</div>
                </div>
            </div>
            """

        df_host, df_attend, df_pop = self.analysis.get_hall_of_fame(cur_month_str)
        
        with c_host:
            st.markdown("##### 📣 이달의 공지왕")
            try:
                if not df_host.empty:
                    self._render_podium(df_host, value_col='cnt', unit='회')
                    st.markdown("---")
                    for idx, row in df_host.iterrows():
                        st.markdown(get_rank_html(idx, row['name'], f"{row['cnt']}회", row['profile_image_url']), unsafe_allow_html=True)
                    names = [f"{r['name']}({r['cnt']}회)" for _, r in df_host.iterrows()]
                    clip_hall_lines.append(f"- 📣 공지왕: {', '.join(names)}")
                else:
                    st.caption("데이터 없음")
            except Exception as e:
                st.error(f"Error: {e}")

        with c_attend:
            st.markdown("##### 🏃 이달의 참석왕")
            try:
                if not df_attend.empty:
                    self._render_podium(df_attend, value_col='score', unit='점')
                    st.markdown("---")
                    for idx, row in df_attend.iterrows():
                        st.markdown(get_rank_html(idx, row['name'], f"{int(row['score'])}점", row['profile_image_url']), unsafe_allow_html=True)
                    names = [f"{r['name']}({int(r['score'])}점)" for _, r in df_attend.iterrows()]
                    clip_hall_lines.append(f"- 🏃 참석왕: {', '.join(names)}")
                else:
                    st.caption("데이터 없음")
            except Exception as e:
                st.error(f"Error: {e}")

        with c_event:
            st.markdown("##### 🔥 이달의 인기 산행")
            try:
                if not df_pop.empty:
                    for idx, row in df_pop.iterrows():
                        # 이벤트는 이미지가 없으므로 텍스트만 표시하는 기존 스타일 유지하거나 아이콘 사용
                        st.markdown(f"""
                        <div style="background-color: rgba(0,0,0,0.4); padding: 10px; border-radius: 12px; margin-bottom: 8px; display: flex; align-items: center; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background-color: #FFFFFF; color: #000; font-weight: bold; display: flex; align-items: center; justify-content: center; margin-right: 12px; flex-shrink: 0; font-size: 14px;">{idx+1}</div>
                            <div style="flex-grow: 1;">
                                <div style="font-weight: bold; color: #fff; font-size: 14px;">{row['title']}</div>
                                <div style="font-size: 13px; color: #ddd;">{row['cnt']}명 참석</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Add to clip text
                    titles = [f"{r['title']}({r['cnt']}명)" for _, r in df_pop.iterrows()]
                    clip_hall_lines.append(f"- 🔥 인기산행: {', '.join(titles)}")
                else:
                    st.caption("데이터 없음")
            except Exception as e:
                st.error(f"Error: {e}")
        


        st.divider()
        # [생년별 포인트 -> 이달의 생년별 참가 현황]
        try:
            df_final = self.analysis.get_monthly_attend_by_birth(cur_month_str)
            if not df_final.empty:
                c = ThemeManager.current.colors
                
                # 차트 생성 (Mockup 기반 프리미엄 디자인)
                fig_attend = px.bar(
                    df_final, x='생년', y='cnt',
                    labels={'cnt': '참가 인원', '생년': '생년별'},
                    text='cnt',
                    color='cnt',
                    # Dynamic Theme Colors
                    color_continuous_scale="Tealgrn"
                )
                
                fig_attend.update_traces(
                    textposition='outside',
                    marker_line_color=c.border,
                    marker_line_width=1.5,
                    opacity=0.85,
                    hovertemplate="<b>%{x}</b><br>참가: %{y}명<extra></extra>"
                )
                
                fig_attend.update_layout(
                    title={
                        'text': f"📅 {now.month}월 생년별 참가 분포 (실인원 기준)",
                        'y':0.95, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top',
                        'font': {'size': 20, 'color': c.text_primary, 'family': ThemeManager.current.font_header}
                    },
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor=c.card_bg, # Use card bg for plot area integration
                    xaxis=dict(
                        showgrid=False, 
                        tickfont=dict(color='#eee', size=13),
                        title=None
                    ),
                    yaxis=dict(
                        gridcolor='rgba(255,255,255,0.05)',
                        tickfont=dict(color='#eee', size=13),
                        title=dict(text="참가 인원수", font=dict(color='#bbb', size=13))
                    ),
                    showlegend=False,
                    coloraxis_showscale=False,
                    height=450,
                    margin=dict(t=80, b=40, l=40, r=40),
                    modebar=dict(bgcolor='rgba(255,255,255,0.8)', color='black', activecolor='#ec4899')
                )
                
                st.plotly_chart(fig_attend, use_container_width=True, config={
                    'displayModeBar': True, 
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                })
                
                # 총 참가 인원 요약
                total_m_attend = int(df_final['cnt'].sum())
                st.markdown(f"""
                <div style="text-align: center; color: #ddd; font-size: 15px; margin-top: -10px;">
                    🎯 이번 달 총 참가 실인원: <span style="color: #ec4899; font-weight: bold; font-size: 19px;">{total_m_attend}명</span> (생년별 중복 제외 합계)
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"📅 생년 데이터가 없습니다.")
        except Exception as e:
            st.error(f"Chart Render Error: {e}")

    def _render_infographics(self):
        st.subheader("📊 멤버십 & 활동 인사이트 (Insights)")
        
        c1, c2 = st.columns(2)
        
        # 1. Active vs Dormant (Donut)
        with c1:
            try:
                seg_counts = self.analysis.get_member_activity_segmentation()
                if not seg_counts.empty:
                    df_seg = seg_counts.reset_index()
                    df_seg.columns = ['status', 'count']
                    
                    # [Translation] Map status to Korean with criteria
                    status_map = {
                        'New': '🌱 신규 (1개월 내)',
                        'Active': '🔥 열정 (3개월 내)',
                        'Casual': '🙂 일반 (6개월 내)',
                        'Dormant': '💤 휴면 (6개월~/미참석)'
                    }
                    df_seg['status_ko'] = df_seg['status'].map(status_map).fillna(df_seg['status'])
                    
                    # Color Mapping (Keys must match new Korean labels)
                    colors = {
                        '🌱 신규 (1개월 내)': '#4ade80',  # Green
                        '🔥 열정 (3개월 내)': '#3b82f6',  # Blue
                        '🙂 일반 (6개월 내)': '#60a5fa',  # Light Blue
                        '💤 휴면 (6개월~/미참석)': '#334155' # Slate
                    }
                    
                    fig_seg = px.pie(
                        df_seg, values='count', names='status_ko',
                        color='status_ko',
                        color_discrete_map=colors,
                        hole=0.62,
                        title=None
                    )
                    
                    # Center Text
                    total_act = df_seg[df_seg['status'].isin(['Active', 'Casual', 'New'])]['count'].sum()
                    active_rate = (total_act / df_seg['count'].sum() * 100)
                    
                    fig_seg.update_traces(
                        textinfo='percent',
                        textposition='outside',
                        textfont=dict(size=13),
                        marker=dict(line=dict(color='#0e1117', width=5)),
                        pull=[0.03] * len(df_seg)
                    )
                    fig_seg.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        showlegend=True,
                        legend=dict(
                            orientation='h', yanchor='bottom', y=-0.25,
                            xanchor='center', x=0.5,
                            font=dict(size=11, color='#cbd5e1'),
                            bgcolor='rgba(0,0,0,0)'
                        ),
                        height=350,
                        margin=dict(t=20, b=60, l=20, r=20),
                        annotations=[dict(
                            text=f"<b>{int(active_rate)}%</b><br><span style='font-size:12px'>활동중</span>",
                            x=0.5, y=0.5, font_size=24, showarrow=False,
                            font_color='white', align='center'
                        )]
                    )
                    st.markdown("<p class='chart-title'>🏃 활동 회원 비율 (Activity Rate)</p>", unsafe_allow_html=True)
                    st.plotly_chart(fig_seg, use_container_width=True)
                else:
                    st.info("데이터 부족")
            except Exception as e:
                st.error(f"Activity Chart Error: {e}")

        # 2. Seasonal Activity (Bar)
        with c2:
            try:
                df_season = self.analysis.get_event_seasonality()
                if not df_season.empty:
                    # [Translation] Map seasons to Korean
                    season_map_ko = {
                        'Spring': '🌸 봄',
                        'Summer': '☀️ 여름',
                        'Autumn': '🍂 가을',
                        'Winter': '❄️ 겨울'
                    }
                    # [Fix] Convert Categorical to string to avoid "Cannot set a Categorical with another" error
                    df_season['season_ko'] = df_season['season'].astype(str).map(season_map_ko).fillna(df_season['season'].astype(str))
                    
                    fig_sea = px.bar(
                        df_season, x='season_ko', y='cnt',
                        color='season_ko',
                        color_discrete_map={'🌸 봄': '#f472b6', '☀️ 여름': '#22c55e', '🍂 가을': '#fb923c', '❄️ 겨울': '#60a5fa'},
                        text='cnt'
                    )
                    fig_sea.update_traces(
                        textposition='outside',
                        textfont=dict(size=14, color='white'),
                        marker_line_width=0,
                        width=0.55
                    )
                    fig_sea.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        xaxis=dict(title=None, showgrid=False, tickfont=dict(size=14)),
                        yaxis=dict(title=None, showgrid=True, gridcolor='rgba(255,255,255,0.08)',
                                   tickfont=dict(color='#64748b', size=11)),
                        height=350,
                        showlegend=False,
                        bargap=0.35,
                        margin=dict(t=40, l=10, r=10, b=20)
                    )
                    st.markdown("<p class='chart-title'>🍂 계절별 산행 빈도 (Seasonality)</p>", unsafe_allow_html=True)
                    st.plotly_chart(fig_sea, use_container_width=True)
                else:
                    st.info("데이터 부족")
            except Exception as e:
                st.error(f"Seasonality Chart Error: {e}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        
        # 3. Monthly Bubble Timeline — NEW
        self._render_monthly_bubble_timeline()

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # 4. Participation Timing (Conversion Speed)
        st.subheader("⚡ 골든 타임 (Golden Time)")
        c3, c4 = st.columns([1, 2])
        
        with c3:
            st.markdown("""
            <div class="insight-card">
                <span class="title">❓ 언제 첫 산행을 할까요?</span>
                신규 회원이 가입 후 <b>첫 산행</b>에 참여하기까지 걸리는 시간을 분석합니다.<br>
                대부분의 열정적인 회원은 <span class="highlight">가입 후 1개월 이내</span>에 첫 활동을 시작합니다. 빠른 참여가 장기 활동으로 이어지는 핵심 지표입니다.
            </div>
            """, unsafe_allow_html=True)
            
        with c4:
            try:
                timing_stats = self.analysis.get_participation_timing_stats()
                if not timing_stats.empty:
                    df_timing = timing_stats.reset_index()
                    df_timing.columns = ['range', 'count']
                    
                    fig_timing = px.bar(
                        df_timing, x='count', y='range', orientation='h',
                        text='count',
                        color='range',
                        color_discrete_sequence=['#ef4444', '#f59e0b', '#3b82f6', '#94a3b8']
                    )
                    
                    fig_timing.update_traces(
                        textposition='inside',
                        textfont=dict(color='white', size=15, family='Noto Sans KR'),
                        width=0.6
                    )
                    fig_timing.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        xaxis=dict(showgrid=False, title=None, visible=False),
                        yaxis=dict(showgrid=False, title=None, tickfont=dict(size=14, family='Noto Sans KR')),
                        height=300,
                        margin=dict(t=10, b=10, l=10, r=30),
                        showlegend=False
                    )
                    st.plotly_chart(fig_timing, use_container_width=True)
                else:
                    st.info("📉 데이터 분석 중...")
            except Exception as e:
                st.error(f"Timing Error: {e}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # 5. 요일별 산행 레이더 + 생년별 참여율 ─────────────────────────
        st.subheader("📡 요일별 산행 패턴 & 생년별 참여율")
        c5, c6 = st.columns(2)

        with c5:
            try:
                import plotly.graph_objects as go
                df_dow = self.analysis.get_event_weekday_stats()
                if not df_dow.empty:
                    day_order = ['월','화','수','목','금','토','일']
                    dow_map   = {'0':'일','1':'월','2':'화','3':'수','4':'목','5':'금','6':'토'}
                    df_dow['day_name'] = df_dow['dow_num'].astype(str).map(dow_map)
                    # full week fill
                    base = pd.DataFrame({'day_name': day_order})
                    df_dow = base.merge(df_dow[['day_name','cnt']], on='day_name', how='left').fillna(0)
                    vals = df_dow['cnt'].tolist()
                    vals += [vals[0]]  # close the loop
                    cats = day_order + [day_order[0]]

                    fig_dow = go.Figure(go.Scatterpolar(
                        r=vals, theta=cats,
                        fill='toself',
                        fillcolor='rgba(46,204,113,0.28)',
                        line=dict(color='#2ecc71', width=3),
                        marker=dict(size=10, color='#2ecc71', line=dict(width=2, color='white')),
                        hovertemplate='<b>%{theta}</b>요일<br>산행: %{r}회<extra></extra>'
                    ))
                    fig_dow.update_layout(
                        polar=dict(
                            bgcolor='rgba(0,0,0,0)',
                            radialaxis=dict(visible=True, showticklabels=True,
                                            tickfont=dict(color='#94a3b8', size=11),
                                            gridcolor='rgba(255,255,255,0.12)'),
                            angularaxis=dict(tickfont=dict(color='#e2e8f0', size=16, family='Noto Sans KR'),
                                             gridcolor='rgba(255,255,255,0.12)')
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        showlegend=False,
                        height=360,
                        margin=dict(t=40, b=40, l=40, r=40)
                    )
                    st.markdown("<p class='chart-title'>🗓️ 요일별 산행 빈도 (레이더)</p>", unsafe_allow_html=True)
                    st.plotly_chart(fig_dow, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("데이터 부족")
            except Exception as e:
                st.error(f"Weekday Chart Error: {e}")

        with c6:
            try:
                import plotly.graph_objects as go
                cur_month_str = datetime.now().strftime('%Y-%m')

                # 이번 달 생년별 실제 참가 인원
                df_m = self.analysis.get_monthly_attend_by_birth(cur_month_str)

                # 생년별 전체 회원 수
                df_total = self.db.query(
                    "SELECT birth_year, COUNT(*) as total FROM members WHERE role<>'exmember' GROUP BY birth_year"
                )

                if not df_m.empty and not df_total.empty:
                    df_m['birth_year_n'] = df_m['birth_year'].astype(int)
                    df_total['birth_year_n'] = df_total['birth_year'].astype(int)
                    df_merged = df_m.merge(df_total[['birth_year_n','total']], on='birth_year_n', how='left').fillna(1)
                    df_merged['rate'] = (df_merged['cnt'] / df_merged['total'] * 100).round(1)
                    df_merged['label'] = df_merged['birth_year_n'].astype(str).str[-2:] + "년생"
                    df_merged = df_merged.sort_values('birth_year_n')

                    colors = [
                        f'rgba(46,204,113,{max(0.15, 0.15 + 0.85 * r/100):.2f})'
                        for r in df_merged['rate']
                    ]
                    hover = [
                        f"{r['label']}<br>{int(r['cnt'])}명 / {int(r['total'])}명 = {r['rate']:.1f}%"
                        for _, r in df_merged.iterrows()
                    ]

                    fig_part = go.Figure(go.Bar(
                        y=df_merged['label'],
                        x=df_merged['rate'],
                        orientation='h',
                        marker=dict(color=colors, line=dict(color='#2ecc71', width=0.8)),
                        text=[f"{r:.0f}%" if r > 0 else "" for r in df_merged['rate']],
                        textposition='outside',
                        textfont=dict(color='#e2e8f0', size=13, family='Noto Sans KR'),
                        customdata=hover,
                        hovertemplate='%{customdata}<extra></extra>'
                    ))
                    fig_part.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='white', family='Noto Sans KR'),
                        xaxis=dict(range=[0, 125], showgrid=True,
                                   gridcolor='rgba(255,255,255,0.06)', title=None,
                                   ticksuffix='%', tickfont=dict(color='#64748b', size=11)),
                        yaxis=dict(showgrid=False, automargin=True,
                                   tickfont=dict(color='#e2e8f0', size=13),
                                   categoryorder='array',
                                   categoryarray=df_merged['label'].tolist()),
                        height=360,
                        margin=dict(t=30, b=10, l=10, r=40),
                        hoverlabel=dict(bgcolor='rgba(10,15,30,0.9)', font_size=13)
                    )
                    st.markdown(f"<p class='chart-title'>🎯 {cur_month_str} 생년별 참가율 (이번 달)</p>", unsafe_allow_html=True)
                    st.plotly_chart(fig_part, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("이번 달 참가 데이터 없음")
            except Exception as e:
                st.error(f"Monthly Participation Error: {e}")

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # 6. 이벤트 스코어 Top-10 랭킹 ────────────────────────────────
        st.subheader("🏅 산행 스코어 TOP 10 (Event Score Ranking)")
        try:
            import plotly.graph_objects as go
            df_top = self.db.query("""
                SELECT e.title,
                       e.score,
                       COUNT(a.user_no) as attendees,
                       e.score * COUNT(a.user_no) as total_score,
                       strftime('%Y-%m', e.date) as month
                FROM events e
                JOIN attendees a ON e.event_id = a.event_id
                GROUP BY e.event_id, e.title, e.score, e.date
                ORDER BY total_score DESC
                LIMIT 10
            """)
            if not df_top.empty:
                df_top = df_top.sort_values('total_score')  # ascending for horizontal bar
                labels = [f"{row['title'][:18]}…" if len(row['title']) > 18 else row['title']
                          for _, row in df_top.iterrows()]
                hover  = [f"{row['title']}<br>참가: {int(row['attendees'])}명 × {int(row['score'])}점 = {int(row['total_score'])}점<br>({row['month']})"
                          for _, row in df_top.iterrows()]

                bar_colors = [f'rgba(46,204,113,{0.35 + 0.65 * i / (len(df_top)-1 or 1):.2f})'
                              for i in range(len(df_top))]

                fig_top = go.Figure(go.Bar(
                    y=labels,
                    x=df_top['total_score'].tolist(),
                    orientation='h',
                    marker=dict(color=bar_colors, line=dict(color='#2ecc71', width=0.8)),
                    text=[f"  {int(v)}점" for v in df_top['total_score']],
                    textposition='outside',
                    textfont=dict(color='#e2e8f0', size=11),
                    customdata=hover,
                    hovertemplate='%{customdata}<extra></extra>'
                ))
                fig_top.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white', family='Noto Sans KR'),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)',
                               title=None, tickfont=dict(color='#64748b', size=10)),
                    yaxis=dict(showgrid=False, automargin=True,
                               tickfont=dict(color='#e2e8f0', size=12)),
                    height=420,
                    margin=dict(t=20, b=20, l=10, r=60),
                    hoverlabel=dict(bgcolor='rgba(10,15,30,0.9)', font_size=13)
                )
                st.plotly_chart(fig_top, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("데이터 부족")
        except Exception as e:
            st.error(f"Top10 Chart Error: {e}")

    def _render_monthly_bubble_timeline(self):
        """월별 산행 활동 버블 타임라인 (x=month, y=events, size=attendance)"""
        st.subheader("📅 월별 활동 버블 타임라인")
        try:
            df_trend, _ = self.analysis.get_event_analysis()
            if df_trend.empty:
                st.info("데이터 부족")
                return

            import plotly.graph_objects as go
            c = ThemeManager.current.colors

            months = df_trend['month'].astype(str).tolist()
            counts = df_trend['count'].tolist()
            max_c  = max(counts) if counts else 1

            fig = go.Figure()
            for i, (month, cnt) in enumerate(zip(months, counts)):
                bubble_color = f"rgba(46, 204, 113, {0.30 + 0.70 * cnt / max_c:.2f})"
                bubble_size  = max(32, int(24 + 56 * cnt / max_c))
                fig.add_trace(go.Scatter(
                    x=[month],
                    y=[cnt],
                    mode='markers+text',
                    marker=dict(
                        size=bubble_size,
                        color=bubble_color,
                        line=dict(width=2.5, color='rgba(46, 204, 113, 0.95)'),
                        opacity=0.88
                    ),
                    text=[str(cnt)],
                    textposition='middle center',
                    textfont=dict(color='white', size=15, family='Noto Sans KR', weight=700),
                    hovertemplate=f"<b>{month}</b><br>산행 횟수: {cnt}회<extra></extra>",
                    showlegend=False
                ))

            # Connect with line
            fig.add_trace(go.Scatter(
                x=months, y=counts,
                mode='lines',
                line=dict(color='rgba(46, 204, 113, 0.35)', width=2, dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))

            y_min = max(0, min(counts) - 1) if counts else 0
            y_max = (max(counts) + 1.5) if counts else 5

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white', family='Noto Sans KR'),
                xaxis=dict(
                    showgrid=False, title=None,
                    tickfont=dict(color='#94a3b8', size=13),
                    tickangle=-30
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='rgba(255,255,255,0.07)',
                    title=dict(text='산행 횟수', font=dict(color='#aaa', size=12)),
                    tickfont=dict(color='#64748b', size=11),
                    range=[y_min, y_max]
                ),
                height=360,
                margin=dict(t=30, b=50, l=50, r=30),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Bubble Timeline Error: {e}")

    def _render_weather_forecast(self):
        try:
            d = self.analysis.get_weather_forecast()
            
            if d:
                dates = d['time']
                codes = d['weather_code']
                max_t = d['temperature_2m_max']
                min_t = d['temperature_2m_min']
                
                def get_icon(c):
                    if c == 0: return "☀️"
                    if c in [1,2,3]: return "🌥️"
                    if c in [45,48]: return "🌫️"
                    if c in [51,53,55,61,63,65]: return "🌧️"
                    if c in [71,73,75,77]: return "❄️"
                    if c >= 95: return "⛈️"
                    return "🌡️"

                cols = st.columns(7)
                for i in range(7): 
                    with cols[i]:
                        dt = datetime.strptime(dates[i], "%Y-%m-%d")
                        dow = ["월", "화", "수", "목", "금", "토", "일"][dt.weekday()]
                        
                        st.markdown(f"""<div style="text-align: center; font-size: 12px; background-color: rgba(255,255,255,0.05); padding: 5px; border-radius: 8px;">
                        {dt.strftime('%m/%d')}<br>({dow})<br>
                        <span style="font-size: 20px;">{get_icon(codes[i])}</span><br>
                        <span style="color: #ff6b6b;">{int(max_t[i])}°</span><br><span style="color: #4ecdc4;">{int(min_t[i])}°</span>
                        </div>""", unsafe_allow_html=True)
            else:
                st.error("날씨 정보 없음")
        except Exception as e:
            st.error("날씨 로드 실패")

    def _show_ai_briefing(self, upcoming_events):
        with st.chat_message("assistant"):
            with st.spinner("🤖 산악회 비서가 데이터를 분석 중입니다..."):
                try:
                    summary_text = f"현재 날짜: {datetime.now().strftime('%Y-%m-%d')}\n"
                    if not upcoming_events.empty:
                        for _, row in upcoming_events.iterrows():
                            summary_text += f"- 일정: {row['title']} ({row['date']}), 담당: {row['host']}\n"
                    
                    if self.ai and self.ai.model:
                        response = self.ai.model.generate_content(f"""
                        당신은 '또닥또닥 산악회'의 AI 비서입니다. 
                        다음 일정 정보를 바탕으로 회원들에게 전할 활기차고 유용한 월간 브리핑을 작성해주세요.
                        날씨 언급은 일반적인 계절감을 섞어서 해주세요.
                        
                        [정보]
                        {summary_text}
                        """)
                        st.markdown(response.text)
                    else:
                        st.info("AI 모델이 연결되지 않았습니다.")
                except Exception as e:
                    st.error(f"AI 분석 중 오류 발생: {e}")
