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
        


        if st.button("✅ 참석 명단 최종 확정", type="primary"):
            with st.spinner("⏳ 참석 명단을 업데이트 중입니다..."):
                # [Delta Update Logic]
                # 1. Get current selection IDs
                current_selection_ids = set()
                # Create a map for faster lookup if list is large
                display_map = dict(zip(mb_list['display'], mb_list['user_no']))
                
                for val in selected:
                    if val in display_map:
                        current_selection_ids.add(display_map[val])
                
                # 2. Get existing IDs (already loaded in 'existing')
                existing_ids = set(existing)
                
                # 3. Calculate Diff
                to_add = current_selection_ids - existing_ids
                to_remove = existing_ids - current_selection_ids
                
                # 4. Execute Updates
                # ADD
                for u_no in to_add:
                    self.db.execute("INSERT INTO attendees (event_id, user_no) VALUES (?, ?)", (str(sel_ev_id), u_no))
                
                # REMOVE
                for u_no in to_remove:
                    self.db.execute("DELETE FROM attendees WHERE event_id=? AND user_no=?", (str(sel_ev_id), u_no))
                
                import time
                time.sleep(0.5)
                
                # Clear cache to ensure dashboard/analysis reflects changes immediately
                st.cache_data.clear()
                
                # Force widget to re-initialize with sorted 'default' by clearing session state
                if f"attendees_{sel_ev_id}" in st.session_state:
                    del st.session_state[f"attendees_{sel_ev_id}"]
                
                st.success(f"""
                ✅ **참석 정보 저장 완료!**
                - ➕ **추가**: {len(to_add)}명
                - ➖ **제외**: {len(to_remove)}명
                - 🏃 **최종 참석 인원**: {len(current_selection_ids)}명
                """)
                st.rerun()


