import streamlit as st
import pandas as pd
from src.ui.layout import Layout

# =========================================================
# Page: Events (산행 일정)
# =========================================================

class EventsPage:
    def __init__(self, db):
        self.db = db

    def render(self):
        Layout.render_manual("공지 관리")
        st.header("📅 공지 관리")
        df_e = self.db.query("SELECT * FROM events ORDER BY date DESC")
        
        # [일정 검색 및 필터]
        with st.expander("🔍 일정 검색 및 필터", expanded=True):
            c1, c2 = st.columns([1, 2])
            with c1:
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
        
        # [DB에 없는 임시 컬럼 제거]
        if 'month' in df_filtered.columns:
            df_filtered = df_filtered.drop(columns=['month'])
        
        # [컬럼 재정렬]
        target_order = ['date', 'title', 'host', 'event_id', 'album_url', 'description']
        final_order = [c for c in target_order if c in df_filtered.columns] + [c for c in df_filtered.columns if c not in target_order]

        column_config = {
            "date": st.column_config.DateColumn("행사일", format="YYYY-MM-DD", width="medium"),
            "title": st.column_config.TextColumn("공지명", width="large"),
            "event_id": st.column_config.TextColumn("ID", help="URL 입력 시 자동 추출되지만, 직접 입력도 가능합니다."),
        }
        
        updated = st.data_editor(
            df_filtered, 
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic", 
            key="event_editor",
            column_config=column_config,
            column_order=final_order 
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
                
                import re
                for _, row in updated.iterrows():
                    # event_id 추출 및 보정
                    event_id = str(row['event_id']).strip() if not pd.isna(row['event_id']) else ""
                    album_url = str(row['album_url']).strip() if not pd.isna(row['album_url']) else ""
                    
                    if event_id == "" and album_url != "":
                        # URL의 마지막 / 뒤의 숫자들 추출
                        match = re.search(r'/(\d+)/?$', album_url)
                        if not match:
                            match = re.search(r'(\d+)$', album_url)
                        
                        if match:
                            event_id = match.group(1)
                    
                    # 수동으로 튜플 생성하여 명시적으로 컬럼 순서 맞춤
                    # updated.columns 순서대로 데이터 구성
                    row_data = []
                    for col in updated.columns:
                        if col == 'event_id':
                            row_data.append(event_id)
                        else:
                            row_data.append(row[col])
                            
                    self.db.execute(sql, tuple(row_data))
                    
                import time
                time.sleep(0.5)
                
                st.success(f"""
                ✅ **일정 반영 완료!**
                - 💾 **저장/수정**: {len(updated)}건
                - 🗑️ **삭제**: {len(deleted_ids)}건
                """)
                st.rerun()
