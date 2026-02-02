import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta
from src.config import Config
from src.ui.layout import Layout
from src.ui.styles import Styles

# =========================================================
# Page: Home (Dashboard)
# =========================================================

class HomePage:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai

    def render(self):
        Layout.render_manual("??)
        
        # ??댄????좊땲硫붿씠???④낵 ?곸슜 (CSS Class ?쒖슜 媛??
        st.title("?곤툘 ?먮떏?먮떏 ?곗븙??)
        
        # [?곗씠??濡쒕뱶]
        # v2.24.2 Hotfix: df_summary ?뺤쓽 蹂듦뎄
        df_summary = self.db.query("SELECT * FROM v_member_attendance_summary")
        # v2.24.4 Hotfix: active_members ?뺤쓽 蹂듦뎄
        active_members = df_summary[df_summary['?뚯썝?곹깭'] != 'exmember']
        
        # [??援ъ“]
        tab_overview, tab_demo, tab_activity = st.tabs(["?뱤 ??쒕낫??(Overview)", "?뫁 ?뚯썝 援ъ꽦 (Demographics)", "?룇 紐낆삁???꾨떦 (Hall of Fame)"])
        
        # --- [TAB 1] 醫낇빀 ?꾪솴 (Overview) ---
        with tab_overview:
            self._render_overview(df_summary)

        # --- [TAB 2] ?뚯썝 ?듦퀎 (Demographics) ---
        with tab_demo:
            self._render_demographics(df_summary)

        # --- [TAB 3] 紐낆삁???꾨떦 (Hall of Fame) ---
        with tab_activity:
            self._render_hall_of_fame(df_summary, active_members)

    def _render_overview(self, df_summary):
        # 1. KPI Cards
        total_members = self.db.query("SELECT COUNT(*) FROM members WHERE role<>'exmember'").iloc[0, 0]
        
        df_points = self.db.query("SELECT user_no, point FROM members WHERE role<>'exmember'")
        total_base = df_points['point'].sum() if not df_points.empty else 0
        event_score = self.db.query("SELECT SUM(e.score) FROM events e JOIN attendees a ON e.event_id = a.event_id").iloc[0,0]
        if pd.isna(event_score): event_score = 0
        total_activity_score = total_base + event_score
        
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        active_count = self.db.query(f"SELECT COUNT(DISTINCT user_no) FROM attendees a JOIN events e ON a.event_id = e.event_id WHERE e.date >= '{three_months_ago}'").iloc[0,0]

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(Styles.card_template(f"""<div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">珥??뚯썝??/div><div style="font-size: 32px; font-weight: bold;">{total_members}紐?/div>"""), unsafe_allow_html=True)
        with c2:
            st.markdown(Styles.card_template(f"""<div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">理쒓렐 ?쒕룞 ?뚯썝</div><div style="font-size: 32px; font-weight: bold; color: #4ade80;">{active_count}紐?/div>"""), unsafe_allow_html=True)
        with c3:
            st.markdown(Styles.card_template(f"""<div style="font-size: 16px; opacity: 0.8; margin-bottom: 5px;">?꾩쟻 ?쒕룞 ?먯닔</div><div style="font-size: 32px; font-weight: bold; color: #ffd700;">{int(total_activity_score):,}??/div>"""), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 2. Events & Weather
        c3, c4 = st.columns([1.2, 1])
        
        with c3:
            st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
            st.subheader("?뱟 ?ㅺ??ㅻ뒗 ?고뻾")
            today = datetime.now().strftime("%Y-%m-%d")
            upcoming = self.db.query(f"SELECT * FROM events WHERE date >= '{today}' ORDER BY date ASC LIMIT 3")
            
            if not upcoming.empty:
                for _, row in upcoming.iterrows():
                    d_day = (pd.to_datetime(row['date']) - pd.to_datetime(today)).days
                    badge = f"D-{d_day}" if d_day > 0 else "D-Day"
                    badge_color = "#ef4444" if d_day <= 3 else "#3b82f6"
                    
                    st.markdown(f"""
                    <div style="background-color: rgba(255,255,255,0.05); padding: 12px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {badge_color}; cursor: pointer; transition: background-color 0.2s;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: bold; font-size: 16px; color: #fff;">{row['title']}</div>
                            <div style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">{badge}</div>
                        </div>
                        <div style="color: #ccc; font-size: 13px; margin-top: 4px;">?뱟 {row['date']} &nbsp;|&nbsp; ?몣 {row['host']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("?덉젙???고뻾???놁뒿?덈떎.")
            st.markdown("</div>", unsafe_allow_html=True)

        with c4:
            st.markdown(f"""<div style="background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 15px;">""", unsafe_allow_html=True)
            st.subheader("?뙟截??쒖슱 ?좎뵪")
            self._render_weather_forecast()
            st.markdown("</div>", unsafe_allow_html=True)

        # 3. AI Briefing
        st.markdown("---")
        st.subheader("?쨼 AI 二쇨컙 釉뚮━??)
        if st.button("???대쾲 二??고뻾 & ?좎뵪 釉뚮━???앹꽦"):
            check_events = self.db.query(f"SELECT * FROM events WHERE date >= '{today}' LIMIT 1")
            if check_events.empty:
                st.warning("?덉젙???고뻾 ?곗씠?곌? ?놁뼱 釉뚮━?묒쓣 ?앹꽦?????놁뒿?덈떎.")
            else:
                self._show_ai_briefing(upcoming)

    def _render_demographics(self, df_summary):
        c3, c4 = st.columns(2)
        df_dist = self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")
        
        with c3:
            st.markdown("### ?뱟 ?곕룄蹂??몄썝 (Birth Year)")
            st.markdown("""
            <div style="display: flex; gap: 15px; margin-bottom: 10px; font-size: 14px; color: #eee; background-color: rgba(255,255,255,0.1); padding: 8px 12px; border-radius: 8px; width: fit-content;">
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #3b82f6; border-radius: 50%; margin-right: 6px;"></span>
                    <span>?⑥꽦 (Male)</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="display: inline-block; width: 12px; height: 12px; background-color: #ec4899; border-radius: 50%; margin-right: 6px;"></span>
                    <span>?ъ꽦 (Female)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if not df_dist.empty:
                # ?곗씠???꾩쿂由?濡쒖쭅? ?숈씪
                df_dist['gender_norm'] = df_dist['gender'].astype(str).str.upper().str.strip()
                gender_map = {'M': 'M', 'MALE': 'M', 'MAN': 'M', '??: 'M', '?⑥꽦': 'M', 'F': 'F', 'FEMALE': 'F', 'WOMAN': 'F', 'W': 'F', '??: 'F', '?ъ꽦': 'F'}
                df_dist['gender_final'] = df_dist['gender_norm'].map(gender_map).fillna('U')
                
                age_gender = df_dist.groupby(['birth_year', 'gender_final']).size().unstack(fill_value=0)
                if 'M' not in age_gender.columns: age_gender['M'] = 0
                if 'F' not in age_gender.columns: age_gender['F'] = 0
                age_gender['total'] = age_gender.sum(axis=1)
                age_gender = age_gender.sort_index()

                max_count = age_gender['total'].max()
                
                html_balls = '<div style="background-color: rgba(0,0,0,0.5); padding: 15px; border-radius: 10px; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; align-items: center;">'
                for year, row in age_gender.iterrows():
                    year = int(year)
                    count = int(row['total'])
                    m_count = int(row['M'])
                    f_count = int(row['F'])
                    
                    m_pct = (m_count / count * 100) if count > 0 else 0
                    bg_style = f"background: linear-gradient(135deg, #3b82f6 {m_pct}%, #ec4899 {m_pct}%);"
                    
                    size = 50 + (count / max_count) * 50 if max_count > 0 else 50
                    font_size = 14 + (count / max_count) * 6
                    
                    # Hover effect added via CSS class (already in Styles)
                    html_balls += f"""<div style="width: {size}px; height: {size}px; border-radius: 50%; {bg_style} color: white; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: transform 0.2s; border: 2px solid rgba(255,255,255,0.2);" title="{year}?꾩깮: {count}紐?(??{m_count}/??{f_count})"><span style="font-weight: bold; font-size: {font_size}px; line-height: 1; text-shadow: 1px 1px 2px black;">{year}??/span><span style="font-size: {font_size*0.7}px; opacity: 0.9; text-shadow: 1px 1px 2px black;">{count}紐?/span></div>"""
                html_balls += '</div>'
                st.markdown(html_balls, unsafe_allow_html=True)

        with c4:
            st.subheader("?슶 ?깅퀎 遺꾪룷 (Gender)")
            if not df_dist.empty:
                gender_counts = df_dist['gender_final'].value_counts()
                total = len(df_dist)
                m_count, f_count, u_count = gender_counts.get('M', 0), gender_counts.get('F', 0), gender_counts.get('U', 0)
                m_pct = (m_count / total * 100) if total > 0 else 0
                f_pct = (f_count / total * 100) if total > 0 else 0
                u_pct = (u_count / total * 100) if total > 0 else 0
                
                # ... (Gender HTML - Same as existing)
                # Use sqrt for area proportionality to make size differences less extreme but accurate visually
                import math
                max_val = max(m_count, f_count) if max(m_count, f_count) > 0 else 1
                base_size = 60
                scale_factor = 60
                
                m_size = int(base_size + (math.sqrt(m_count) / math.sqrt(max_val)) * scale_factor) if m_count > 0 else 40
                f_size = int(base_size + (math.sqrt(f_count) / math.sqrt(max_val)) * scale_factor) if f_count > 0 else 40
                u_size = 40  # Unknown is typically small

                html_gender = f"""<div style="background-color: rgba(0,0,0,0.5); border-radius: 10px; height: 100%; padding: 20px; position: relative; min-height: 350px; display: flex; flex-direction: column; align-items: center;">
    <!-- Title -->
    <div style="width: 100%; text-align: center; margin-bottom: 30px; color: #eee; font-weight: bold; font-size: 18px;">?뽳툘 ?깅퀎 遺꾪룷 (Balance Scale)</div>
    <!-- Scale Container -->
    <div style="position: relative; width: 100%; height: 220px; display: flex; justify-content: center;">
        <!-- Fulcrum (Triangle Base) -->
        <div style="position: absolute; top: 40px; width: 0; height: 0; border-left: 15px solid transparent; border-right: 15px solid transparent; border-bottom: 30px solid #555; z-index: 1;"></div>
        <!-- Unknown (Center Circle) -->
        <div style="position: absolute; top: 30px; z-index: 2; width: {u_size}px; height: {u_size}px; background-color: #9ca3af; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.5); border: 2px solid #555;">
             <div style="text-align: center; line-height: 1;">
                <div style="font-size: 12px; color: #fff; font-weight: bold;">??/div>
                <div style="font-size: 10px; color: #eee;">{u_count}</div>
             </div>
        </div>
        <!-- Beam (Crossbar) -->
        <div style="position: absolute; top: 40px; width: 80%; height: 6px; background: linear-gradient(90deg, #444, #666, #444); border-radius: 4px; z-index: 0;"></div>
        <!-- Left Pan (Male) -->
        <div style="position: absolute; left: 10%; top: 40px; display: flex; flex-direction: column; align-items: center;">
            <!-- String -->
            <div style="width: 2px; height: 40px; background-color: #888;"></div>
            <!-- Circle -->
            <div style="width: {m_size}px; height: {m_size}px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, #60a5fa, #2563eb); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.4); border: 2px solid rgba(255,255,255,0.1); transition: transform 0.3s;">
                <div style="text-align: center; color: white;">
                    <div style="font-size: 20px;">?귨툘</div>
                    <div style="font-weight: bold; font-size: 16px;">{m_count}</div>
                    <div style="font-size: 11px; opacity: 0.8;">{m_pct:.1f}%</div>
                </div>
            </div>
        </div>
        <!-- Right Pan (Female) -->
        <div style="position: absolute; right: 10%; top: 40px; display: flex; flex-direction: column; align-items: center;">
            <!-- String -->
            <div style="width: 2px; height: 40px; background-color: #888;"></div>
            <!-- Circle -->
            <div style="width: {f_size}px; height: {f_size}px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, #f472b6, #db2777); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(219, 39, 119, 0.4); border: 2px solid rgba(255,255,255,0.1); transition: transform 0.3s;">
                <div style="text-align: center; color: white;">
                    <div style="font-size: 20px;">?截?/div>
                    <div style="font-weight: bold; font-size: 16px;">{f_count}</div>
                    <div style="font-size: 11px; opacity: 0.8;">{f_pct:.1f}%</div>
                </div>
            </div>
        </div>
    </div>
    <!-- Legend -->
    <div style="margin-top: auto; width: 100%; display: flex; justify-content: center; gap: 15px; font-size: 12px; color: #ccc; background-color: rgba(255,255,255,0.05); padding: 8px; border-radius: 8px;">
        <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #3b82f6; border-radius: 50%; margin-right: 5px;"></span>?⑥꽦 (Male)</div>
        <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #ec4899; border-radius: 50%; margin-right: 5px;"></span>?ъ꽦 (Female)</div>
        <div style="display: flex; align-items: center;"><span style="width: 10px; height: 10px; background-color: #9ca3af; border-radius: 50%; margin-right: 5px;"></span>誘몄긽 (Unknown)</div>
    </div>
    <div style="margin-top: 5px; font-size: 11px; color: #888;">* ?숆렇?쇰? ?ш린???몄썝?섏뿉 鍮꾨??⑸땲??</div>
</div>"""
                st.markdown(html_gender, unsafe_allow_html=True)
        
        st.divider()
        
        # Map logic (Truncated for brevity, assuming standard map logic)
        self._render_map(df_summary)

    def _render_map(self, df_summary):
        c1, c2 = st.columns(2)
        # ... (Map coordinates logic)
        coords = {
                "?쒖슱": [37.5665, 126.9780], "寃쎄린": [37.4138, 127.5183], "?몄쿇": [37.4563, 126.7052],
                "愿묐챸": [37.4784, 126.8643], "?덉뼇": [37.3910, 126.9269], "怨좎뼇": [37.6584, 126.8320], "?쇱궛": [37.6584, 126.8320],
                "遺泥?: [37.5034, 126.7660], "?쒗씎": [37.3801, 126.8031], "?덉궛": [37.3195, 126.8308],
                "?깅궓": [37.4200, 127.1265], "遺꾨떦": [37.3827, 127.1189], "?⑹씤": [37.2410, 127.1775],
                "?섏썝": [37.2636, 127.0286], "?붿꽦": [37.1995, 126.8315], "?⑥뼇二?: [37.6360, 127.2165],
                "援щ줈": [37.4954, 126.8874], "湲덉쿇": [37.4565, 126.8954], "愿??: [37.4782, 126.9515], "?쒖슱愿??: [37.4782, 126.9515],
                "?숈옉": [37.5124, 126.9393], "?щ떦": [37.4765, 126.9816], "?곷벑??: [37.5264, 126.8962],
                "留덊룷": [37.5636, 126.9019], "?쒕?臾?: [37.5791, 126.9368], "???: [37.6027, 126.9291],
                "媛뺤꽌": [37.5509, 126.8495], "?묒쿇": [37.5169, 126.8660],
                "媛뺣궓": [37.5172, 127.0473], "?쒖큹": [37.4837, 127.0324], "?≫뙆": [37.5145, 127.1066], "媛뺣룞": [37.5301, 127.1238],
                "?몄썝": [37.6542, 127.0568], "?꾨큺": [37.6688, 127.0471], "源??: [37.6152, 126.7157]
            }
        
        df_map = df_summary['吏??].value_counts().reset_index()
        df_map.columns = ['area', 'count']
        
        def get_coords(area_name):
            if area_name in coords: return coords[area_name]
            for k in coords:
                if k in area_name: return coords[k]
            return [37.5665, 126.9780]

        df_map['lat'] = df_map['area'].apply(lambda x: get_coords(x)[0])
        df_map['lon'] = df_map['area'].apply(lambda x: get_coords(x)[1])
        
        with c1: 
            fig_map = px.scatter_mapbox(
                df_map, lat="lat", lon="lon", size="count", color="count",
                hover_name="area", size_max=25, zoom=8, 
                center={"lat": 37.5, "lon": 127.0},
                title='?뱧 吏??遺꾪룷 (?쒖슱/寃쎄린)',
                mapbox_style="open-street-map", height=400
            )
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
            st.markdown("""<div style="text-align: right; font-size: 11px; color: #aaa; margin-top: -10px;">* ?먯쓽 ?ш린? ?됱긽? ?대떦 吏??쓽 ?뚯썝 ?섏뿉 鍮꾨??⑸땲??</div>""", unsafe_allow_html=True)
            
        with c2:
            st.subheader("?룞截?Top 5 ?쒕룞 吏??)
            top_regions = df_map.head(5)
            max_reg = top_regions['count'].max()
            
            bar_html = "<div style='background-color: rgba(0,0,0,0.5); border-radius: 10px; padding: 15px;'>"
            for _, row in top_regions.iterrows():
                pct = (row['count'] / max_reg) * 100
                bar_html += f"""<div style="margin-bottom: 12px;"><div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span style="font-weight: bold; color: #eee;">{row['area']}</span><span style="font-weight: bold; color: #4da6ff;">{row['count']}紐?/span></div><div style="width: 100%; background-color: #444; border-radius: 6px; height: 12px;"><div style="width: {pct}%; background: linear-gradient(90deg, #2575fc, #6a11cb); height: 100%; border-radius: 6px;"></div></div></div>"""
            bar_html += "</div>"
            st.markdown(bar_html, unsafe_allow_html=True)


    def _render_hall_of_fame(self, df_summary, active_members):
        now = datetime.now(Config.KST)
        cur_month_str = now.strftime('%Y-%m')
        st.subheader(f"?룇 {now.month}?붿쓽 紐낆삁???꾨떦")
        
        c_host, c_attend, c_event = st.columns(3)
        
        def get_rank_html(rank, text, subtext):
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"] 
            color = colors[rank] if rank < 3 else "#FFFFFF"
            rank_num = rank + 1
            return f"""
            <div style="background-color: rgba(0,0,0,0.4); padding: 10px; border-radius: 8px; margin-bottom: 6px; display: flex; align-items: center;">
                <div style="width: 30px; height: 30px; border-radius: 50%; background-color: {color}; color: #000; font-weight: bold; display: flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0;">{rank_num}</div>
                <div style="flex-grow: 1;"><b>{text}</b></div>
                <div style="font-size: 14px; color: #eee;">{subtext}</div>
            </div>
            """

        with c_host:
            st.markdown("##### ?뱽 ?대떖??怨듭???)
            try:
                df_host = self.db.query(f"SELECT m.name, COUNT(*) as cnt FROM events e JOIN members m ON e.host = m.user_no WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' GROUP BY m.name ORDER BY cnt DESC LIMIT 3")
                if not df_host.empty:
                    for idx, row in df_host.iterrows():
                        st.markdown(get_rank_html(idx, row['name'], f"{row['cnt']}??), unsafe_allow_html=True)
                else:
                    st.caption("?곗씠???놁쓬")
            except Exception as e:
                st.error(f"Error: {e}")

        with c_attend:
            st.markdown("##### ?룂 ?대떖??李몄꽍??)
            try:
                top_scorers = active_members.sort_values(by='?띾뱷?먯닔', ascending=False).head(3)
                if not top_scorers.empty:
                    for i in range(len(top_scorers)):
                        row = top_scorers.iloc[i]
                        st.markdown(get_rank_html(i, row['MemberID'], f"{int(row['?띾뱷?먯닔'])}??), unsafe_allow_html=True)
                else:
                    st.caption("?곗씠???놁쓬")
            except Exception as e:
                st.error(f"Error: {e}")

        with c_event:
            st.markdown("##### ?뵦 ?대떖???멸린 ?고뻾")
            try:
                df_pop = self.db.query(f"SELECT e.title, COUNT(a.user_no) as cnt FROM events e JOIN attendees a ON e.event_id = a.event_id WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' GROUP BY e.title ORDER BY cnt DESC LIMIT 3")
                if not df_pop.empty:
                    for idx, row in df_pop.iterrows():
                        st.markdown(get_rank_html(idx, row['title'], f"{row['cnt']}紐?), unsafe_allow_html=True)
                else:
                    st.caption("?곗씠???놁쓬")
            except Exception as e:
                st.error(f"Error: {e}")
        
        st.divider()
        st.plotly_chart(px.bar(df_summary, x='?앸뀈', y='?꾩옱?ъ씤??, color='?뚯썝?곹깭', title='?럟 湲곗닔蹂??ъ씤??遺꾪룷'), use_container_width=True)

    def _render_weather_forecast(self):
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo"
            res = requests.get(url, timeout=3).json()
            
            if 'daily' in res:
                d = res['daily']
                dates = d['time']
                codes = d['weather_code']
                max_t = d['temperature_2m_max']
                min_t = d['temperature_2m_min']
                
                def get_icon(c):
                    if c == 0: return "?截?
                    if c in [1,2,3]: return "?뙠截?
                    if c in [45,48]: return "?뙧截?
                    if c in [51,53,55,61,63,65]: return "?뙢截?
                    if c in [71,73,75,77]: return "?꾬툘"
                    if c >= 95: return "?덌툘"
                    return "?뙜截?

                cols = st.columns(7)
                for i in range(7): 
                    with cols[i]:
                        dt = datetime.strptime(dates[i], "%Y-%m-%d")
                        dow = ["??, "??, "??, "紐?, "湲?, "??, "??][dt.weekday()]
                        
                        st.markdown(f"""<div style="text-align: center; font-size: 12px; background-color: rgba(255,255,255,0.05); padding: 5px; border-radius: 8px;">
                        {dt.strftime('%m/%d')}<br>({dow})<br>
                        <span style="font-size: 20px;">{get_icon(codes[i])}</span><br>
                        <span style="color: #ff6b6b;">{int(max_t[i])}째</span><br><span style="color: #4ecdc4;">{int(min_t[i])}째</span>
                        </div>""", unsafe_allow_html=True)
            else:
                st.error("?좎뵪 ?뺣낫 ?놁쓬")
        except Exception as e:
            st.error("?좎뵪 濡쒕뱶 ?ㅽ뙣")

    def _show_ai_briefing(self, upcoming_events):
        with st.chat_message("assistant"):
            with st.spinner("?쨼 ?곗븙??鍮꾩꽌媛 ?곗씠?곕? 遺꾩꽍 以묒엯?덈떎..."):
                try:
                    summary_text = f"?꾩옱 ?좎쭨: {datetime.now().strftime('%Y-%m-%d')}\n"
                    if not upcoming_events.empty:
                        for _, row in upcoming_events.iterrows():
                            summary_text += f"- ?쇱젙: {row['title']} ({row['date']}), ?대떦: {row['host']}\n"
                    
                    if self.ai and self.ai.model:
                        response = self.ai.model.generate_content(f"""
                        ?뱀떊? '?먮떏?먮떏 ?곗븙????AI 鍮꾩꽌?낅땲?? 
                        ?ㅼ쓬 ?쇱젙 ?뺣낫瑜?諛뷀깢?쇰줈 ?뚯썝?ㅼ뿉寃??꾪븷 ?쒓린李④퀬 ?좎슜??二쇨컙 釉뚮━?묒쓣 ?묒꽦?댁＜?몄슂.
                        ?좎뵪 ?멸툒? ?쇰컲?곸씤 怨꾩젅媛먯쓣 ?욎뼱???댁＜?몄슂.
                        
                        [?뺣낫]
                        {summary_text}
                        """)
                        st.markdown(response.text)
                    else:
                        st.info("AI 紐⑤뜽???곌껐?섏? ?딆븯?듬땲??")
                except Exception as e:
                    st.error(f"AI 遺꾩꽍 以??ㅻ쪟 諛쒖깮: {e}")
