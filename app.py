import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit_authenticator as stauth
import plotly.express as px  
import google.generativeai as genai
import importlib.metadata
import os
from dotenv import load_dotenv

# =========================================================
# 🔑 [설정] API 키 및 환경 설정
# =========================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    lib_version = importlib.metadata.version("google-generativeai")
except:
    lib_version = "알 수 없음"

ai_model = None
selected_model = "대기 중..."

if GEMINI_API_KEY and GEMINI_API_KEY.startswith("AI"):
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        models = genai.list_models()
        text_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        if 'models/gemini-1.5-flash' in text_models:
            selected_model = "gemini-1.5-flash"
        elif 'models/gemini-pro' in text_models:
            selected_model = "gemini-pro"
        elif text_models:
            selected_model = text_models[0].replace('models/', '')
        else:
            selected_model = "gemini-1.5-flash"
            
        ai_model = genai.GenerativeModel(selected_model)
    except Exception as e:
        st.sidebar.error(f"⚠️ AI 로드 오류: {e}")
        ai_model = None

KST = timezone(timedelta(hours=9))

credentials = {
    "usernames": {
        "ddodak_admin": {
            "name": "또닥 운영진",
            "password": "$2b$12$26eJr8zlp73HWwLlP7xbAeArmA844B0iRAc39VanX.7ezIZ/abbiq" 
        }
    }
}

def get_db_connection():
    return duckdb.connect('ddodak.duckdb', read_only=False)

# =========================================================
# 🚀 앱 시작 및 인증
# =========================================================
st.set_page_config(page_title="또닥또닥 산악회 관리시스템", layout="wide", page_icon="⛰️")

authenticator = stauth.Authenticate(credentials, "ddodak_cookie", "ddodak_key", cookie_expiry_days=30)
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    with st.sidebar:
        if not GEMINI_API_KEY:
            st.error("❌ API 키를 찾을 수 없습니다.")
        else:
            st.caption("🔑 API 키 로드 완료")
        st.title("⛰️ 또닥또닥 산악회")
        authenticator.logout('로그아웃', 'sidebar')
        st.write(f"반갑습니다, **{st.session_state['name']}**님!")
        st.divider()
        st.caption(f"🛠️ Lib: v{lib_version} | 🤖 AI: {selected_model}")
        st.divider()
        menu_options = ["🏠 홈", "👥 회원 관리", "📅 산행 일정", "🏃 참가 체크", "📊 보고서 생성"]
        choice = st.sidebar.radio("메뉴 이동", menu_options, index=0)

    # --- 🏠 홈 ---
    if choice == "🏠 홈":
        st.title("🏔️ 운영 대시보드")
        with get_db_connection() as conn:
            df_summary = conn.execute("SELECT * FROM v_member_attendance_summary").df()
            active_members = df_summary[df_summary['회원상태'] != 'exmember']
            active_count = len(active_members)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("정회원/신입", f"{active_count}명")
        m2.metric("이달의 총 점수", f"{int(df_summary['획득점수'].sum())}점")
        m3.metric("🚨 관리대상", f"{len(df_summary[df_summary['회원상태'].str.contains('🚨')])}명")

        # --- [복구된 AI 버튼 영역] ---
        if ai_model:
            st.divider()
            with st.expander("✨ AI 산악회 비서 브리핑", expanded=True):
                if st.button("🔍 데이터 분석 및 격려 멘트 생성", use_container_width=True):
                    with st.spinner(f"{selected_model} 모델이 데이터를 분석 중입니다..."):
                        data_json = df_summary[['MemberID', '획득점수', '현재포인트', '회원상태']].to_json()
                        prompt = f"당신은 '또닥또닥 산악회'의 AI 비서입니다. 다음 데이터를 분석해 이번 달 산행 MVP를 칭찬하고, 활동이 뜸한 휴면 우려 회원들에게 따뜻한 격려의 메시지를 작성해줘: {data_json}"
                        try:
                            res = ai_model.generate_content(prompt)
                            st.markdown(res.text)
                        except Exception as e:
                            st.error(f"AI 분석 중 오류 발생: {e}")
        # ----------------------------

        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_summary, names='지역', title=f'📍 지역별 분포 (총 {active_count}명)', hole=0.3), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df_summary, x='생년', y='현재포인트', color='회원상태', title='🎂 기수별 활동 지수'), use_container_width=True)

    # --- 👥 회원 관리 ---
    elif choice == "👥 회원 관리":
        st.header("👥 회원 명부 관리")
        with get_db_connection() as conn:
            df_all = conn.execute("SELECT * FROM members ORDER BY birth_year ASC, name ASC").df()

        f1, f2, f3 = st.columns(3)
        with f1: 
            years = sorted(df_all['birth_year'].unique().tolist())
            sel_years = st.multiselect(f"🎂 생년 필터 ({len(years)}개 기수)", years)
        with f2: 
            areas = sorted(df_all['area'].unique().tolist())
            sel_areas = st.multiselect(f"📍 지역 필터 ({len(areas)}개 지역)", areas)
        with f3: 
            roles = sorted(df_all['role'].unique().tolist())
            sel_role = st.multiselect(f"👤 등급 필터 ({len(roles)}종류)", roles)

        df_m = df_all.copy()
        if sel_years: df_m = df_m[df_m['birth_year'].isin(sel_years)]
        if sel_areas: df_m = df_m[df_m['area'].isin(sel_areas)]
        if sel_role: df_m = df_m[df_m['role'].isin(sel_role)]

        st.subheader(f"📋 회원 목록 (검색 결과: {len(df_m)}명 / 전체: {len(df_all)}명)")
        updated_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True, hide_index=True)

        if st.button("💾 변경사항 저장 (회원)"):
            with get_db_connection() as conn:
                for _, row in updated_m.iterrows():
                    u_id = str(row['user_no'])
                    row_dict = row.to_dict()
                    existing = conn.execute("SELECT * FROM members WHERE user_no = ?", (u_id,)).df()
                    if not existing.empty:
                        changed, params = [], []
                        for col in updated_m.columns:
                            if col in ['user_no', 'last_attended']: continue
                            if str(row_dict[col]) != str(existing.iloc[0][col]):
                                changed.append(f'"{col}" = ?'); params.append(row_dict[col])
                        if changed: conn.execute(f"UPDATE members SET {', '.join(changed)} WHERE user_no = ?", tuple(params + [u_id]))
                    else:
                        m_cols = updated_m.columns.tolist()
                        m_quoted = [f'"{c}"' for c in m_cols]
                        m_placeholders = ", ".join(["?"] * len(m_cols))
                        m_sql = f"INSERT INTO members ({', '.join(m_quoted)}) VALUES ({m_placeholders})"
                        conn.execute(m_sql, tuple([row_dict[c] for c in m_cols]))
            st.success(f"{len(updated_m)}명의 정보가 업데이트되었습니다."); st.rerun()

    # --- 📅 산행 일정 ---
    elif choice == "📅 산행 일정":
        st.header("📅 산행 일정 관리")
        with get_db_connection() as conn:
            df_e = conn.execute("SELECT * FROM events ORDER BY date DESC").df()
        
        st.subheader(f"🗓️ 등록된 일정 (총 {len(df_e)}건)")
        updated_e = st.data_editor(df_e, num_rows="dynamic", use_container_width=True, hide_index=True)
        
        if st.button("💾 일정 저장"):
            with get_db_connection() as conn:
                for _, row in updated_e.iterrows():
                    e_id = str(row['event_id'])
                    existing = conn.execute("SELECT * FROM events WHERE event_id = ?", (e_id,)).df()
                    if not existing.empty:
                        changed, params = [], []
                        for col in updated_e.columns:
                            if col == 'event_id': continue
                            if str(row[col]) != str(existing.iloc[0][col]):
                                changed.append(f'"{col}" = ?'); params.append(row[col])
                        if changed: conn.execute(f"UPDATE events SET {', '.join(changed)} WHERE event_id = ?", tuple(params + [e_id]))
                    else:
                        e_cols = updated_e.columns.tolist()
                        e_quoted = [f'"{c}"' for c in e_cols]
                        e_placeholders = ", ".join(["?"] * len(e_cols))
                        e_sql = f"INSERT INTO events ({', '.join(e_quoted)}) VALUES ({e_placeholders})"
                        conn.execute(e_sql, tuple(row[e_cols]))
            st.success("일정이 반영되었습니다."); st.rerun()

    # --- 🏃 참가 체크 ---
    elif choice == "🏃 참가 체크":
        st.header("🏃 참석자 명단 체크")
        with get_db_connection() as conn:
            ev_list = conn.execute("SELECT event_id, strftime('%Y-%m-%d', date) as d, title FROM events ORDER BY date DESC").df()
            mb_list = conn.execute("SELECT user_no, birth_year, name, area FROM members WHERE role<>'exmember' ORDER BY birth_year ASC, name ASC").df()
        
        if not ev_list.empty:
            ev_list['label'] = ev_list.apply(lambda r: f"{r['d']} | {r['title']}", axis=1)
            sel_ev = st.selectbox(f"🎯 산행 선택 (총 {len(ev_list)}개 중 선택)", ev_list['label'].tolist())
            sel_ev_id = str(ev_list.loc[ev_list['label'] == sel_ev, 'event_id'].iloc[0])
            
            with get_db_connection() as conn:
                existing = conn.execute("SELECT user_no FROM attendees WHERE event_id = ?", (sel_ev_id,)).df()['user_no'].tolist()
            
            mb_list['display'] = mb_list.apply(lambda r: f"{r['birth_year']}/{r['name']}/{r['area']}", axis=1)
            selected = st.multiselect(f"🏃 참석자 선택 (대상 회원: {len(mb_list)}명)", 
                                      options=mb_list['display'].tolist(), 
                                      default=mb_list[mb_list['user_no'].isin(existing)]['display'].tolist())

            st.info(f"💡 현재 선택된 인원: **{len(selected)}명**")

            if st.button("✅ 참석 명단 최종 확정", use_container_width=True, type="primary"):
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM attendees WHERE event_id = ?", (sel_ev_id,))
                    for val in selected:
                        u_no = mb_list.loc[mb_list['display'] == val, 'user_no'].iloc[0]
                        conn.execute("INSERT INTO attendees (event_id, user_no) VALUES (?, ?)", (sel_ev_id, u_no))
                st.success(f"저장 성공! 총 {len(selected)}명이 기록되었습니다."); st.rerun()

    # --- 📊 보고서 생성 ---
    elif choice == "📊 보고서 생성":
        st.header("📊 활동 결과 보고서")
        target_month = st.text_input("📅 대상 월 선택 (YYYY-MM)", value=datetime.now(KST).strftime('%Y-%m'))
        
        if st.button("📝 보고서 생성", use_container_width=True):
            with get_db_connection() as conn:
                ev_det = conn.execute(f"""
                    SELECT CAST(e.date AS DATE) as d, e.title, m.name 
                    FROM events e 
                    JOIN attendees a ON e.event_id = a.event_id 
                    JOIN members m ON a.user_no = m.user_no 
                    WHERE strftime('%Y-%m', CAST(e.date AS DATE)) = '{target_month}' 
                    ORDER BY e.date ASC, m.birth_year ASC, m.name ASC
                """).df()

            report_text = f"⛰️ **{target_month} 또닥또닥 활동 요약**\n\n"
            if not ev_det.empty:
                for (d, title), group in ev_det.groupby(['d', 'title'], sort=False):
                    names = group['name'].tolist()
                    report_text += f"📍 {d.strftime('%m/%d')} | {title}\n└ 참석({len(names)}명): {', '.join(names)}\n\n"
                report_text += f"--- \n총 {len(ev_det['title'].unique())}회의 산행이 진행되었습니다."
            else:
                report_text += "활동 내역이 없습니다."
            
            st.code(report_text.replace("**", ""), language="text")
            st.markdown(report_text)

elif st.session_state["authentication_status"] is False:
    st.error('ID/PW가 일치하지 않습니다.')
elif st.session_state["authentication_status"] is None:
    st.warning('또닥또닥 운영진 로그인이 필요합니다.')