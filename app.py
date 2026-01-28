
import streamlit as st
import streamlit_authenticator as stauth
from src.config import Config
from src.services.db_service import DBService
from src.services.ai_service import AIService
from src.ui.styles import Styles
from src.ui.layout import Layout
from src.ui.pages.home import HomePage
from src.ui.pages.members import MembersPage
from src.ui.pages.events import EventsPage
from src.ui.pages.attend import AttendancePage
from src.ui.pages.report import ReportPage

# =========================================================
# Main Entry Point (v3.0 Modular Architecture)
# =========================================================

def main():
    # 1. Page Config (Must be first)
    st.set_page_config(
        page_title="또닥또닥 산악회",
        page_icon="⛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Authentication
    auth = stauth.Authenticate(Config.CREDENTIALS, "ddodak_cookie", "ddodak_key")
    auth.login(location='main')

    if st.session_state["authentication_status"]:
        # 3. Initialize Services
        db = DBService()
        ai = AIService()

        # 4. Apply Global Styles
        Styles.apply_custom_css()

        # 5. Render Layout & Navigation
        choice = Layout.render_sidebar(ai.model_name)

        # 6. Route to Page
        if choice == "🏠 홈":
            HomePage(db, ai).render()
        elif choice == "👥 회원 관리":
            MembersPage(db).render()
        elif choice == "📅 산행 일정":
            EventsPage(db).render()
        elif choice == "🏃 참가 체크":
            AttendancePage(db).render()
        elif choice == "📊 보고서 생성":
            ReportPage(db).render()
        
        # Logout Button in Sidebar
        auth.logout("로그아웃", "sidebar")
        
    elif st.session_state["authentication_status"] is False:
        st.error("비밀번호가 틀렸습니다.")
    elif st.session_state["authentication_status"] is None:
        st.warning("로그인이 필요합니다.")

if __name__ == "__main__":
    main()