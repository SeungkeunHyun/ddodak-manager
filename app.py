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

    def view_home(self):
        st.title("🏔️ 운영 대시보드")
        df_summary = self.db.query("SELECT * FROM v_member_attendance_summary")
        active_members = df_summary[df_summary['회원상태'] != 'exmember']
        
        m1, m2, m3 = st.columns(3)
        m1.metric("전체 회원", f"{len(active_members)}명")
        m2.metric("이달의 열정 합계", f"{int(df_summary['획득점수'].sum())}점")
        m3.metric("🚨 관리 대상", f"{len(df_summary[df_summary['회원상태'].str.contains('🚨')])}명")

        if self.ai.model:
            with st.expander("✨ AI 산악회 비서 브리핑", expanded=True):
                if st.button("🔍 데이터 분석 실행", use_container_width=True):
                    st.write(self.ai.get_briefing(df_summary))

        st.divider()
        st.divider()
        c1, c2 = st.columns(2)
        
        # [지도 시각화] 좌표계 및 설정
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
                hover_name="area", size_max=25, 
                zoom=8, # 경기도 전체가 보이도록 축소
                center={"lat": 37.5, "lon": 127.0}, # 서울/경기 중심
                title='📍 지역 분포 (서울/경기)',
                mapbox_style="open-street-map", # 한글 지명을 위해 OSM 스타일 사용
                height=400 # 지도 파악을 위해 높이 약간 확보
            )
            # 마진 조정
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            
        with c2: st.plotly_chart(px.bar(df_summary, x='생년', y='현재포인트', color='회원상태', title='🎂 기수별 포인트'), use_container_width=True)
        
        c3, c4 = st.columns(2)
        df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")
        with c3: st.plotly_chart(px.histogram(df_dist, x='birth_year', title='📅 연도별 인원', text_auto=True), use_container_width=True)
        with c4: st.plotly_chart(px.pie(df_dist, names='gender', title='🚻 성별 분포', hole=0.3), use_container_width=True)

    def view_members(self):
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
            "user_no": st.column_config.TextColumn("ID", disabled=True), 
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