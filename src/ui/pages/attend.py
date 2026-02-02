import streamlit as st
import pandas as pd
from src.ui.layout import Layout

# =========================================================
# Page: Attendance (참가 체크)
# =========================================================

class AttendancePage:
    def __init__(self, db):
        self.db = db

    def render(self):
        Layout.render_manual("참가 체크")
        st.header("🏃 참석자 명단 체크")
        
        # 목록 데이터 로드
        ev_list = self.db.query("SELECT event_id, date, title, host FROM events ORDER BY date DESC")
        mb_list = self.db.query("SELECT user_no, birth_year, name, area FROM members WHERE role<>'exmember' ORDER BY birth_year, name")
        
        if ev_list.empty: return st.warning("일정을 먼저 등록하세요.")
        
        # 일정 선택
        ev_labels = ev_list.apply(lambda r: f"{r['date']} | {r['title']}", axis=1).tolist()
        sel_label = st.selectbox(f"🎯 산행 선택 (총 {len(ev_list)}건)", ev_labels)
        
        selected_event = ev_list.iloc[ev_labels.index(sel_label)]
        sel_ev_id = selected_event['event_id']
        host_id = str(selected_event['host']) if selected_event['host'] else None
        
        # 기존 참석자 로드
        existing = self.db.query("SELECT user_no FROM attendees WHERE event_id=?", (str(sel_ev_id),))['user_no'].tolist()
        
        # 표시 포맷 (생년/이름/지역)
        mb_list['display'] = mb_list.apply(lambda r: f"{r['birth_year']}/{r['name']}/{r['area']}", axis=1)
        
        # 공지자 표시 로직
        if host_id:
            host_row = mb_list[mb_list['user_no'].astype(str) == host_id]
            if not host_row.empty:
                host_name = host_row['display'].iloc[0]
                st.markdown(f"👑 **공지자**: :orange[{host_name}]")
        
        # 멀티 셀렉트로 참석자 체크
        selected = st.multiselect(
            f"🏃 참석자 선택 (대상: {len(mb_list)}명)", 
            options=mb_list['display'].tolist(),
            default=mb_list[mb_list['user_no'].isin(existing)]['display'].tolist(),
            key=f"attendees_{sel_ev_id}" 
        )
        
        st.info(f"💡 현재 선택된 인원: **{len(selected)}명**")
        
        # [Clip Button for Report]
        if selected:
            clip_title = f"{selected_event['title']} 참석자"
            clip_content = f"📍 **{selected_event['title']}** ({selected_event['date']})\n"
            clip_content += f"참석({len(selected)}명): {', '.join([s.split('/')[1] for s in selected])}"
            
            # 우측 정렬을 위한 컬럼 배치
            _, col_clip = st.columns([3, 1])
            with col_clip:
                self._add_clip_button(f"clip_attend_{sel_ev_id}", clip_title, clip_content)

        if st.button("✅ 참석 명단 최종 확정", type="primary"):
            with st.spinner("⏳ 참석 명단을 업데이트 중입니다..."):
                # 기존 내역 삭제 후 재생성 (Bulk Insert)
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

    def _add_clip_button(self, key, title, content):
        """리포트 생성을 위한 클립보드 버튼 (Helper)"""
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
