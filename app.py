import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit_authenticator as stauth

# --- 사용자 인증 설정 ---
# 아이디: ddodak_admin / 비번: ddodak2_2016! 의 해싱 결과입니다.
credentials = {
    "usernames": {
        "ddodak_admin": {
            "name": "관리자",
            "password": "$2b$12$26eJr8zlp73HWwLlP7xbAeArmA844B0iRAc39VanX.7ezIZ/abbiq" # 해싱된 비밀번호
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "ddodak_cookie", # 쿠키 이름
    "ddodak_key",    # 서명 키
    cookie_expiry_days=30
)

# 로그인 화면 출력
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    # --- 로그인 성공: 기존 앱 로직 시작 ---
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.write(f"환영합니다, {st.session_state['name']}님!")
    
    # [이 아래에 기존의 choice = st.sidebar.radio(...) 부터의 코드를 모두 넣으세요]
    # (주의: 기존 코드 전체를 이 if문 안으로 한 칸씩 들여쓰기 해야 합니다.)

elif st.session_state["authentication_status"] is False:
    st.error('아이디 또는 비밀번호가 일치하지 않습니다.')
    st.stop()
elif st.session_state["authentication_status"] is None:
    st.warning('아이디와 비밀번호를 입력해 주세요.')
    st.stop()
# 1. 환경 설정 (한국 시간)
KST = timezone(timedelta(hours=9))

def get_db_connection():
    # 데이터베이스 파일 연결 (read_only=False로 수정 가능 모드)
    return duckdb.connect('ddodak.duckdb', read_only=False)

st.set_page_config(page_title="또닥또닥 산악회 관리시스템", layout="wide")
st.sidebar.title("⛰️ 메뉴")
choice = st.sidebar.radio("메뉴 이동", ["🏠 홈", "👥 회원 관리", "📅 이벤트 관리", "🏃 참가 기록", "📊 보고서 생성"], key="nav_main")

# ---------------------------------------------------------
# 1. 홈
# ---------------------------------------------------------
if choice == "🏠 홈":
    st.title("⛰️ 대시보드")
    with get_db_connection() as conn:
        active = conn.execute("SELECT count(*) FROM members WHERE role <> 'exmember'").fetchone()[0]
    st.metric("현재 활동 회원", f"{active}명")
    st.info("💡 모든 데이터는 실시간으로 반영되며, 보고서는 v_member_attendance_summary 뷰를 기반으로 생성됩니다.")

# ---------------------------------------------------------
# 2. 회원 관리 (FK 제약 조건 우회 - 동적 컬럼 업데이트)
# ---------------------------------------------------------
elif choice == "👥 회원 관리":
    st.header("👥 회원 정보 관리")
    with get_db_connection() as conn:
        conn.execute("""
    UPDATE members AS m
    SET last_attended = t.last_attended
    FROM (
    SELECT a.user_no, MAX(e.date) AS last_attended
    FROM attendees AS a
    JOIN events AS e ON e.event_id = a.event_id
    GROUP BY a.user_no
    ) AS t
    WHERE t.user_no = m.user_no;
                     """)
        df_m = conn.execute("SELECT * FROM members Order by birth_year, name, area").df()
    
    updated_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True, hide_index=True, key="m_edit")
    
    if st.button("💾 회원 정보 업데이트"):
        if not updated_m.empty:
            with get_db_connection() as conn:
                for _, row in updated_m.iterrows():
                    u_id = str(row['user_no'])
                    
                    # 1. 기존 데이터 로드 (비교용)
                    existing = conn.execute("SELECT * FROM members WHERE user_no = ?", (u_id,)).df()
                    
                    if not existing.empty:
                        # 2. 실제로 값이 바뀐 컬럼만 추출
                        changed_cols = []
                        params = []
                        for col in updated_m.columns:
                            if col == 'user_no': continue  # PK(회원번호)는 절대 수정 대상(SET)에 넣지 않음
                            
                            val_new = row[col]
                            val_old = existing.iloc[0][col]
                            
                            # 데이터 비교 (문자열 변환 후 비교하여 형식 차이 무시)
                            if str(val_new) != str(val_old):
                                changed_cols.append(f'"{col}" = ?')
                                params.append(val_new)
                        
                        # 3. 변경사항이 있을 때만 UPDATE 실행
                        if changed_cols:
                            sql = f"UPDATE members SET {', '.join(changed_cols)} WHERE user_no = ?"
                            params.append(u_id)
                            conn.execute(sql, tuple(params))
                    else:
                        # 4. 신규 회원 INSERT
                        cols = updated_m.columns.tolist()
                        quoted_cols = [f'"{c}"' for c in cols]
                        placeholders = ", ".join(["?"] * len(cols))
                        sql = f'INSERT INTO members ({", ".join(quoted_cols)}) VALUES ({placeholders})'
                        conn.execute(sql, tuple(row[cols]))
            
            st.success("회원 정보가 참조 무결성을 유지하며 안전하게 저장되었습니다.")
            st.rerun()

# ---------------------------------------------------------
# 3. 일정 관리 (FK 제약 조건 우회 - 동적 컬럼 업데이트)
# ---------------------------------------------------------
elif choice == "📅 이벤트 관리":
    st.header("📅 산행 일정 관리")
    with get_db_connection() as conn:
        df_e = conn.execute("SELECT * FROM events ORDER BY date DESC").df()
    
    updated_e = st.data_editor(df_e, num_rows="dynamic", use_container_width=True, hide_index=True, key="e_edit")
    
    if st.button("💾 일정 업데이트"):
        if not updated_e.empty:
            with get_db_connection() as conn:
                for _, row in updated_e.iterrows():
                    e_id = str(row['event_id'])
                    
                    # 1. 기존 데이터 로드 (비교용)
                    existing = conn.execute("SELECT * FROM events WHERE event_id = ?", (e_id,)).df()
                    
                    if not existing.empty:
                        # 2. 실제로 값이 바뀐 컬럼만 추출
                        changed_cols = []
                        params = []
                        for col in updated_e.columns:
                            if col == 'event_id': continue  # PK는 절대 수정 대상에 넣지 않음
                            
                            val_new = row[col]
                            val_old = existing.iloc[0][col]
                            
                            # None/NaN 처리 및 비교
                            if str(val_new) != str(val_old):
                                changed_cols.append(f'"{col}" = ?')
                                params.append(val_new)
                        
                        # 3. 변경사항이 있을 때만 UPDATE 실행
                        if changed_cols:
                            sql = f"UPDATE events SET {', '.join(changed_cols)} WHERE event_id = ?"
                            params.append(e_id)
                            conn.execute(sql, tuple(params))
                    else:
                        # 4. 신규 데이터 INSERT
                        cols = updated_e.columns.tolist()
                        quoted_cols = [f'"{c}"' for c in cols]
                        placeholders = ", ".join(["?"] * len(cols))
                        sql = f'INSERT INTO events ({", ".join(quoted_cols)}) VALUES ({placeholders})'
                        conn.execute(sql, tuple(row[cols]))
            
            st.success("참조 무결성을 유지하며 변경된 필드만 업데이트했습니다.")
            st.rerun()

# ---------------------------------------------------------
# 4. 참가 기록 (스크롤바 완벽 수정 및 인원 표시)
# ---------------------------------------------------------
elif choice == "🏃 참가 기록":
    st.header("🏃 공지 참가자 체크")
    
    # --- [스크롤바 강제 생성을 위한 CSS 고도화] ---
    st.markdown("""
        <style>
            /* 멀티셀렉트의 태그(항목)가 쌓이는 컨테이너 높이 제한 */
            div[data-baseweb="select"] > div:first-child {
                max-height: 200px !important;
                overflow-y: auto !important;
                display: block !important;
            }
            /* 개별 태그(X버튼 있는 항목)들의 간격 조정 */
            div[data-baseweb="tag"] {
                margin: 2px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    with get_db_connection() as conn:
        ev_list = conn.execute("SELECT event_id, strftime('%Y-%m-%d', date) as date, title FROM events ORDER BY date DESC").df()
        mb_list = conn.execute("SELECT user_no, birth_year, name, area FROM members WHERE role <> 'exmember' ORDER BY birth_year, name").df()
    
    if not ev_list.empty:
        ev_list['label'] = ev_list.apply(lambda r: f"{r['date']} | {r['title']}", axis=1)
        sel_ev = st.selectbox("공지 선택", ev_list['label'].tolist(), key="sel_ev")
        sel_ev_id = str(ev_list.loc[ev_list['label'] == sel_ev, 'event_id'].iloc[0])

        with get_db_connection() as conn:
            existing = conn.execute("SELECT user_no FROM attendees WHERE event_id = ?", (sel_ev_id,)).df()['user_no'].tolist()
        
        mb_list['display'] = mb_list.apply(lambda r: f"{r['birth_year']}/{r['name']}/{r['area']}", axis=1)
        
        selected = st.multiselect(
            "참가자 선택", 
            options=mb_list['display'].tolist(), 
            default=mb_list[mb_list['user_no'].isin(existing)]['display'].tolist(), 
            key=f"ms_{sel_ev_id}"
        )
        
        # --- [추가: 총 참가 인원 표시] ---
        total_count = len(selected)
        st.markdown(f"### 👥 총 참가 인원: `{total_count}`명")
        # -------------------------------

        if st.button("✅ 참석 명단 저장", use_container_width=True, type="primary"):
            with get_db_connection() as conn:
                conn.execute("DELETE FROM attendees WHERE event_id = ?", (sel_ev_id,))
                for val in selected:
                    u_no = mb_list.loc[mb_list['display'] == val, 'user_no'].iloc[0]
                    conn.execute("INSERT INTO attendees (event_id, user_no) VALUES (?, ?)", (sel_ev_id, u_no))
            st.success(f"저장 완료! 현재 총 {total_count}명이 등록되었습니다.")
            
    else: 
        st.warning("이벤트를 먼저 등록하세요.")

# ---------------------------------------------------------
# 5. 보고서 생성 (줄바꿈 및 가독성 강화 버전)
# ---------------------------------------------------------
elif choice == "📊 보고서 생성":
    st.header("📊 활동 결과 보고서")
    st.markdown("""
        <a href="https://www.band.us/band/85157163/post/4765" target="_blank" style="text-decoration: none;">
            <div style="background-color: #2e7d32; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 20px;">
                📜 또닥또닥 회칙 확인하기 (네이버 밴드)
            </div>
        </a>
    """, unsafe_allow_html=True)
    target_month = st.text_input("📅 대상 월 선택", value=datetime.now(KST).strftime('%Y-%m'))
    
    if st.button("📝 보고서 생성", use_container_width=True):
        try:
            with get_db_connection() as conn:
                df_rep = conn.execute("SELECT * FROM v_member_attendance_summary").df()
                ev_det = conn.execute(f"""
                    SELECT CAST(e.date AS DATE) as d, e.title, m.name, m.birth_year, m.area
                    FROM events e 
                    JOIN attendees a ON e.event_id = a.event_id 
                    JOIN members m ON a.user_no = m.user_no
                    WHERE strftime('%Y-%m', CAST(e.date AS DATE)) = '{target_month}'
                    ORDER BY e.date ASC
                """).df()

            df_rep['획득점수'] = df_rep['획득점수'].fillna(0).astype(int)
            df_rep['현재포인트'] = df_rep['현재포인트'].fillna(0).astype(int)
            
            # --- 리포트 텍스트 구성 (줄바꿈 \n\n 적용) ---
            report_text = f"⛰️ **{target_month} 활동 요약 보고서**\n\n"
            report_text += "---\n\n"
            
            report_text += "📂 **[이달의 산행 내역]**\n\n"
            if not ev_det.empty:
                for (d, title), group in ev_det.groupby(['d', 'title'], sort=False):
                    names = group['name'].tolist()
                    report_text += f"📍 **{d.strftime('%m/%d')} | {title}**  \n"
                    report_text += f"└ 참석({len(names)}명): {', '.join(names)}  \n\n"
            else:
                report_text += "이달의 기록이 없습니다.  \n\n"
            
            report_text += "🏆 **[시상 및 안내]**\n\n"
            winners, sleep_warning, new_warning = [], [], []
            for _, row in df_rep.iterrows():
                info, status, m_score, t_point = row['MemberID'], row['회원상태'], row['획득점수'], row['현재포인트']
                if m_score > 0:
                    prev_p = t_point - m_score
                    for th, msg in [(100, "💯 특별시상"), (50, "🎫50 ₩20,000"), (30, "🎫30 ₩15,000"), (10, "🎫10 ₩10,000")]:
                        if t_point >= th and prev_p < th:
                            winners.append(f"✨ {info} ({t_point}점) {msg}")
                            break
                if status == '😴🚨': sleep_warning.append(info)
                elif status == '🌱🚨': new_warning.append(info)

            report_text += ("\n".join(winners) if winners else "해당 사항 없음") + "\n\n"
            
            report_text += "🚨 **[미참석 경고 명단]**\n\n"
            report_text += f"😴 장기 미참석:  \n{', '.join(sleep_warning) if sleep_warning else '없음'}  \n"
            report_text += f"🌱 신입 미참석:  \n{', '.join(new_warning) if new_warning else '없음'}  \n\n"
            
            report_text += "🔢 **[회원별 점수 현황]**\n\n"
            # 마크다운 표 앞뒤로 반드시 빈 줄(\n\n)이 있어야 깨지지 않습니다.
            report_text += df_rep[['MemberID', '획득점수', '현재포인트', '회원상태']].rename(columns={'획득점수':'당월','현재포인트':'누적','회원상태':'상태'}).to_markdown(index=False)
            report_text += "\n\n---\n"

            # --- 화면 출력 섹션 ---
            t1, t2 = st.tabs(["📋 밴드 복사용 (텍스트)", "👀 미리보기 (시각화)"])
            
            with t1:
                st.info("박스 안의 텍스트를 복사하세요.")
                st.code(report_text.replace("**", ""), language="text") # 복사용은 강조 표시 제거
            
            with t2:
                # 마크다운 렌더링 (st.markdown은 \n\n을 인식하여 단락을 나눕니다)
                st.markdown(report_text)

        except Exception as e:
            st.error(f"오류 발생: {e}")