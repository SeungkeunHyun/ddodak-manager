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
    DB_NAME = 'ddodak.duckdb'
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
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_summary, names='지역', title='📍 지역분포', hole=0.3), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df_summary, x='생년', y='현재포인트', color='회원상태', title='🎂 기수별 포인트'), use_container_width=True)
        
        c3, c4 = st.columns(2)
        df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")
        with c3: st.plotly_chart(px.histogram(df_dist, x='birth_year', title='📅 연도별 인원', text_auto=True), use_container_width=True)
        with c4: st.plotly_chart(px.pie(df_dist, names='gender', title='🚻 성별 분포', hole=0.3), use_container_width=True)

    def view_members(self):
        st.header("👥 회원 명부 관리")
        # 1. 원본 데이터 로드 (삭제 비교용)
        df_all = self.db.query("SELECT * FROM members ORDER BY birth_year, name")
        st.subheader(f"📋 회원 목록 (전체: {len(df_all)}명)")
        
        # 2. 데이터 에디터 (삭제 가능하도록 설정)
        updated = st.data_editor(df_all, use_container_width=True, hide_index=True, num_rows="dynamic", key="member_editor")
        
        if st.button("💾 회원 정보 최종 저장"):
            # [삭제 로직] 원본에는 있었는데 수정본에는 없는 user_no를 찾아 삭제
            orig_ids = set(df_all['user_no'].astype(str).tolist())
            curr_ids = set(updated['user_no'].astype(str).tolist())
            deleted_ids = orig_ids - curr_ids
            
            for d_id in deleted_ids:
                self.db.execute("DELETE FROM members WHERE user_no = ?", (d_id,))
            
            # [저장/수정 로직]
            cols = ", ".join([f'"{c}"' for c in updated.columns])
            placeholders = ", ".join(["?"] * len(updated.columns))
            sql = f"INSERT OR REPLACE INTO members ({cols}) VALUES ({placeholders})"
            for _, row in updated.iterrows():
                self.db.execute(sql, tuple(row))
                
            st.success(f"변경사항 반영 완료! (저장: {len(updated)}건 / 삭제: {len(deleted_ids)}건)")
            st.rerun()

    def view_events(self):
        st.header("📅 산행 일정 관리")
        # 1. 원본 데이터 로드
        df_e = self.db.query("SELECT * FROM events ORDER BY date DESC")
        st.subheader(f"🗓️ 등록된 일정 (총 {len(df_e)}건)")
        
        # 2. 데이터 에디터
        updated = st.data_editor(df_e, use_container_width=True, hide_index=True, num_rows="dynamic", key="event_editor")
        
        if st.button("💾 일정 최종 저장"):
            # [삭제 로직]
            orig_ids = set(df_e['event_id'].astype(str).tolist())
            curr_ids = set(updated['event_id'].astype(str).tolist())
            deleted_ids = orig_ids - curr_ids
            
            for d_id in deleted_ids:
                self.db.execute("DELETE FROM events WHERE event_id = ?", (d_id,))
                # 일정 삭제 시 참석자 테이블도 함께 정리 (Cascading 효과)
                self.db.execute("DELETE FROM attendees WHERE event_id = ?", (d_id,))
            
            # [저장/수정 로직]
            cols = ", ".join([f'"{c}"' for c in updated.columns])
            placeholders = ", ".join(["?"] * len(updated.columns))
            sql = f"INSERT OR REPLACE INTO events ({cols}) VALUES ({placeholders})"
            for _, row in updated.iterrows():
                self.db.execute(sql, tuple(row))
                
            st.success(f"일정 반영 완료! (저장: {len(updated)}건 / 삭제: {len(deleted_ids)}건)")
            st.rerun()

    def view_attendance(self):
        st.header("🏃 참석자 명단 체크")
        ev_list = self.db.query("SELECT event_id, date, title FROM events ORDER BY date DESC")
        mb_list = self.db.query("SELECT user_no, birth_year, name, area FROM members WHERE role<>'exmember' ORDER BY birth_year, name")
        
        if ev_list.empty: return st.warning("일정을 먼저 등록하세요.")
        ev_labels = ev_list.apply(lambda r: f"{r['date']} | {r['title']}", axis=1).tolist()
        sel_label = st.selectbox(f"🎯 산행 선택 (총 {len(ev_list)}건)", ev_labels)
        sel_ev_id = ev_list.iloc[ev_labels.index(sel_label)]['event_id']
        
        existing = self.db.query("SELECT user_no FROM attendees WHERE event_id=?", (str(sel_ev_id),))['user_no'].tolist()
        mb_list['display'] = mb_list.apply(lambda r: f"{r['birth_year']}/{r['name']}/{r['area']}", axis=1)
        
        selected = st.multiselect(f"🏃 참석자 선택 (대상: {len(mb_list)}명)", options=mb_list['display'].tolist(),
                                  default=mb_list[mb_list['user_no'].isin(existing)]['display'].tolist())
        
        st.info(f"💡 현재 선택된 인원: **{len(selected)}명**")
        if st.button("✅ 참석 명단 최종 확정", type="primary"):
            self.db.execute("DELETE FROM attendees WHERE event_id=?", (str(sel_ev_id),))
            for val in selected:
                u_no = mb_list.loc[mb_list['display'] == val, 'user_no'].iloc[0]
                self.db.execute("INSERT INTO attendees (event_id, user_no) VALUES (?, ?)", (str(sel_ev_id), u_no))
            st.success("참석 정보 저장 완료!")
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