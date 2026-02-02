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

    def _add_clip_button(self, key, title, content):
        """리포트 생성을 위한 클립보드 버튼"""
        if st.button("📋 리포트에 담기", key=key, help="이 내용을 '보고서 생성' 페이지로 가져갑니다."):
            if 'report_clips' not in st.session_state:
                st.session_state['report_clips'] = []
            
            # 중복 체크
            if not any(c['key'] == key for c in st.session_state['report_clips']):
                st.session_state['report_clips'].append({
                    'key': key,
                    'title': title,
                    'content': content
                })
                st.toast(f"✅ '{title}' 내용이 담겼습니다! (보고서 페이지에서 확인)")
            else:
                st.toast(f"⚠️ 이미 담긴 내용입니다: {title}")

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
        
        c1, c2, c3 = st.columns(3)
        with c1:
            # Force White/Light colors for visibility on dark background
            st.markdown(Styles.card_template(f"""<span style="font-size: 15px; color: #b7e4c7 !important; font-weight: bold;">총 회원수</span><br><span style="font-size: 38px; font-weight: bold; color: #ffffff !important;">{total_members}</span>""", extra_classes="neon-border-cyan"), unsafe_allow_html=True)
        with c2:
            st.markdown(Styles.card_template(f"""<span style="font-size: 15px; color: #b7e4c7 !important; font-weight: bold;">최근 활동 회원</span><br><span style="font-size: 38px; font-weight: bold; color: #ffffff !important;">{active_count}</span>""", extra_classes="neon-border-green"), unsafe_allow_html=True)
        with c3:
            st.markdown(Styles.card_template(f"""<span style="font-size: 15px; color: #b7e4c7 !important; font-weight: bold;">누적 포인트</span><br><span style="font-size: 38px; font-weight: bold; color: #ffffff !important;">{int(total_activity_score):,}</span>""", extra_classes="neon-border-magenta"), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 2. Events & Weather
        c3, c4 = st.columns([1.2, 1])
        
        with c3:
            st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
            st.subheader("📅 다가오는 산행")
            today = datetime.now().strftime("%Y-%m-%d")
            upcoming = self.analysis.get_upcoming_events()
            
            if not upcoming.empty:
                for _, row in upcoming.iterrows():
                    d_day = (pd.to_datetime(row['date']) - pd.to_datetime(today)).days
                    badge = f"D-{d_day}" if d_day > 0 else "D-Day"
                    badge_color = "#ef4444" if d_day <= 3 else "#3b82f6"
                    
                    # 주최자 상세 정보 포맷팅 (생년/이름/지역)
                    birth = str(int(row['birth_year']))[-2:] if pd.notna(row['birth_year']) else "??"
                    host_info = f"{birth}/{row['host_name'] or row['host']}/{row['area'] or '미상'}"
                    
                    # 프로필 이미지 처리
                    img_url = row['profile_image_url'] if pd.notna(row['profile_image_url']) and row['profile_image_url'] else "https://ui-avatars.com/api/?name=" + (row['host_name'] or "Host") + "&background=random"
                    
                    # 날짜 형식 처리 (시간 정보 제거)
                    display_date = pd.to_datetime(row['date']).strftime('%Y-%m-%d')
                    
                    c = ThemeManager.current.colors
                    
                    st.markdown(f"""
                    <div style="background: {c.card_bg}; border-radius: 12px; margin-bottom: 12px; border: 1px solid {c.border}; display: flex; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05); transition: transform 0.3s ease;" class="hover-3d">
                        <div style="width: 6px; background: {badge_color};"></div>
                        <div style="flex-grow: 1; padding: 12px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                    <span style="background-color: {badge_color}22; color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{badge}</span>
                                    <span style="font-weight: bold; font-size: 16px; color: {c.text_primary};">{row['title']}</span>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <img src="{img_url}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover; border: 1px solid {c.border};">
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
            st.markdown("</div>", unsafe_allow_html=True)
            
            # [Clip Button for Upcoming Events]
            if not upcoming.empty:
                clip_text = f"📅 [다가오는 산행]\n"
                for _, row in upcoming.iterrows():
                    d_day = (pd.to_datetime(row['date']) - pd.to_datetime(today)).days
                    dd_str = f"D-{d_day}" if d_day > 0 else "D-Day"
                    clip_text += f"- {row['title']} ({pd.to_datetime(row['date']).strftime('%m/%d')}, {dd_str}) / 담당: {row['host_name'] or row['host']}\n"
                
                st.markdown("<div style='margin-top: 5px; text-align: right;'>", unsafe_allow_html=True)
                self._add_clip_button("clip_upcoming", "다가오는 산행", clip_text)
                st.markdown("</div>", unsafe_allow_html=True)

        with c4:
            st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
            st.subheader("🌤️ 서울 날씨")
            self._render_weather_forecast()
            st.markdown("</div>", unsafe_allow_html=True)

        # 4. 인포그래픽 (New)
        st.markdown("---")
        self._render_infographics()
        
        # 5. 최근 공지 분석 (Relocated from Demographics)
        st.markdown("---")
        self._render_event_analysis()

    def _render_demographics(self, df_summary):
        c3, c4 = st.columns(2)
        df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")
        
        # [Fix] Define variables at top scope for safety
        if not df_dist.empty:
            df_dist['gender_norm'] = df_dist['gender'].astype(str).str.upper().str.strip()
            gender_map = {'M': 'M', 'MALE': 'M', 'MAN': 'M', '남': 'M', '남성': 'M', 'F': 'F', 'FEMALE': 'F', 'WOMAN': 'F', 'W': 'F', '여': 'F', '여성': 'F'}
            df_dist['gender_final'] = df_dist['gender_norm'].map(gender_map).fillna('U')
            
            gender_counts = df_dist['gender_final'].value_counts()
            total = len(df_dist)
            m_count, f_count, u_count = gender_counts.get('M', 0), gender_counts.get('F', 0), gender_counts.get('U', 0)
        else:
            total, m_count, f_count, u_count = 0, 0, 0, 0

        with c3:
            st.markdown("### 📅 연도별 인원 (Birth Year)")
            st.markdown("""
            <div style="display: flex; gap: 15px; margin-bottom: 10px; font-size: 14px; color: #eee; background-color: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 8px; width: fit-content;">
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #3b82f6; border-radius: 50%; margin-right: 6px;"></span>
                    <span>남성 (Male)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #ec4899; border-radius: 50%; margin-right: 6px;"></span>
                    <span>여성 (Female)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not df_dist.empty:
                # [Chart Restoration] Original Bubble Chart (Total per Year)
                # Calculates Total per Year and plots single bubble + count text
                age_gender = df_dist.groupby(['birth_year', 'gender_final']).size().unstack(fill_value=0)
                if 'M' not in age_gender.columns: age_gender['M'] = 0
                if 'F' not in age_gender.columns: age_gender['F'] = 0
                age_gender['total'] = age_gender.sum(axis=1)
                age_gender = age_gender.reset_index()

                # [Chart FIX] Restoration of 3.x Custom HTML Bubble Chart
                max_total = age_gender['total'].max()
                
                html_balls = '<div style="background-color:rgba(0,0,0,0.4);padding:15px;border-radius:12px;display:flex;flex-wrap:wrap;gap:12px;justify-content:center;align-items:center;border:1px solid rgba(255,255,255,0.05);">'
                for _, row in age_gender.iterrows():
                    year_val = int(row['birth_year'])
                    count = int(row['total'])
                    m_val = int(row['M'])
                    f_val = int(row['F'])
                    
                    m_pct = (m_val / count * 100) if count > 0 else 0
                    bg_style = f"background:linear-gradient(135deg, #3b82f6 {m_pct}%, #ec4899 {m_pct}%);"
                    
                    size = 55 + (count / max_total * 45) if max_total > 0 else 55
                    font_size = 13 + (count / max_total * 5)
                    
                    html_balls += f'<div class="hover-3d" style="width:{size}px;height:{size}px;border-radius:50%;{bg_style}color:white;display:flex;flex-direction:column;justify-content:center;align-items:center;box-shadow:0 4px 10px rgba(0,0,0,0.3);border:2px solid rgba(255,255,255,0.15);" title="{year_val}년생: {count}명 (남{m_val}/여{f_val})"><span style="font-weight:bold;font-size:{font_size}px;line-height:1;text-shadow:1px 1px 2px rgba(0,0,0,0.8);">{year_val}년</span><span style="font-size:{font_size*0.8}px;opacity:0.9;text-shadow:1px 1px 2px rgba(0,0,0,0.8);">{count}명</span></div>'
                html_balls += '</div>'
                st.markdown(html_balls, unsafe_allow_html=True)


        with c4:
            st.subheader("⚖️ 성별 분포")
            if not df_dist.empty:
                gender_counts = df_dist['gender_final'].value_counts().reset_index()
                gender_counts.columns = ['gender', 'count']
                gender_counts['label'] = gender_counts['gender'].map({'M': '남성', 'F': '여성', 'U': '미상'})
                
                fig_gender = px.pie(
                    gender_counts, values='count', names='label',
                    color='label',
                    color_discrete_map={'남성': '#3b82f6', '여성': '#ec4899', '미상': '#64748b'},
                    hole=0.4
                )
                fig_gender.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='white'),
                    height=350,
                    showlegend=True
                )
                st.plotly_chart(fig_gender, use_container_width=True)

            
        # [Clip Button for Demographics]
        if not df_dist.empty:
            clip_demo = f"👥 [회원 구성 통계]\n"
            # Gender summary
            clip_demo += f"- 성별 분포: 남성 {m_count}명({(m_count / total * 100) if total else 0:.1f}%), 여성 {f_count}명({(f_count / total * 100) if total else 0:.1f}%)\n"
            # Top 3 birth years
            if 'total' in age_gender.columns:
                top_births = age_gender.sort_values(by='total', ascending=False).head(3)
                birth_summary = ", ".join([f"{idx}년({int(row['total'])}명)" for idx, row in top_births.iterrows()])
                clip_demo += f"- 최다 인원 생년: {birth_summary}"
            
            st.markdown("<div style='margin-top: 10px; text-align: right;'>", unsafe_allow_html=True)
            self._add_clip_button("clip_demographics", "회원 구성 통계", clip_demo)
            st.markdown("</div>", unsafe_allow_html=True)

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

        # [Clip Button for Analysis]
        if not df_stats.empty:
            clip_analysis = f"📊 [최근 산행 분석]\n"
            clip_analysis += f"- 연간 평균 산행: {avg_v:.1f}회\n"
            clip_analysis += f"- 활동 최다월: {peak_m} ({int(peak_v)}회)\n"
            clip_analysis += f"- 이번 달 활동: {int(curr_v)}회"
            
            st.markdown("<div style='margin-top: 10px; text-align: right;'>", unsafe_allow_html=True)
            self._add_clip_button("clip_analysis", "최근 산행 분석", clip_analysis)
            st.markdown("</div>", unsafe_allow_html=True)


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
                    for idx, row in df_host.iterrows():
                        st.markdown(get_rank_html(idx, row['name'], f"{row['cnt']}회", row['profile_image_url']), unsafe_allow_html=True)
                    
                    # Add to clip text
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
                    for idx, row in df_attend.iterrows():
                        st.markdown(get_rank_html(idx, row['name'], f"{int(row['score'])}점", row['profile_image_url']), unsafe_allow_html=True)
                    
                    # Add to clip text
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
        
        # [Clip Button for Hall of Fame]
        st.markdown("<div style='margin-top: 10px; text-align: right;'>", unsafe_allow_html=True)
        self._add_clip_button(f"clip_hof_{cur_month_str}", f"{now.month}월 명예의 전당", "\n".join(clip_hall_lines))
        st.markdown("</div>", unsafe_allow_html=True)

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
        st.subheader("📊 멤버십 & 활동 인사이트")
        
        c1, c2 = st.columns(2)
        
        # 1. 세대별 참여율 (Participation Rate)
        with c1:
            try:
                df_age = self.analysis.get_participation_by_age_group()
                if not df_age.empty:
                    # Radial Chart or Bar Chart
                    # Let's use Bar Chart for clarity
                    fig_age = px.bar(
                        df_age, x='age_group_str', y='participation_rate',
                        title="📌 출생년도별 활동 참여율 (%)",
                        text='participation_rate',
                        color='participation_rate',
                        color_continuous_scale='Blues'
                    )
                    fig_age.update_traces(
                        texttemplate='%{text}%', 
                        textposition='outside',
                        marker_line_color='rgba(255,255,255,0.2)',
                        marker_line_width=1
                    )
                    fig_age.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color=ThemeManager.current.colors.text_primary),
                        xaxis=dict(title=None, tickfont=dict(size=14)),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=None, range=[0, 110]),
                        height=250,
                        margin=dict(t=40, b=20, l=20, r=20),
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_age, use_container_width=True, config={'displayModeBar': False})
                    
                    # Insight Text
                    best_gen = df_age.loc[df_age['participation_rate'].idxmax()]
                    st.caption(f"💡 **{best_gen['age_group_str']}**의 참여율이 **{best_gen['participation_rate']}%**로 가장 높습니다!")
                else:
                    st.info("데이터 부족")
            except Exception as e:
                st.error(f"Age Chart Error: {e}")

        # 2. 요일별 활동 패턴 (Day of Week)
        with c2:
            try:
                df_dow = self.analysis.get_event_weekday_stats()
                if not df_dow.empty:
                    # Polar Chart (Radar) for aesthetics
                    # Need to close the loop for radar? No, Bar Polar is better for discrete
                    fig_dow = px.line_polar(
                        df_dow, r='cnt', theta='day_name', line_close=True,
                        title="🗓️ 요일별 산행 빈도 Pattern",
                        markers=True
                    )
                    fig_dow.update_traces(
                        fill='toself', 
                        line_color=ThemeManager.current.colors.accent,
                        marker=dict(size=8, color='white')
                    )
                    fig_dow.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        polar=dict(
                            bgcolor='rgba(255,255,255,0.02)',
                            radialaxis=dict(visible=False),
                            angularaxis=dict(
                                color=ThemeManager.current.colors.text_secondary,
                                rotation=90, direction="clockwise"
                            )
                        ),
                        font=dict(color=ThemeManager.current.colors.text_primary),
                        height=250,
                        margin=dict(t=40, b=20, l=40, r=40)
                    )
                    st.plotly_chart(fig_dow, use_container_width=True, config={'displayModeBar': False})
                    
                    # Insight Text
                    peak_day = df_dow.loc[df_dow['cnt'].idxmax()]
                    st.caption(f"💡 주로 **{peak_day['day_name']}요일**에 산행이 집중되어 있습니다.")
                else:
                    st.info("데이터 부족")
            except Exception as e:
                st.error(f"DOW Chart Error: {e}")

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
