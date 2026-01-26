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
 # --- 🏠 홈 ---
    if choice == "🏠 홈":
        st.title("🏔️ 운영 대시보드")
        with get_db_connection() as conn:
            # 요약 데이터와 전체 회원 데이터 로드
            df_summary = conn.execute("SELECT * FROM v_member_attendance_summary").df()
            # 성별 및 연도 분포를 위해 members 테이블 직접 조회 (탈퇴 회원 제외)
            df_members = conn.execute("SELECT birth_year, gender, area, role FROM members WHERE role<>'exmember'").df()
            active_count = len(df_members)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("정회원/신입", f"{active_count}명")
        m2.metric("이달의 총 점수", f"{int(df_summary['획득점수'].sum())}점")
        m3.metric("🚨 관리대상", f"{len(df_summary[df_summary['회원상태'].str.contains('🚨')])}명")

        # AI 비서 섹션
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

        st.divider()
        
        # 첫 번째 행: 기존 지역 및 활동 지수
        c1, c2 = st.columns(2)
        with c1: 
            st.plotly_chart(px.pie(df_summary, names='지역', title=f'📍 지역별 분포 (총 {active_count}명)', 
                                   hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        with c2: 
            st.plotly_chart(px.bar(df_summary, x='생년', y='현재포인트', color='회원상태', 
                                   title='🎂 기수별 활동 지수 (누적 포인트)'), use_container_width=True)

        # [신규] 두 번째 행: 연도별 인원 및 성별 분포
        st.write("### 📊 회원 통계 상세")
        c3, c4 = st.columns(2)
        with c3:
            # 연도별(기수별) 인원 분포 (막대 차트)
            df_year_dist = df_members.groupby('birth_year').size().reset_index(name='인원수')
            fig_year = px.bar(df_year_dist, x='birth_year', y='인원수', 
                              title='📅 연도별(기수) 회원 수', 
                              text_auto=True, color_discrete_sequence=['#636EFA'])
            fig_year.update_xaxes(type='category') # 연도를 카테고리로 처리하여 숫자가 겹치지 않게 함
            st.plotly_chart(fig_year, use_container_width=True)
            
        with c4:
            # 성별 분포 (파이 차트)
            if 'gender' in df_members.columns and not df_members['gender'].isnull().all():
                st.plotly_chart(px.pie(df_members, names='gender', title='🚻 성별 분포', 
                                       hole=0.3, color_discrete_sequence=['#EF553B', '#00CC96']), use_container_width=True)
            else:
                st.info("💡 '성별' 데이터가 입력되지 않았습니다. 명부 관리에서 gender 항목을 채워주세요.")
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
        st.header("📊 활동 결과 보고서 생성")
        
        # 날짜 입력 및 데이터 로드
        col1, col2 = st.columns([2, 1])
        with col1:
            # [복구] 회칙 링크 입력란 (기존에 쓰시던 링크를 value에 넣으시면 편합니다)
            rules_url = st.text_input("🔗 회칙 링크", value="https://www.band.us/band/85157163/post/4765") 
        with col2:
            target_month = st.text_input("📅 대상 월 (YYYY-MM)", value=datetime.now(KST).strftime('%Y-%m'))
        
        if st.button("📝 보고서 생성 및 데이터 분석", use_container_width=True, type="primary"):
            with get_db_connection() as conn:
                # 1. 해당 월의 모든 산행 및 참석자 명단 (정렬: 날짜 -> 기수 -> 이름)
                ev_det = conn.execute(f"""
                    SELECT CAST(e.date AS DATE) as d, e.title, e.album_url, m.name, Case When e.host = a.user_no Then  1 Else 0 End as is_host
                    FROM events e 
                    JOIN attendees a ON e.event_id = a.event_id 
                    JOIN members m ON a.user_no = m.user_no
                    WHERE strftime('%Y-%m', CAST(e.date AS DATE)) = '{target_month}'
                    ORDER BY e.date ASC, m.birth_year ASC, m.name ASC
                """).df()

                # 2. 요약 뷰 데이터 로드 (시상 및 경고 계산용)
                df_rep = conn.execute("SELECT * FROM v_member_attendance_summary").df()

            # --- 리포트 텍스트 생성 시작 ---
            report_text = f"⛰️ **{target_month} 또닥또닥 활동 요약 보고서**\n\n"
            report_text = f"🔗 **또닥또닥 회칙 안내**  \n{rules_url}\n\n"
            # [항목 1] 산행 내역 및 참석자 (호스트 표시)
            report_text += "📅 **[이달의 산행 기록]**  \n"
            if not ev_det.empty:
                for (d, title), group in ev_det.groupby(['d', 'title'], sort=False):
                    # 호스트는 이름 뒤에 (H) 표시
                    names_with_host = group.apply(lambda r: f"{r['name']}(H)" if r['is_host'] == 1 else r['name'], axis=1).tolist()
                    report_text += f"📍 {d.strftime('%m/%d')} | {title}  \n└ 참석({len(names_with_host)}명): {', '.join(names_with_host)}  \n"
                    if group['album_url'].iloc[0]:
                        report_text += f"└ 📸 사진첩: {group['album_url'].iloc[0]}  \n"
                    report_text += "\n"
            else:
                report_text += "등록된 산행 기록이 없습니다.\n\n"

            # [항목 2] 시상 안내 (포인트 기반)
            report_text += "🏆 **[이달의 시상 및 포인트 현황]**  \n"
            winners = []
            # 점수 타입 변환 및 결측치 처리
            df_rep['획득점수'] = df_rep['획득점수'].fillna(0).astype(int)
            df_rep['현재포인트'] = df_rep['현재포인트'].fillna(0).astype(int)

            for _, row in df_rep.iterrows():
                info, m_score, t_point = row['MemberID'], row['획득점수'], row['현재포인트']
                if m_score > 0:
                    prev_p = t_point - m_score
                    # 구간 돌파 시상 로직
                    for th, msg in [(100, "💯 특별시상"), (50, "🎫 50점 달성"), (30, "🎫 30점 달성"), (10, "🎫 10점 달성")]:
                        if t_point >= th and prev_p < th:
                            winners.append(f"✨ {info} (현재 {t_point}점) {msg}")
                            break
            
            report_text += ("\n".join(winners) if winners else "이번 달 시상 대상자 없음") + "\n\n"

            # [항목 3] 미활동 경고 (상태값 기반)
            report_text += "🚨 **[활동 관리 안내]**  \n"
            sleep_warning = df_rep[df_rep['회원상태'] == '😴🚨']['MemberID'].tolist()
            new_warning = df_rep[df_rep['회원상태'] == '🌱🚨']['MemberID'].tolist()
            
            report_text += f"😴 장기 미참석(경고):  \n {', '.join(sleep_warning) if sleep_warning else '없음'}  \n"
            report_text += f"🌱 신입 미참석(경고):  \n {', '.join(new_warning) if new_warning else '없음'}\n\n"

            # [4] 최하단: 전체 회원 누적 점수 (요청하신 대로 맨 아래 배치!)
            report_text += "🔢 **[전체 회원 누적 점수 현황]**\n"
            report_text += "| 회원 | 금월 획득 점수 | 누적 점수 | 현재 상태 |\n"
            report_text += "| :--- | ---: | ---: | :---: |\n"
            
            active_list = df_rep[df_rep['회원상태'] != 'exmember']
            for _, row in active_list.iterrows():
                # 테이블 각 행 생성
                report_text += f"| {row['MemberID']} | {row['획득점수']}점 | {row['현재포인트']}점 | {row['회원상태']} |\n"
            report_text += "---\n"
            report_text += f"건강한 산행 문화, 함께 만들어가요! ⛰️\n"
            st.success(f"✅ {target_month} 리포트 생성 완료!")
            
            t1, t2 = st.tabs(["📋 밴드 복사용", "👀 미리보기"])
            
            with t1:
                st.info("아래 코드를 복사해서 네이버 밴드에 붙여넣으세요.")
                st.code(report_text.replace("**", ""), language="text")
            
            with t2:
                st.markdown(report_text)

           

elif st.session_state["authentication_status"] is False:
    st.error('ID/PW가 일치하지 않습니다.')
elif st.session_state["authentication_status"] is None:
    st.warning('또닥또닥 운영진 로그인이 필요합니다.')