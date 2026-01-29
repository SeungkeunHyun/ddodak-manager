import os
import duckdb
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# =========================================================
# 1. App Configuration (설정 관리)
# 애플리케이션의 전반적인 설정을 관리하는 클래스입니다.
# 환경 변수, DB 경로, 상수 등을 정의합니다.
# =========================================================
class Config:
    load_dotenv()
    # AI API 키 (Google Gemini)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # 한국 표준시(KST) 설정
    KST = timezone(timedelta(hours=9))
    
    # 데이터베이스 파일 경로
    # src/ 폴더 밖의 root 경로에 있는 DB를 참조해야 하므로 ..를 사용하거나 절대경로 사용
    # Docker 환경에서는 /app/ddodak.duckdb
    DB_NAME = 'ddodak.duckdb' 
    
    # 회칙 링크 (보고서 생성 시 사용)
    RULES_URL = "https://www.band.us/band/85157163/post/4765"
    
    # [Naver Band Authenticatoin]
    # BAND API Console: https://developers.band.us/
    BAND_CLIENT_ID = os.getenv("BAND_CLIENT_ID", "") 
    BAND_CLIENT_SECRET = os.getenv("BAND_CLIENT_SECRET", "")
    # Default Redirect URI for local docker
    BAND_REDIRECT_URI = os.getenv("BAND_REDIRECT_URI", "http://localhost:8501")
    # The Band ID (Numeric) used for validation - though API uses Band Key
    TARGET_BAND_ID = "85157163" 
    
    # 관리자 로그인 정보 (Streamlit Authenticator 사용)
    CREDENTIALS = {
        "usernames": {
            "ddodak_admin": {
                "name": "또닥 운영진",
                "password": "$2b$12$26eJr8zlp73HWwLlP7xbAeArmA844B0iRAc39VanX.7ezIZ/abbiq"
            }
        }
    }
