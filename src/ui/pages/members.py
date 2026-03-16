import streamlit as st
import pandas as pd
from src.ui.layout import Layout

# =========================================================
# Page: Members (회원 관리)
# =========================================================

class MembersPage:
    def __init__(self, db):
        self.db = db

    def render(self):
        Layout.render_manual("회원 관리")
        st.header("👥 회원 명부 관리")
        df_all = self.db.query("SELECT * FROM members ORDER BY birth_year, name")
        
        # [고급 필터 & 검색]
        with st.expander("🔍 상세 검색 및 필터", expanded=True):
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2], gap="medium")
            with c1: 
                years = sorted(df_all['birth_year'].dropna().unique())
                sel_years = st.multiselect("🎂 생년", years, placeholder="전체 선택")
            with c2:
                areas = sorted(df_all['area'].dropna().unique())
                sel_areas = st.multiselect("📍 지역", areas, placeholder="전체 선택")
            with c3:
                roles = sorted(df_all['role'].dropna().unique())
                sel_roles = st.multiselect("👑 역할", roles, placeholder="전체 선택")
            with c4:
                search_name = st.text_input("👤 이름/설명 검색", placeholder="검색어를 입력하세요...")

        # 필터링 로직
        mask = pd.Series([True] * len(df_all))
        if sel_years: mask &= df_all['birth_year'].isin(sel_years)
        if sel_areas: mask &= df_all['area'].isin(sel_areas)
        if sel_roles: mask &= df_all['role'].isin(sel_roles)
        if search_name:
            mask &= (
                df_all['name'].str.contains(search_name, case=False, na=False) | 
                df_all['description'].str.contains(search_name, case=False, na=False)
            )
        
        df_filtered = df_all[mask]
        st.caption(f"검색 결과: **{len(df_filtered)}**명 (전체 {len(df_all)}명 중)")
        
        # 컬럼 순서
        target_order = ['birth_year', 'name', 'area', 'role', 'gender', 'user_no', 'phone', 'description', 'original_name', 'point', 'created_at', 'last_attended', 'profile_image_url']
        final_order = [c for c in target_order if c in df_filtered.columns] + [c for c in df_filtered.columns if c not in target_order]
        
        column_config = {
            "birth_year": st.column_config.NumberColumn("생년", format="%d", width="small"),
            "name": st.column_config.TextColumn("이름", width="medium"),
            "area": st.column_config.TextColumn("지역", width="small"),
            "role": st.column_config.SelectboxColumn("역할", options=['member', 'admin', 'staff', 'exmember'], width="small"),
            "user_no": st.column_config.TextColumn("ID", disabled=False), 
            "last_attended": st.column_config.Column("최근 참석일", disabled=True, help="참가 체크 시 자동으로 업데이트됩니다."),
        }
        
        updated = st.data_editor(
            df_filtered, 
            use_container_width=True, 
            hide_index=True, 
            num_rows="dynamic", 
            key="member_editor",
            column_config=column_config,
            column_order=final_order 
        )
        
        if st.button("💾 회원 정보 최종 저장"):
            with st.spinner("⏳ 회원 정보를 저장하고 있습니다..."):
                # [삭제 로직]
                orig_ids_in_view = set(df_filtered['user_no'].astype(str).tolist())
                curr_ids_in_view = set(updated['user_no'].astype(str).tolist())
                deleted_ids = orig_ids_in_view - curr_ids_in_view
                
                for d_id in deleted_ids:
                    self.db.execute("DELETE FROM members WHERE user_no = ?", (d_id,))
                
                # [저장/수정 로직 - Delta Update]
                cols = ", ".join([f'"{c}"' for c in updated.columns])
                placeholders = ", ".join(["?"] * len(updated.columns))
                sql = f"INSERT OR REPLACE INTO members ({cols}) VALUES ({placeholders})"
                
                count_saved = 0
                
                # Comparison for delta
                # Ensure index uniqueness for searching
                df_orig_indexed = df_filtered.set_index('user_no')
                
                for _, row in updated.iterrows():
                    user_id = row['user_no']
                    
                    # 1. New Record
                    if user_id not in df_orig_indexed.index:
                        self.db.execute(sql, tuple(row))
                        count_saved += 1
                        continue
                        
                    # 2. Existing Record - Check for changes
                    orig_row = df_orig_indexed.loc[user_id]
                    
                    curr_dict = row.to_dict()
                    orig_dict = orig_row.to_dict()
                    
                    def normalize_val(val):
                        if pd.isna(val) or val is None or str(val).strip() == "" or str(val).strip() == "nan":
                            return ""
                        # Handle float representations of integers (e.g. 1980.0 -> "1980")
                        s = str(val).strip()
                        if s.endswith(".0"):
                            return s[:-2]
                        return s
                    
                    is_changed = False
                    for k, v in curr_dict.items():
                        orig_v = orig_dict.get(k)
                        if normalize_val(v) != normalize_val(orig_v):
                            is_changed = True
                            break
                    
                    if is_changed:
                        self.db.execute(sql, tuple(row))
                        count_saved += 1

                import time
                time.sleep(0.5)
                
                # Clear cache to ensure dashboard/analysis reflects changes immediately
                st.cache_data.clear()
                
                # 통계와 팝업 토스트 추가 (MCP UI)
                if count_saved == 0 and len(deleted_ids) == 0:
                    st.toast("변경 사항이 없습니다.", icon="👀")
                else:    
                    # Force editor refresh by clearing session state
                    if "member_editor" in st.session_state:
                        del st.session_state["member_editor"]
                    
                    st.toast(f"저장 성공: 변경 {count_saved}건, 삭제 {len(deleted_ids)}건 반영", icon="💾")
                    
                    msg = f"""
                    ✅ **작업 완료!**
                    - 💾 **저장/수정**: {count_saved}건 (실제 변경됨)
                    - 🗑️ **삭제**: {len(deleted_ids)}건
                    """
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
