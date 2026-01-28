import streamlit as st
import duckdb
import pandas as pd
import os
import google.generativeai as genai
import streamlit_authenticator as stauth
import plotly.express as px
import importlib.metadata
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests

# =========================================================
# 1. App Configuration (설정 관리)
# =========================================================
class Config:
    load_dotenv()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    KST = timezone(timedelta(hours=9))
    DB_NAME = 'ddodak.duckdb' # Docker 컨테이너 내에서는 /app/ddodak.duckdb 또는 로컬 경로 매핑 사용
    RULES_URL = "https://www.band.us/band/85157163/post/4765" # 실제 회칙 링크 입력
    
    CREDENTIALS = {
        "usernames": {
            "ddodak_admin": {
                "name": "또닥 운영진",
                "password": "$2b$12$26eJr8zlp73HWwLlP7xbAeArmA844B0iRAc39VanX.7ezIZ/abbiq"
            }
        }
    }

# =========================================================
# 2. Service Layer (데이터베이스 및 AI 서비스)
# =========================================================
class DBService:
    @staticmethod
    def query(sql, params=None):
        with duckdb.connect(Config.DB_NAME) as conn:
            return conn.execute(sql, params).df() if params else conn.execute(sql).df()

    @staticmethod
    def execute(sql, params=None):
        with duckdb.connect(Config.DB_NAME) as conn:
            if params:
                conn.execute(sql, params)
            else:
                conn.execute(sql)
            return None
class AIService:
    def __init__(self):
        self.model = self._setup_model()
        self.model_name = "None"

    def _setup_model(self):
        if not Config.GEMINI_API_KEY: return None
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            models = genai.list_models()
            text_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            target = "models/gemini-1.5-flash"
            self.model_name = target if target in text_models else text_models[0]
            return genai.GenerativeModel(self.model_name)
        except: return None

    def get_briefing(self, df):
        if not self.model: return "AI 서비스가 연결되지 않았습니다."
        prompt = f"산악회 회원 데이터 분석 후 MVP 칭찬과 격려 메시지를 작성해줘: {df.to_json()}"
        return self.model.generate_content(prompt).text

# =========================================================
# 3. UI Layer (컴포넌트 기반 렌더링)
# =========================================================
class UIRenderer:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    def render_sidebar(self):
        with st.sidebar:
            st.title("⛰️ 또닥 산악회")
            try: ver = importlib.metadata.version("google-generativeai")
            except: ver = "Unknown"
            st.caption(f"🛠️ Lib: v{ver} | 🤖 AI: {self.ai.model_name}")
            st.divider()
            return st.radio("메뉴 이동", ["🏠 홈", "👥 회원 관리", "📅 산행 일정", "🏃 참가 체크", "📊 보고서 생성"])

    # --- Helper: Page Manuals ---
    def render_manual(self, page):
        with st.expander(f"📖 {page} 페이지 이용 가이드", expanded=False):
            if page == "홈":
                st.markdown("""
                - **대시보드**: 전체 회원 수, 이달의 활동 점수 등 핵심 지표를 한눈에 확인하세요.
                - **다가오는 산행**: 가장 가까운 일정(3개)과 디데이, 서울 주간 날씨를 제공합니다.
                - **명예의 전당**: 이달의 공지왕, 참석왕(획득점수 순), 인기 산행 랭킹을 볼 수 있습니다.
                - **회원 통계**: 기수별 인원 및 성별 분포를 시각적으로 분석합니다.
                """)
            elif page == "회원 관리":
                st.markdown("""
                - **회원 검색**: 이름, 전화번호, 닉네임 등으로 회원을 빠르게 찾을 수 있습니다.
                - **회원 추가**: **테이블 우측 상단의 ➕ 아이콘**을 누르거나, **맨 아래의 빈 행**을 클릭하여 직접 입력하세요.
                - **수정/삭제**: 목록에서 내용을 직접 수정하거나, 행을 선택하여 삭제할 수 있습니다.
                """)
            elif page == "산행 일정":
                st.markdown("""
                - **일정 확인**: 달력(Calendar)보기와 리스트 보기를 지원합니다.
                - **일정 등록**: **테이블 우측 상단의 ➕ 아이콘**을 누르거나, **맨 아래의 빈 행**을 클릭하여 추가하세요.
                - **설정**: 날짜, 산 이름, 담당자 등을 입력하면 D-Day가 자동 계산됩니다.
                """)
            elif page == "참가 체크":
                st.markdown("""
                - **출석부**: 진행된 산행을 선택하고 참가자를 체크합니다.
                - **점수 자동 부여**: 참석 체크 시 활동 점수가 자동으로 누적됩니다.
                - **게스트 관리**: 비회원(게스트) 참가자도 별도로 기록할 수 있습니다.
                """)
            elif page == "보고서 생성":
                st.markdown("""
                - **엑셀 다운로드**: 전체 회원 명부나 산행 기록을 엑셀 파일로 저장합니다.
                - **월간/연간 보고**: 특정 기간의 활동 내역을 요약하여 보고서 형태로 출력합니다.
                """)
            st.caption("💡 팁: 화면이 좁다면 사이드바를 닫고 넓게 보실 수 있습니다.")

    def set_background(self):
        import base64
        try:
            with open("background.png", "rb") as f:
                data = f.read()
            bin_str = base64.b64encode(data).decode()
            page_bg_img = f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.85)), url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
            }}
            </style>
            """
            st.markdown(page_bg_img, unsafe_allow_html=True)
        except Exception as e:
            print(f"Background image not found: {e}")

    def view_home(self):
        self.set_background()
        self.render_manual("홈")
        st.title("⛰️ 또닥또닥 산악회")
        
        # [Dashboard Layout]
        # Tabbed layout for better organization
        tab_overview, tab_demo, tab_activity = st.tabs(["📊 대시보드 (Overview)", "👥 회원 구성 (Demographics)", "🏆 명예의 전당 (Hall of Fame)"])
        
        # --- TAB 1: OVERVIEW ---
        with tab_overview:
            # 1. Headline Metrics (Card Style)
            total_members = self.db.query("SELECT COUNT(*) FROM members WHERE role<>'exmember'").iloc[0, 0]
            # Calculate total points
            df_points = self.db.query("SELECT user_no, point FROM members WHERE role<>'exmember'")
            total_base = df_points['point'].sum() if not df_points.empty else 0
            event_score = self.db.query("SELECT SUM(e.score) FROM events e JOIN attendees a ON e.event_id = a.event_id").iloc[0,0]
            if pd.isna(event_score): event_score = 0
            total_activity_score = total_base + event_score
            
            # Count active members (attended within 3 months) for "Active" metric
            three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            active_count = self.db.query(f"SELECT COUNT(DISTINCT user_no) FROM attendees a JOIN events e ON a.event_id = e.event_id WHERE e.date >= '{three_months_ago}'").iloc[0,0]

            # Custom Card CSS
            card_style = "background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: white; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;"
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div style="{card_style}">
                    <div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">총 회원수</div>
                    <div style="font-size: 32px; font-weight: bold;">{total_members}명</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="{card_style}">
                    <div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">최근 활동 회원</div>
                    <div style="font-size: 32px; font-weight: bold; color: #4ade80;">{active_count}명</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div style="{card_style}">
                    <div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">누적 활동 점수</div>
                    <div style="font-size: 32px; font-weight: bold; color: #ffd700;">{int(total_activity_score):,}점</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 2. Upcoming Events & Weather (Card Style)
            c3, c4 = st.columns([1.2, 1])
            
            with c3:
                # Wrap Events in Card
                st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
                st.subheader("📅 다가오는 산행")
                today = datetime.now().strftime("%Y-%m-%d")
                upcoming = self.db.query(f"SELECT * FROM events WHERE date >= '{today}' ORDER BY date ASC LIMIT 3")
                
                if not upcoming.empty:
                    for _, row in upcoming.iterrows():
                        d_day = (pd.to_datetime(row['date']) - pd.to_datetime(today)).days
                        badge = f"D-{d_day}" if d_day > 0 else "D-Day"
                        badge_color = "#ef4444" if d_day <= 3 else "#3b82f6"
                        
                        st.markdown(f"""
                        <div style="background-color: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {badge_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-weight: bold; font-size: 16px; color: #fff;">{row['title']}</div>
                                <div style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{badge}</div>
                            </div>
                            <div style="color: #ccc; font-size: 13px; margin-top: 4px;">📅 {row['date']} &nbsp;|&nbsp; 👑 {row['host']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("예정된 산행이 없습니다.")
                st.markdown("</div>", unsafe_allow_html=True)

            with c4:
                # Wrap Weather in Card
                st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
                st.subheader("🌤️ 서울 날씨")
                self.render_weather_forecast()
                st.markdown("</div>", unsafe_allow_html=True)

            # AI Briefing Section
            st.markdown("---")
            st.subheader("🤖 AI 주간 브리핑")
            if st.button("✨ 이번 주 산행 & 날씨 브리핑 생성"):
                check_events = self.db.query(f"SELECT * FROM events WHERE date >= '{today}' LIMIT 1")
                if check_events.empty:
                    st.warning("예정된 산행 데이터가 없어 브리핑을 생성할 수 없습니다.")
                else:
                    self.show_ai_briefing(upcoming)


        # --- TAB 2: DEMOGRAPHICS ---
        with tab_demo:
            c3, c4 = st.columns(2)
            df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")
            
            # 1. Age Composition (Circles with Gender Split)
            with c3:
                st.markdown("### 📅 연도별 인원 (Birth Year)")
                # Visual Legend
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
                    # Data Processing
                    # Normalizing gender first
                    df_dist['gender_norm'] = df_dist['gender'].astype(str).str.upper().str.strip()
                    gender_map = {'M': 'M', 'MALE': 'M', 'MAN': 'M', '남': 'M', '남성': 'M', 'F': 'F', 'FEMALE': 'F', 'WOMAN': 'F', 'W': 'F', '여': 'F', '여성': 'F'}
                    df_dist['gender_final'] = df_dist['gender_norm'].map(gender_map).fillna('U')
                    
                    # Group by year and gender
                    age_gender = df_dist.groupby(['birth_year', 'gender_final']).size().unstack(fill_value=0)
                    
                    # Ensure columns exist
                    if 'M' not in age_gender.columns: age_gender['M'] = 0
                    if 'F' not in age_gender.columns: age_gender['F'] = 0
                    
                    age_gender['total'] = age_gender.sum(axis=1)
                    age_gender = age_gender.sort_index()

                    # Max count for scaling size
                    max_count = age_gender['total'].max()
                    
                    # HTML Generation
                    html_balls = '<div style="background-color: rgba(0,0,0,0.5); padding: 15px; border-radius: 10px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: center;">'
                    for year, row in age_gender.iterrows():
                        year = int(year)
                        count = int(row['total'])
                        m_count = int(row['M'])
                        f_count = int(row['F'])
                        
                        # Calculate percentage for gradient split
                        m_pct = (m_count / count * 100) if count > 0 else 0
                        # Hard stop gradient for split effect
                        bg_style = f"background: linear-gradient(135deg, #3b82f6 {m_pct}%, #ec4899 {m_pct}%);"
                        
                        # Size calculation
                        size = 50 + (count / max_count) * 50 if max_count > 0 else 50
                        font_size = 14 + (count / max_count) * 6
                        
                        html_balls += f"""<div style="width: {size}px; height: {size}px; border-radius: 50%; {bg_style} color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s; border: 2px solid rgba(255,255,255,0.2);" title="{year}년생: {count}명 (남:{m_count}/여:{f_count})"><span style="font-weight: bold; font-size: {font_size}px; line-height: 1; text-shadow: 1px 1px 2px black;">{year}년</span><span style="font-size: {font_size*0.7}px; opacity: 0.9; text-shadow: 1px 1px 2px black;">{count}명</span></div>"""
                    html_balls += '</div>'
                    st.markdown(html_balls, unsafe_allow_html=True)

            # 2. Gender Composition (Icons)
            with c4:
                st.subheader("🚻 성별 분포 (Gender)")
                if not df_dist.empty:
                    gender_counts = df_dist['gender_final'].value_counts()
                    total = len(df_dist)
                                        
                    m_count, f_count, u_count = gender_counts.get('M', 0), gender_counts.get('F', 0), gender_counts.get('U', 0)
                    m_pct = (m_count / total * 100) if total > 0 else 0
                    f_pct = (f_count / total * 100) if total > 0 else 0
                    u_pct = (u_count / total * 100) if total > 0 else 0
                    
                    if u_count > 0:
                        html_gender = f"""<div style="background-color: rgba(0,0,0,0.5); border-radius: 10px; display: flex; justify-content: space-around; align-items: center; height: 100%; padding: 20px 0;"><div style="text-align: center;"><div style="font-size: 60px; color: #3b82f6;">♂️</div><div style="font-size: 18px; font-weight: bold; color: #eee;">남성</div><div style="font-size: 14px; color: #ccc;">{m_count}명 ({m_pct:.1f}%)</div></div><div style="width: 1px; height: 80px; background-color: #555;"></div><div style="text-align: center;"><div style="font-size: 60px; color: #ec4899;">♀️</div><div style="font-size: 18px; font-weight: bold; color: #eee;">여성</div><div style="font-size: 14px; color: #ccc;">{f_count}명 ({f_pct:.1f}%)</div></div><div style="width: 1px; height: 80px; background-color: #555;"></div><div style="text-align: center;"><div style="font-size: 60px; color: #9ca3af;">❓</div><div style="font-size: 18px; font-weight: bold; color: #eee;">미상</div><div style="font-size: 14px; color: #ccc;">{u_count}명 ({u_pct:.1f}%)</div></div></div>"""
                    else:
                        html_gender = f"""<div style="background-color: rgba(0,0,0,0.5); border-radius: 10px; display: flex; justify-content: space-around; align-items: center; height: 100%; padding: 20px 0;"><div style="text-align: center;"><div style="font-size: 80px; color: #3b82f6;">♂️</div><div style="font-size: 24px; font-weight: bold; color: #eee;">남성</div><div style="font-size: 18px; color: #ccc;">{m_count}명 ({m_pct:.1f}%)</div></div><div style="width: 2px; height: 100px; background-color: #555;"></div><div style="text-align: center;"><div style="font-size: 80px; color: #ec4899;">♀️</div><div style="font-size: 24px; font-weight: bold; color: #eee;">여성</div><div style="font-size: 18px; color: #ccc;">{f_count}명 ({f_pct:.1f}%)</div></div></div>"""
                    
                    st.markdown(html_gender, unsafe_allow_html=True)
            
            st.divider()
            
            c1, c2 = st.columns(2)
            # [Map Visualization]
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
            
            with c1: 
                fig_map = px.scatter_mapbox(
                    df_map, lat="lat", lon="lon", size="count", color="count",
                    hover_name="area", size_max=25, zoom=8, 
                    center={"lat": 37.5, "lon": 127.0},
                    title='📍 지역 분포 (서울/경기)',
                    mapbox_style="open-street-map", height=400
                )
                fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
                
            # [NEW] Top Regions Bar Chart
            with c2:
                st.subheader("🏙️ Top 5 활동 지역")
                top_regions = df_map.head(5)
                max_reg = top_regions['count'].max()
                
                bar_html = "<div style='background-color: rgba(0,0,0,0.5); border-radius: 10px; padding: 15px;'>"
                for _, row in top_regions.iterrows():
                    pct = (row['count'] / max_reg) * 100
                    bar_html += f"""<div style="margin-bottom: 12px;"><div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="font-weight: bold; color: #eee;">{row['area']}</span><span style="font-weight: bold; color: #4da6ff;">{row['count']}명</span></div><div style="width: 100%; background-color: #444; border-radius: 6px; height: 12px;"><div style="width: {pct}%; background: linear-gradient(90deg, #2575fc, #6a11cb); height: 100%; border-radius: 6px;"></div></div></div>"""
                bar_html += "</div>"
                st.markdown(bar_html, unsafe_allow_html=True)


        # --- TAB 3: ACTIVITY (HALL OF FAME) ---
        # --- TAB 3: MONTHLY ACTIVITY (HALL OF FAME) ---
        with tab_activity:
            now = datetime.now(Config.KST)
            cur_month_str = now.strftime('%Y-%m')
            st.subheader(f"🏆 {now.month}월의 명예의 전당")
            
            c_host, c_attend, c_event = st.columns(3)
            
            # Helper for Rank Bubbles
            def get_rank_html(rank, text, subtext):
                colors = ["#FFD700", "#C0C0C0", "#CD7F32"] # Gold, Silver, Bronze
                color = colors[rank] if rank < 3 else "#FFFFFF"
                rank_num = rank + 1
                return f"""
                <div style="background-color: rgba(0,0,0,0.4); padding: 10px; border-radius: 8px; margin-bottom: 6px; display: flex; align-items: center;">
                    <div style="width: 30px; height: 30px; border-radius: 50%; background-color: {color}; color: #000; font-weight: bold; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0;">{rank_num}</div>
                    <div style="flex-grow: 1;"><b>{text}</b></div>
                    <div style="font-size: 14px; color: #eee;">{subtext}</div>
                </div>
                """

            # 1. Top Hosts (공지왕)
            with c_host:
                st.markdown("##### 📣 이달의 공지왕")
                try:
                    df_host = self.db.query(f"SELECT m.name, COUNT(*) as cnt FROM events e JOIN members m ON e.host = m.user_no WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' GROUP BY m.name ORDER BY cnt DESC LIMIT 3")
                    if not df_host.empty:
                        for idx, row in df_host.iterrows():
                            st.markdown(get_rank_html(idx, row['name'], f"{row['cnt']}회"), unsafe_allow_html=True)
                    else:
                        st.caption("데이터 없음")
                except Exception as e:
                    st.error(f"Error: {e}")

            # 2. Top Attendees (참석왕 - 획득점수 기준)
            with c_attend:
                st.markdown("##### 🏃 이달의 참석왕")
                try:
                    top_scorers = active_members.sort_values(by='획득점수', ascending=False).head(3)
                    if not top_scorers.empty:
                        for i in range(len(top_scorers)):
                            row = top_scorers.iloc[i]
                            st.markdown(get_rank_html(i, row['MemberID'], f"{int(row['획득점수'])}점"), unsafe_allow_html=True)
                    else:
                        st.caption("데이터 없음")
                except Exception as e:
                    st.error(f"Error: {e}")

            # 3. Most Popular Events (인기 산행)
            with c_event:
                st.markdown("##### 🔥 이달의 인기 산행")
                try:
                    df_pop = self.db.query(f"SELECT e.title, COUNT(a.user_no) as cnt FROM events e JOIN attendees a ON e.event_id = a.event_id WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' GROUP BY e.title ORDER BY cnt DESC LIMIT 3")
                    if not df_pop.empty:
                        for idx, row in df_pop.iterrows():
                            st.markdown(get_rank_html(idx, row['title'], f"{row['cnt']}명"), unsafe_allow_html=True)
                    else:
                        st.caption("데이터 없음")
                except Exception as e:
                    st.error(f"Error: {e}")
            
            st.divider()
            st.plotly_chart(px.bar(df_summary, x='생년', y='현재포인트', color='회원상태', title='🎂 기수별 포인트 분포'), use_container_width=True)



    def view_members(self):
        self.render_manual("회원 관리")
        st.header("👥 회원 명부 관리")
        # 1. 원본 데이터 로드 (삭제 비교용)
        df_all = self.db.query("SELECT * FROM members ORDER BY birth_year, name")
        
        # [고급 필터 & 검색]
        # [고급 필터 & 검색]
        with st.expander("🔍 상세 검색 및 필터", expanded=True):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
            with c1: 
                years = sorted(df_all['birth_year'].dropna().unique())
                sel_years = st.multiselect("🎂 생년", years, placeholder="전체")
            with c2:
                areas = sorted(df_all['area'].dropna().unique())
                sel_areas = st.multiselect("📍 지역", areas, placeholder="전체")
            with c3:
                roles = sorted(df_all['role'].dropna().unique())
                sel_roles = st.multiselect("👑 역할", roles, placeholder="전체")
            with c4:
                search_name = st.text_input("👤 이름/설명 검색", placeholder="검색어 입력")

        # 필터링 로직 적용
        mask = pd.Series([True] * len(df_all))
        if sel_years: mask &= df_all['birth_year'].isin(sel_years)
        if sel_areas: mask &= df_all['area'].isin(sel_areas)
        if sel_roles: mask &= df_all['role'].isin(sel_roles)
        if search_name:
            mask &= (
                df_all['name'].str.contains(search_name, case=False, na=False) | 
                df_all['description'].str.contains(search_name, case=False, na=False)
            )
        
        df_filtered = df_all[mask]
        st.caption(f"검색 결과: **{len(df_filtered)}**명 (전체 {len(df_all)}명 중)")
        
        # [컬럼 순서 지정] 횡스크롤 시 이름까지라도 먼저 보이도록 강제
        target_order = ['birth_year', 'name', 'area', 'role', 'gender', 'user_no', 'phone', 'description', 'original_name', 'point', 'created_at', 'last_attended', 'profile_image_url']
        # 실제 데이터프레임에 있는 컬럼만 필터링 (동적 컬럼 대응)
        final_order = [c for c in target_order if c in df_filtered.columns] + [c for c in df_filtered.columns if c not in target_order]
        
        # 2. 데이터 에디터
        column_config = {
            "birth_year": st.column_config.NumberColumn("생년", format="%d", width="small"), # 너비 조정으로 가독성 확보
            "name": st.column_config.TextColumn("이름", width="medium"),
            "area": st.column_config.TextColumn("지역", width="small"),
            "role": st.column_config.SelectboxColumn("역할", options=['member', 'admin', 'staff', 'exmember'], width="small"),
            "user_no": st.column_config.TextColumn("ID", disabled=False), 
        }
        
        updated = st.data_editor(
            df_filtered, # 순서 처리는 column_order로
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic", 
            key="member_editor",
            column_config=column_config,
            column_order=final_order # 컬럼 순서 강제 적용
        )
        
        if st.button("💾 회원 정보 최종 저장"):
            with st.spinner("⏳ 회원 정보를 저장하고 있습니다..."):
                # [삭제 로직]
                orig_ids_in_view = set(df_filtered['user_no'].astype(str).tolist())
                curr_ids_in_view = set(updated['user_no'].astype(str).tolist())
                deleted_ids = orig_ids_in_view - curr_ids_in_view
                
                for d_id in deleted_ids:
                    self.db.execute("DELETE FROM members WHERE user_no = ?", (d_id,))
                
                # [저장/수정 로직]
                cols = ", ".join([f'"{c}"' for c in updated.columns])
                placeholders = ", ".join(["?"] * len(updated.columns))
                sql = f"INSERT OR REPLACE INTO members ({cols}) VALUES ({placeholders})"
                for _, row in updated.iterrows():
                    self.db.execute(sql, tuple(row))
                
                import time
                time.sleep(0.5)
                
                st.success(f"""
                ✅ **작업 완료!**
                - 💾 **저장/수정**: {len(updated)}건
                - 🗑️ **삭제**: {len(deleted_ids)}건
                """)
                st.rerun()

    def view_events(self):
        self.render_manual("산행 일정")
        st.header("📅 산행 일정 관리")
        # 1. 원본 데이터 로드
        df_e = self.db.query("SELECT * FROM events ORDER BY date DESC")
        
        
        # [고급 필터]
        with st.expander("🔍 일정 검색 및 필터", expanded=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                # [월별 필터 (YYYY-MM) - 내림차순]
                df_e['month'] = df_e['date'].astype(str).str[:7]
                months = sorted(df_e['month'].unique(), reverse=True)
                sel_month = st.selectbox("📅 월 선택", ["전체"] + months)
            with c2:
                search_text = st.text_input("📝 제목 검색", placeholder="일정 제목")

        mask = pd.Series([True] * len(df_e))
        if sel_month != "전체":
            mask &= (df_e['month'] == sel_month)
        if search_text:
            mask &= df_e['title'].str.contains(search_text, case=False, na=False)
            
        df_filtered = df_e[mask]
        st.subheader(f"🗓️ 등록된 일정 (표시: {len(df_filtered)} / 전체: {len(df_e)}건)")
        
        # [컬럼 재정렬] Date, Title, Host 우선
        target_order = ['date', 'title', 'host', 'event_id', 'album_url', 'description']
        final_order = [c for c in target_order if c in df_filtered.columns] + [c for c in df_filtered.columns if c not in target_order]

        column_config = {
            "date": st.column_config.DateColumn("행사일", format="YYYY-MM-DD", width="medium"),
            "title": st.column_config.TextColumn("일정명", width="large"),
            "event_id": st.column_config.TextColumn("ID", disabled=True),
        }
        
        updated = st.data_editor(
            df_filtered, 
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic", 
            key="event_editor",
            column_config=column_config,
            column_order=final_order # 컬럼 순서 강제 적용
        )
        
        if st.button("💾 일정 최종 저장"):
            with st.spinner("⏳ 일정을 저장하고 있습니다..."):
                # [삭제 로직]
                orig_ids_in_view = set(df_filtered['event_id'].astype(str).tolist())
                curr_ids_in_view = set(updated['event_id'].astype(str).tolist())
                deleted_ids = orig_ids_in_view - curr_ids_in_view
                
                for d_id in deleted_ids:
                    self.db.execute("DELETE FROM events WHERE event_id = ?", (d_id,))
                    self.db.execute("DELETE FROM attendees WHERE event_id = ?", (d_id,))
                
                # [저장/수정 로직]
                cols = ", ".join([f'"{c}"' for c in updated.columns])
                placeholders = ", ".join(["?"] * len(updated.columns))
                sql = f"INSERT OR REPLACE INTO events ({cols}) VALUES ({placeholders})"
                for _, row in updated.iterrows():
                    self.db.execute(sql, tuple(row))
                    
                import time
                time.sleep(0.5)
                
                st.success(f"""
                ✅ **일정 반영 완료!**
                - 💾 **저장/수정**: {len(updated)}건
                - 🗑️ **삭제**: {len(deleted_ids)}건
                """)
                st.rerun()

    def view_attendance(self):
        self.render_manual("참가 체크")
        st.header("🏃 참석자 명단 체크")
        ev_list = self.db.query("SELECT event_id, date, title, host FROM events ORDER BY date DESC")
        mb_list = self.db.query("SELECT user_no, birth_year, name, area FROM members WHERE role<>'exmember' ORDER BY birth_year, name")
        
        if ev_list.empty: return st.warning("일정을 먼저 등록하세요.")
        ev_labels = ev_list.apply(lambda r: f"{r['date']} | {r['title']}", axis=1).tolist()
        sel_label = st.selectbox(f"🎯 산행 선택 (총 {len(ev_list)}건)", ev_labels)
        
        selected_event = ev_list.iloc[ev_labels.index(sel_label)]
        sel_ev_id = selected_event['event_id']
        host_id = str(selected_event['host']) if selected_event['host'] else None
        
        existing = self.db.query("SELECT user_no FROM attendees WHERE event_id=?", (str(sel_ev_id),))['user_no'].tolist()
        
        # 명단 포맷팅 (텍스트 추가 없이 깔끔하게)
        mb_list['display'] = mb_list.apply(lambda r: f"{r['birth_year']}/{r['name']}/{r['area']}", axis=1)
        
        # 공지자(Host) 정보 색상 강조 표시
        host_name = "미지정"
        if host_id:
            host_row = mb_list[mb_list['user_no'].astype(str) == host_id]
            if not host_row.empty:
                host_name = host_row['display'].iloc[0]
                st.markdown(f"👑 **공지자**: :orange[{host_name}]")
        
        # key에 event_id를 포함시켜 선택 변경 시 컴포넌트 강제 리셋 (이전 선택 클리어)
        selected = st.multiselect(
            f"🏃 참석자 선택 (대상: {len(mb_list)}명)", 
            options=mb_list['display'].tolist(),
            default=mb_list[mb_list['user_no'].isin(existing)]['display'].tolist(),
            key=f"attendees_{sel_ev_id}" 
        )
        
        st.info(f"💡 현재 선택된 인원: **{len(selected)}명**")
        if st.button("✅ 참석 명단 최종 확정", type="primary"):
            with st.spinner("⏳ 참석 명단을 업데이트 중입니다..."):
                self.db.execute("DELETE FROM attendees WHERE event_id=?", (str(sel_ev_id),))
                for val in selected:
                    u_no = mb_list.loc[mb_list['display'] == val, 'user_no'].iloc[0]
                    self.db.execute("INSERT INTO attendees (event_id, user_no) VALUES (?, ?)", (str(sel_ev_id), u_no))
                
                import time
                time.sleep(0.5)
                
                st.success(f"""
                ✅ **참석 정보 저장 완료!**
                - 🏃 **최종 참석 인원**: {len(selected)}명
                """)
                st.rerun()

    def view_report(self):
        self.render_manual("보고서 생성")
        st.header("📊 활동 결과 보고서")
        col1, col2 = st.columns([2, 1])
        with col1: rules = st.text_input("🔗 회칙 링크", value=Config.RULES_URL)
        with col2: target_month = st.text_input("📅 대상 월 (YYYY-MM)", value=datetime.now(Config.KST).strftime('%Y-%m'))
        
        if st.button("📝 보고서 생성", type="primary", use_container_width=True):
            df_ev = self.db.query(f"SELECT e.date, e.title, e.album_url, m.birth_year, m.name FROM events e JOIN attendees a ON e.event_id=a.event_id JOIN members m ON a.user_no=m.user_no WHERE strftime('%Y-%m', e.date)='{target_month}' ORDER BY e.date, m.birth_year, m.name")
            df_rep = self.db.query("SELECT * FROM v_member_attendance_summary ORDER BY MemberID ASC")
            
            # [NaN 처리]
            df_rep['획득점수'] = df_rep['획득점수'].fillna(0).astype(int)
            df_rep['현재포인트'] = df_rep['현재포인트'].fillna(0).astype(int)

            # [줄 바꿈 규칙 적용: 문장 끝에 스페이스 2개 추가]
            sp = "  " # 마크다운 하드 브레이크용 스페이스 2개
            report = f"🔗 **또닥또닥 회칙 안내**{sp}\n{rules}{sp}\n\n"
            report += f"⛰️ **{target_month} 활동 요약 보고서**{sp}\n────────────────{sp}\n\n"
            
            report += f"📅 **[이달의 산행 기록]**{sp}\n"
            if not df_ev.empty:
                for (d, t), g in df_ev.groupby(['date', 'title'], sort=False):
                    report += f"📍 {d} | {t}{sp}\n└ 참석({len(g)}명): {', '.join(g['name'].tolist())}{sp}\n"
                    if g['album_url'].iloc[0]: report += f"└ 📸 사진첩: {g['album_url'].iloc[0]}{sp}\n"
                    report += f"\n"
            else: report += f"활동 내역 없음{sp}\n\n"
            
            # 시상 로직
            winners = []
            for _, r in df_rep.iterrows():
                curr, prev = r['현재포인트'], r['현재포인트'] - r['획득점수']
                for th, msg in [(100, "💯 특별시상"), (50, "🎫 50점 돌파"), (30, "🎫 30점 돌파"), (10, "🎫 10점 돌파")]:
                    if curr >= th and prev < th: winners.append(f"✨ {r['MemberID']} ({curr}점) {msg}")
            
            report += f"🏆 **[이달의 시상 현황]**{sp}\n" + (f"{sp}\n".join(winners) if winners else "해당사항 없음") + f"{sp}\n\n"
            
            # 4. [복구] 활동 관리 안내 (경고 목록)
            # v_member_attendance_summary의 회원상태에서 아이콘을 필터링합니다.
            sleep_warning = df_rep[df_rep['회원상태'].str.contains('😴🚨', na=False)]['MemberID'].tolist()
            new_warning = df_rep[df_rep['회원상태'].str.contains('🌱🚨', na=False)]['MemberID'].tolist()
            
            report += f"🚨 **[활동 관리 안내]**{sp}\n"
            report += f"😴 **장기 미참석(경고)**:  \n{', '.join(sleep_warning) if sleep_warning else '없음'}{sp}\n"
            report += f"🌱 **신입 미참석(경고)**:  \n{', '.join(new_warning) if new_warning else '없음'}{sp}\n\n"

            # 테이블 형식
            report += f"🔢 **[전체 회원 누적 점수 현황]**{sp}\n"
            report += f"| 회원명 | 이번달 점수 | 누적 점수 | 상태 |{sp}\n"
            report += f"| :--- | ---: | ---: | :---: |{sp}\n"
            for _, r in df_rep[df_rep['회원상태'] != 'exmember'].iterrows():
                report += f"| {r['MemberID']} | {r['획득점수']}점 | {r['현재포인트']}점 | {r['회원상태']} |{sp}\n"
            
            report += f"\n────────────────{sp}\n건강하게 다음 산행에서 뵙겠습니다! ⛰️"
            
            t1, t2 = st.tabs(["📋 밴드 복사용", "👀 미리보기"])
            with t1: st.code(report.replace("**", ""), language="text")
            with t2: st.markdown(report)

# =========================================================
# 4. Main Controller (진입점)
# =========================================================
def main():
    auth = stauth.Authenticate(Config.CREDENTIALS, "ddodak_cookie", "ddodak_key")
    auth.login(location='main')

    if st.session_state["authentication_status"]:
        db, ai = DBService(), AIService()
        ui = UIRenderer(db, ai)
        choice = ui.render_sidebar()
        
        if choice == "🏠 홈": ui.view_home()
        elif choice == "👥 회원 관리": ui.view_members()
        elif choice == "📅 산행 일정": ui.view_events()
        elif choice == "🏃 참가 체크": ui.view_attendance()
        elif choice == "📊 보고서 생성": ui.view_report()
            
    elif st.session_state["authentication_status"] is False:
        st.error("인증 실패")

if __name__ == "__main__":
    main()