import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from src.config import Config

# =========================================================
# 2. Service Layer - Analysis
# 복잡한 통계 연산 API 호출, 데이터 가공을 담당합니다.
# =========================================================

class AnalysisService:
    def __init__(self, db_service):
        self.db = db_service

    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def get_overview_kpis(_self):
        """
        종합 현황 KPI (총 회원, 최근 활동, 누적 포인트) 계산
        """
        total_members = _self.db.query("SELECT COUNT(*) FROM members WHERE role<>'exmember'").iloc[0, 0]
        
        df_points = _self.db.query("SELECT user_no, point FROM members WHERE role<>'exmember'")
        total_base = df_points['point'].sum() if not df_points.empty else 0
        event_score = _self.db.query("SELECT SUM(e.score) FROM events e JOIN attendees a ON e.event_id = a.event_id").iloc[0,0]
        if pd.isna(event_score): event_score = 0
        total_activity_score = total_base + event_score
        
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        active_count = _self.db.query(f"SELECT COUNT(DISTINCT user_no) FROM attendees a JOIN events e ON a.event_id = e.event_id WHERE e.date >= '{three_months_ago}'").iloc[0,0]

        return total_members, active_count, total_activity_score

    def get_upcoming_events(self):
        """
        다가오는 산행 목록 조회 (캐싱 제외 - 실시간성 중요)
        """
        today = datetime.now().strftime("%Y-%m-%d")
        sql = f"""
            SELECT e.*, m.name as host_name, m.birth_year, m.area, m.profile_image_url 
            FROM events e 
            LEFT JOIN members m ON e.host = m.user_no 
            WHERE e.date >= '{today}' 
            ORDER BY e.date ASC 
            LIMIT 3
        """
        return self.db.query(sql)

    @st.cache_data(ttl=3600) # Cache for 1 hour
    def get_weather_forecast(_self):
        """
        서울 날씨 예보 조회 (Open-Meteo API)
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo"
            res = requests.get(url, timeout=3).json()
            return res.get('daily')
        except Exception as e:
            print(f"Weather API Error: {e}")
            return None

    @st.cache_data(ttl=600)
    def get_event_analysis(_self):
        """
        최근 산행 분석 (월별 추이, 연간 통계)
        """
        # 1. 월별 추이 (최근 5개월)
        sql_trend = """
            SELECT strftime('%Y-%m', date) as month, count(*) as count 
            FROM events 
            WHERE date >= CAST(date_trunc('month', today() - interval 4 month) AS DATE)
              AND date <= today()
            GROUP BY month 
            ORDER BY month
        """
        
        # 2. 연간 통계 (최근 12개월)
        sql_stats = """
            WITH monthly_data AS (
                SELECT strftime('%Y-%m', date) as month, count(*) as cnt 
                FROM events 
                WHERE date >= CAST(date_trunc('month', today() - interval 11 month) AS DATE)
                  AND date <= today()
                GROUP BY month
            )
            SELECT 
                (SELECT AVG(cnt) FROM monthly_data) as avg_cnt,
                (SELECT month FROM monthly_data ORDER BY cnt DESC, month DESC LIMIT 1) as peak_month,
                (SELECT cnt FROM monthly_data ORDER BY cnt DESC, month DESC LIMIT 1) as peak_cnt,
                (SELECT month FROM monthly_data ORDER BY cnt ASC, month ASC LIMIT 1) as low_month,
                (SELECT cnt FROM monthly_data ORDER BY cnt ASC, month ASC LIMIT 1) as low_cnt,
                (SELECT count(*) FROM events WHERE strftime('%Y-%m', date) = strftime('%Y-%m', today()) AND date <= today()) as current_cnt
        """
        return _self.db.query(sql_trend), _self.db.query(sql_stats)

    @st.cache_data(ttl=600)
    def get_demographics(_self):
        """
        회원 구성 통계 (연도별/성별 분포)
        """
        return _self.db.query("SELECT birth_year, gender FROM members WHERE role<>'exmember'")

    @st.cache_data(ttl=600)
    def get_hall_of_fame(_self, cur_month_str):
        """
        이달의 명예의 전당 (공지왕, 참석왕, 인기산행)
        """
        # 공지왕
        df_host = _self.db.query(f"""
            SELECT m.name, m.profile_image_url, COUNT(*) as cnt 
            FROM events e 
            JOIN members m ON e.host = m.user_no 
            WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' 
            GROUP BY m.name, m.profile_image_url 
            ORDER BY cnt DESC 
            LIMIT 3
        """)
        
        # 참석왕
        df_attend = _self.db.query(f"""
            SELECT m.name, m.profile_image_url, SUM(e.score) as score
            FROM attendees a
            JOIN events e ON a.event_id = e.event_id
            JOIN members m ON a.user_no = m.user_no
            WHERE strftime('%Y-%m', e.date) = '{cur_month_str}'
            GROUP BY m.name, m.profile_image_url
            ORDER BY score DESC
            LIMIT 3
        """)

        # 인기산행
        df_pop = _self.db.query(f"SELECT e.title, COUNT(a.user_no) as cnt FROM events e JOIN attendees a ON e.event_id = a.event_id WHERE strftime('%Y-%m', e.date) = '{cur_month_str}' GROUP BY e.title ORDER BY cnt DESC LIMIT 3")

        return df_host, df_attend, df_pop

    @st.cache_data(ttl=600)
    def get_monthly_attend_by_birth(_self, cur_month_str):
        """
        이달의 생년별 참가 현황
        """
        # 1. 모든 활성 회원의 생년
        df_all_births = _self.db.query("SELECT DISTINCT birth_year FROM members WHERE role<>'exmember' ORDER BY birth_year")
        
        # 2. 이달의 참가 데이터
        df_curr_attend_raw = _self.db.query(f"""
            SELECT m.birth_year, COUNT(DISTINCT a.user_no) as cnt
            FROM attendees a
            JOIN events e ON a.event_id = e.event_id
            JOIN members m ON a.user_no = m.user_no
            WHERE strftime('%Y-%m', e.date) = '{cur_month_str}'
            GROUP BY m.birth_year
        """)
        
        if not df_all_births.empty:
            df_final = pd.merge(df_all_births, df_curr_attend_raw, on='birth_year', how='left').fillna(0)
            df_final['생년'] = df_final['birth_year'].astype(int).astype(str).str[-2:] + "년"
            return df_final
        return pd.DataFrame()

    @st.cache_data(ttl=3600) # 지도 데이터는 잘 안변함
    def get_map_summary(_self, df_summary):
        # NOTE: df_summary는 이미 홈에서 넘겨주는 큰 뷰 데이터.
        # 여기서는 지역별 카운트만 재집계하거나 UI에서 처리하도록 둘 수 있음.
        # 리팩토링 편의상 UI logic을 간소화하기 위해 여기서 집계.
        df_map = df_summary['지역'].value_counts().reset_index()
        df_map.columns = ['area', 'count']
        return df_map
