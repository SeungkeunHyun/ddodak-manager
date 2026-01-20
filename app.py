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
query_params = st.query_params
default_menu = query_params.get("menu", "🏠 홈") # 기본값은 홈
menu_options = ["🏠 홈", "👥 회원 관리", "📅 이벤트 관리", "🏃 참가 기록", "📊 보고서 생성"]

# URL 파라미터에 따라 인덱스 찾기 (잘못된 파라미터면 0번 인덱스)
try:
    default_index = menu_options.index(default_menu)
except ValueError:
    default_index = 0
choice = st.sidebar.radio("메뉴 이동", menu_options, index=default_index)
if choice != query_params.get("menu"):
    st.query_params["menu"] = choice
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
# 2. 회원 관리 (필터링 + 최신 참석일 갱신 + 동적 업데이트)
# ---------------------------------------------------------
elif choice == "👥 회원 관리":
    st.header("👥 회원 정보 관리")

    with get_db_connection() as conn:
        # A. 최신 참석일(last_attended) 자동 동기화 쿼리
        conn.execute("""
            UPDATE members AS m
            SET last_attended = t.max_date
            FROM (
                SELECT a.user_no, MAX(e.date) AS max_date
                FROM attendees AS a
                JOIN events AS e ON e.event_id = a.event_id
                GROUP BY a.user_no
            ) AS t
            WHERE t.user_no = m.user_no;
        """)
        # B. 전체 회원 데이터 로드 (필터 옵션 추출용)
        df_all = conn.execute("SELECT * FROM members WHERE role <> 'exmember' order by birth_year, name, area").df()

    # --- [필터링 UI 섹션] ---
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        years_options = sorted(df_all['birth_year'].unique().tolist())
        sel_years = st.multiselect("🎂 생년 필터", options=years_options, placeholder="전체 보기")
    with f_col2:
        areas_options = sorted(df_all['area'].unique().tolist())
        sel_areas = st.multiselect("📍 지역 필터", options=areas_options, placeholder="전체 보기")

    # 데이터 필터링 적용
    df_m = df_all.copy()
    if sel_years:
        df_m = df_m[df_m['birth_year'].isin(sel_years)]
    if sel_areas:
        df_m = df_m[df_m['area'].isin(sel_areas)]

    st.caption(f"🔍 검색 결과: {len(df_m)}명")

    # --- [데이터 에디터 섹션] ---
    # last_attended는 자동 갱신되므로 편집 비활성화(disabled) 권장
    updated_m = st.data_editor(
        df_m, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True, 
        key="m_edit",
        column_config={
            "last_attended": st.column_config.Column(disabled=True, help="참가 기록 시 자동 갱신됩니다.")
        }
    )
    
    # --- [저장 로직 섹션] ---
    if st.button("💾 회원 정보 업데이트"):
        if not updated_m.empty:
            with get_db_connection() as conn:
                for _, row in updated_m.iterrows():
                    u_id = str(row['user_no'])
                    
                    # 1. 기존 데이터 로드 (비교용)
                    existing = conn.execute("SELECT * FROM members WHERE user_no = ?", (u_id,)).df()
                    
                    if not existing.empty:
                        # 2. 변경된 컬럼만 추출
                        changed_cols = []
                        params = []
                        for col in updated_m.columns:
                            if col in ['user_no', 'last_attended']: continue # PK와 자동갱신 컬럼 제외
                            
                            val_new = row[col]
                            val_old = existing.iloc[0][col]
                            
                            if str(val_new) != str(val_old):
                                changed_cols.append(f'"{col}" = ?')
                                params.append(val_new)
                        
                        # 3. 변경사항이 있을 때만 UPDATE
                        if changed_cols:
                            sql = f"UPDATE members SET {', '.join(changed_cols)} WHERE user_no = ?"
                            params.append(u_id)
                            conn.execute(sql, tuple(params))
                    # 기존의 백슬래시가 포함된 복잡한 f-string을 아래와 같이 간결하게 수정합니다.
                    else:
                        # 4. 신규 회원 INSERT
                        cols = updated_m.columns.tolist()
                        quoted_cols = [f'"{c}"' for c in cols]
                        placeholders = ", ".join(["?"] * len(cols))
                        
                        sql = f'INSERT INTO members ({", ".join(quoted_cols)}) VALUES ({placeholders})'
                        conn.execute(sql, tuple(row[cols]))
            
            st.success("필터링된 상태에서도 회원 정보가 안전하게 저장되었습니다.")
            st.rerun()

elif choice == "📅 이벤트 관리":
    st.header("📅 산행 일정 관리")
    
    # --- 필터링 섹션 ---
    col1, col2 = st.columns(2)
    with col1:
        years = [str(datetime.now().year - i) for i in range(3)] # 최근 3년
        f_year = st.selectbox("연도 선택", ["전체"] + years)
    with col2:
        f_month = st.selectbox("월 선택", ["전체"] + [f"{i:02d}" for i in range(1, 13)])

    # DB 조회 쿼리 구성
    query = "SELECT * FROM events WHERE 1=1"
    if f_year != "전체":
        query += f" AND strftime('%Y', date) = '{f_year}'"
    if f_month != "전체":
        query += f" AND strftime('%m', date) = '{f_month}'"
    query += " ORDER BY date DESC"

    with get_db_connection() as conn:
        df_e = conn.execute(query).df()
    
    # 앨범 URL 등 컬럼 설정 추가
    updated_e = st.data_editor(
        df_e, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True, 
        key="e_edit",
        column_config={
            "album_url": st.column_config.LinkColumn("앨범 URL"),
            "url": st.column_config.LinkColumn("공지 URL"),
            "date": st.column_config.DateColumn("날짜")
        }
    )
    
    # [저장 로직은 기존과 동일하되 st.rerun()으로 필터 유지]
    if st.button("💾 일정 업데이트"):
        if not updated_e.empty:
            with get_db_connection() as conn:
                for _, row in updated_e.iterrows():
                    e_id = str(row['event_id'])
                    existing = conn.execute("SELECT * FROM events WHERE event_id = ?", (e_id,)).df()
                    
                    if not existing.empty:
                        changed_cols, params = [], []
                        for col in updated_e.columns:
                            if col == 'event_id': continue
                            val_new, val_old = row[col], existing.iloc[0][col]
                            if str(val_new) != str(val_old):
                                changed_cols.append(f'"{col}" = ?')
                                params.append(val_new)
                        
                        if changed_cols:
                            sql = f"UPDATE events SET {', '.join(changed_cols)} WHERE event_id = ?"
                            params.append(e_id)
                            conn.execute(sql, tuple(params))
                    # 기존의 백슬래시가 포함된 복잡한 f-string을 아래와 같이 간결하게 수정합니다.
                    else:
                        # 4. 신규 데이터 INSERT
                        cols = updated_e.columns.tolist()
                        # f-string 내부에서 백슬래시 없이 쌍따옴표를 입히는 방법
                        quoted_cols = [f'"{c}"' for c in cols] 
                        placeholders = ", ".join(["?"] * len(cols))
                        
                        # 최종 SQL문 구성
                        sql = f'INSERT INTO events ({", ".join(quoted_cols)}) VALUES ({placeholders})'
                        conn.execute(sql, tuple(row[cols]))
            st.success("업데이트 완료!")
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
# 5. 보고서 생성 (앨범 URL 및 월간 요약 통합 버전)
# ---------------------------------------------------------
elif choice == "📊 보고서 생성":
    st.header("📊 활동 결과 보고서")
    
    # 상단 회칙 링크 (UI용)
    st.info("🔗 [또닥또닥 회칙 확인하기]  \n(https://www.band.us/band/85157163/post/4765)")
    
    target_month = st.text_input("📅 대상 월 선택", value=datetime.now(KST).strftime('%Y-%m'))
    
    if st.button("📝 보고서 생성", use_container_width=True):
        try:
            with get_db_connection() as conn:
                df_rep = conn.execute("SELECT * FROM v_member_attendance_summary").df()
                # 쿼리에 e.album_url 추가
                ev_det = conn.execute(f"""
                    SELECT CAST(e.date AS DATE) as d, e.title, e.album_url, m.name, m.birth_year, m.area
                    FROM events e 
                    JOIN attendees a ON e.event_id = a.event_id 
                    JOIN members m ON a.user_no = m.user_no
                    WHERE strftime('%Y-%m', CAST(e.date AS DATE)) = '{target_month}'
                    ORDER BY e.date, m.birth_year, m.name, m.area ASC
                """).df()

            df_rep['획득점수'] = df_rep['획득점수'].fillna(0).astype(int)
            df_rep['현재포인트'] = df_rep['현재포인트'].fillna(0).astype(int)
            
            # --- 리포트 텍스트 구성 ---
            report_text = f"⛰️ **{target_month} 활동 요약 보고서**\n\n"
            report_text += "---\n\n"
            report_text += "📜 **회칙 확인하기**  \n"
            report_text += "https://www.band.us/band/85157163/post/4765 \n\n"
            
            report_text += "📂 **[이달의 산행 내역]**\n\n"
            if not ev_det.empty:
                # groupby에 album_url을 포함하여 링크 정보 유지
                for (d, title), group in ev_det.groupby(['d', 'title'], sort=False):
                    names = group['name'].tolist()
                    album = group['album_url'].iloc[0]
                    report_text += f"📍 **{d.strftime('%m/%d')} | {title}**  \n"
                    report_text += f"└ 참석({len(names)}명): {', '.join(names)}  \n"
                    # 앨범 링크가 존재할 경우에만 추가
                    if album and str(album).strip() not in ["None", ""]:
                        report_text += f"└ 📸 사진첩: {album}  \n"
                    report_text += "\n" # 행사 간 간격
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
            report_text += df_rep[['MemberID', '획득점수', '현재포인트', '회원상태']].rename(columns={'획득점수':'당월','현재포인트':'누적','회원상태':'상태'}).to_markdown(index=False)
            report_text += "\n\n---\n"

            # --- 화면 출력 섹션 ---
            t1, t2 = st.tabs(["📋 밴드 복사용 (텍스트)", "👀 미리보기 (시각화)"])
            
            with t1:
                st.info("아래 박스 안의 내용을 복사하여 밴드에 게시하세요.")
                # 밴드 복사용은 가독성을 위해 강조 기호(**) 제거 및 앨범 링크 포함 유지
                clean_report = report_text.replace("**", "")
                st.code(clean_report, language="text")
            
            with t2:
                st.markdown(report_text)

        except Exception as e:
            st.error(f"오류 발생: {e}")