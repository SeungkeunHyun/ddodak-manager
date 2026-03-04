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
        
        # [회원 명단 로드 및 호스트 매핑 초기화]
        @st.cache_data(ttl=300)
        def get_user_map(_db):
            try:
                df_members = _db.query("SELECT user_no, name FROM members ORDER BY name")
                return {str(r['user_no']): f"{r['name']} ({r['user_no']})" for _, r in df_members.iterrows()}
            except Exception:
                return {}

        user_map = get_user_map(self.db)
            
        def map_host_to_display(h):
            if pd.isna(h) or str(h).strip() in ["", "None", "nan"]:
                return None
            h_str = str(h).strip()
            if '(' in h_str and h_str.endswith(')'):
                return h_str
            if h_str in user_map:
                return user_map[h_str]
            for display in user_map.values():
                if display.startswith(h_str + ' ('):
                    return display
            return h_str
            
        df_e['host'] = df_e['host'].apply(map_host_to_display)
        
        host_options = list(user_map.values())
        existing_hosts = set(df_e['host'].dropna().unique())
        host_options.extend([eh for eh in existing_hosts if eh not in host_options])
        
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
            "host": st.column_config.SelectboxColumn("호스트", options=host_options, help="호스트(주최자)를 선택하세요. (이름 검색 가능)", width="medium"),
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
                
                # [저장/수정 로직 - Delta Update]
                cols = ", ".join([f'"{c}"' for c in updated.columns])
                placeholders = ", ".join(["?"] * len(updated.columns))
                sql = f"INSERT OR REPLACE INTO events ({cols}) VALUES ({placeholders})"
                
                import re
                
                count_saved = 0
                count_error = 0
                df_orig_indexed = df_filtered.set_index('event_id') if not df_filtered.empty else pd.DataFrame()

                for _, row in updated.iterrows():
                    try:
                        # event_id 추출 및 보정
                        event_id_raw = row.get('event_id')
                        event_id = str(event_id_raw).strip() if not pd.isna(event_id_raw) else ""
                        album_url_raw = row.get('album_url')
                        album_url = str(album_url_raw).strip() if not pd.isna(album_url_raw) else ""
                        
                        if event_id == "" and album_url != "":
                            # URL의 마지막 / 뒤의 숫자들 추출
                            match = re.search(r'/(\d+)/?$', album_url)
                            if not match:
                                match = re.search(r'(\d+)$', album_url)
                            
                            if match:
                                event_id = match.group(1)
                                
                        # host 파싱 ("이름 (user_no)" -> "user_no")
                        host_raw = row.get('host', None)
                        if pd.isna(host_raw) or str(host_raw).strip() in ["", "None", "nan"]:
                            host_val = None
                        else:
                            host_val = str(host_raw).strip()
                            if "(" in host_val and host_val.endswith(")"):
                                u_no_match = re.search(r'\(([^)]+)\)$', host_val)
                                if u_no_match:
                                    host_val = u_no_match.group(1)
                        
                        # 수동으로 튜플 생성하여 명시적으로 컬럼 순서 맞춤
                        row_data = []
                        for col in updated.columns:
                            if col == 'event_id':
                                row_data.append(event_id)
                            elif col == 'host':
                                row_data.append(host_val)
                            else:
                                row_data.append(row[col])
                                
                        # Delta Check
                        if df_orig_indexed.empty or event_id not in df_orig_indexed.index:
                            # New record
                            self.db.execute(sql, tuple(row_data))
                            count_saved += 1
                            continue
                        
                        # Existing record - Compare
                        try:
                            orig_row = df_orig_indexed.loc[event_id]
                            # Handle duplicate IDs gracefully (if any)
                            if isinstance(orig_row, pd.DataFrame):
                                orig_row = orig_row.iloc[0]
                        except KeyError:
                            # Fail-safe fallback
                            self.db.execute(sql, tuple(row_data))
                            count_saved += 1
                            continue
                            
                        curr_dict = {col: (event_id if col=='event_id' else row[col]) for col in updated.columns}
                        orig_dict = orig_row.to_dict()
                        
                        is_changed = False
                        for k, v in curr_dict.items():
                            orig_v = orig_dict.get(k)
                            if str(v) != str(orig_v):
                                is_changed = True
                                break
                        
                        if is_changed:
                             self.db.execute(sql, tuple(row_data))
                             count_saved += 1
                    except Exception as e:
                        st.error(f"⚠️ 행 데이터 처리 중 오류 발생: {str(e)}")
                        count_error += 1
                        continue
                    
                import time
                time.sleep(0.5)
                
                # Clear cache to ensure dashboard/analysis reflects changes immediately
                st.cache_data.clear()
                
                # Force editor refresh by clearing session state
                if "event_editor" in st.session_state:
                    del st.session_state["event_editor"]
                
                msg = f"""
                ✅ **일정 반영 완료!**
                - 💾 **저장/수정**: {count_saved}건 (변경됨)
                - 🗑️ **삭제**: {len(deleted_ids)}건
                """
                if count_error > 0:
                    msg += f"\n- ⚠️ **오류 발생**: {count_error}건 (저장 실패)"
                    st.warning(msg)
                else:
                    st.success(msg)
                st.rerun()
