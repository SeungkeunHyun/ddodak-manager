import streamlit as st
import pandas as pd
from datetime import datetime
from src.config import Config
from src.ui.layout import Layout

# =========================================================
# Page: Report (보고서 생성)
# =========================================================

class ReportPage:
    def __init__(self, db):
        self.db = db

    def render(self):
        Layout.render_manual("보고서 생성")
        st.header("📊 활동 결과 보고서")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1], gap="large")
        with col1: rules = st.text_input("🔗 회칙 링크", value=Config.RULES_URL)
        with col2: target_month = st.text_input("📅 대상 월 (YYYY-MM)", value=datetime.now(Config.KST).strftime('%Y-%m'))
        
        # [Dashboard Clips Selection]
        clips_to_include = []
        if 'report_clips' in st.session_state and st.session_state['report_clips']:
            with st.expander("📋 대시보드 스크랩 (선택하여 추가)", expanded=True):
                st.caption("대시보드에서 '리포트에 담기' 한 내용을 선택하세요.")
                c_clips = st.columns(2)
                for i, clip in enumerate(st.session_state['report_clips']):
                    if c_clips[i % 2].checkbox(f"📌 {clip['title']}", value=True, key=f"use_clip_{i}"):
                        clips_to_include.append(clip['content'])
        
        if st.button("📝 보고서 생성", type="primary", use_container_width=True):
            # 산행 내역 쿼리 (exmember 제외)
            df_ev = self.db.query(f"SELECT e.date, e.title, e.album_url, m.birth_year, m.name FROM events e JOIN attendees a ON e.event_id=a.event_id JOIN members m ON a.user_no=m.user_no WHERE strftime('%Y-%m', e.date)='{target_month}' AND m.role != 'exmember' ORDER BY e.date, m.birth_year, m.name")
            # 전체 활동 통계 쿼리
            df_rep_raw = self.db.query("SELECT * FROM v_member_attendance_summary ORDER BY MemberID ASC")
            # exmember 제외
            df_rep = df_rep_raw[df_rep_raw['회원상태'] != 'exmember'].copy()
            
            # 결측치 처리
            df_rep['획득점수'] = df_rep['획득점수'].fillna(0).astype(int)
            df_rep['현재포인트'] = df_rep['현재포인트'].fillna(0).astype(int)

            sp = "  " # 마크다운 줄바꿈
            report = f"🔗 **또닥또닥 회칙 안내**{sp}\n{rules}{sp}\n\n"
            report += f"⛰️ **{target_month} 활동 요약 보고서**{sp}\n────────────────{sp}\n\n"
            
            # [Added] Dashboard Clips
            if clips_to_include:
                for c in clips_to_include:
                    report += f"{c}{sp}\n"
                report += f"\n"
            
            # 1. 산행 기록
            report += f"📅 **[이달의 산행 기록]**{sp}\n"
            if not df_ev.empty:
                for (d, t), g in df_ev.groupby(['date', 'title'], sort=False):
                    report += f"📍 {d} | {t}{sp}\n└ 참석({len(g)}명): {', '.join(g['name'].tolist())}{sp}\n"
                    if g['album_url'].iloc[0]: report += f"└ 📸 사진첩: {g['album_url'].iloc[0]}{sp}\n"
                    report += f"\n"
            else: report += f"활동 내역 없음{sp}\n\n"
            
            # 2. 시상 및 마일스톤
            winners = []
            for _, r in df_rep.iterrows():
                curr, prev = r['현재포인트'], r['현재포인트'] - r['획득점수']
                for th, msg in [(100, "💯 특별시상"), (50, "🎫 50점 돌파"), (30, "🎫 30점 돌파"), (10, "🎫 10점 돌파")]:
                    if curr >= th and prev < th: winners.append(f"✨ {r['MemberID']} ({curr}점) {msg}")
            
            report += f"🏆 **[이달의 시상 현황]**{sp}\n" + (f"{sp}\n".join(winners) if winners else "해당사항 없음") + f"{sp}\n\n"
            
            # 2.5 신입 첫 산행 축하 (exmember 제외)
            df_first = self.db.query(f"""
                SELECT m.name, MIN(e.date) as first_date 
                FROM attendees a 
                JOIN events e ON a.event_id = e.event_id 
                JOIN members m ON a.user_no = m.user_no 
                WHERE m.role != 'exmember'
                GROUP BY m.user_no, m.name 
                HAVING strftime('%Y-%m', first_date) = '{target_month}'
            """)
            celebrations = [f"🎊 {row['name']}님 (첫 참석 환영합니다!)" for _, row in df_first.iterrows()]
            report += f"🎉 **[첫 참석을 반겨요]**{sp}\n" + (f"{sp}\n".join(celebrations) if celebrations else "없음") + f"{sp}\n\n"
            
            # 3. 경고 (미활동) 안내
            sleep_warning = df_rep[df_rep['회원상태'].str.contains('😴🚨', na=False)]['MemberID'].tolist()
            new_warning = df_rep[df_rep['회원상태'].str.contains('🌱🚨', na=False)]['MemberID'].tolist()
            
            report += f"🚨 **[활동 관리 안내]**{sp}\n"
            report += f"😴 **장기 미참석(경고)**:  \n{', '.join(sleep_warning) if sleep_warning else '없음'}{sp}\n"
            report += f"🌱 **신입 미참석(경고)**:  \n{', '.join(new_warning) if new_warning else '없음'}{sp}\n\n"

            # 4. 전체 점수 현황 테이블
            report += f"🔢 **[전체 회원 누적 점수 현황]**{sp}\n"
            report += f"| 회원명 | 이번달 점수 | 누적 점수 | 상태 |{sp}\n"
            report += f"| :--- | ---: | ---: | :---: |{sp}\n"
            for _, r in df_rep.iterrows():
                report += f"| {r['MemberID']} | {r['획득점수']}점 | {r['현재포인트']}점 | {r['회원상태']} |{sp}\n"
            
            report += f"\n────────────────{sp}\n건강하게 다음 산행에서 뵙겠습니다! ⛰️"
            
            # 결과 표시 (복사 및 미리보기 탭)
            t1, t2 = st.tabs(["📋 밴드 복사용", "👀 미리보기"])
            with t1: st.code(report.replace("**", ""), language="text")
            with t2: st.markdown(report)
