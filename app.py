
import streamlit as st
import streamlit_authenticator as stauth
from src.config import Config
from src.services import DBService, AIService, BandAuthService, AnalysisService
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

    with st.sidebar:
        st.title("⛰️ 또닥또닥 산악회")
        st.caption("🚀 App Version: v3.2.5 (Report Full Restore)")

    # 2. Authentication
    
    # [Visuals] Apply Global Styles & Background (Before Login)
    Styles.apply_custom_css()
    
    # [Naver Band Auth Integration]
    band_auth = BandAuthService(
        client_id=Config.BAND_CLIENT_ID,
        client_secret=Config.BAND_CLIENT_SECRET,
        redirect_uri=Config.BAND_REDIRECT_URI
    )
    
    # Check for OAuth Callback
    if "code" in st.query_params:
        code = st.query_params["code"]
        token = band_auth.exchange_code_for_token(code)
        if token:
            user_bands = band_auth.get_user_bands(token)
            # Find Target Band (ID: 85157163)
            target_band = next((b for b in user_bands if str(b.get("band_sn")) == Config.TARGET_BAND_ID), None)
            
            if target_band:
                band_key = target_band.get("band_key")
                if band_key and band_auth.get_permissions(token, band_key):
                    st.session_state["authentication_status"] = True
                    st.session_state["name"] = target_band.get("name", "Band Member")
                    st.session_state["username"] = "band_user"
                    st.query_params.clear()
                    st.rerun()
            else:
                 st.error(f"가입된 밴드 목록에서 목표 밴드(ID: {Config.TARGET_BAND_ID})를 찾을 수 없습니다.")

    auth = stauth.Authenticate(Config.CREDENTIALS, "ddodak_cookie", "ddodak_key")
    
    # Render Login UI (Hybrid - Centered)
    if not st.session_state.get("authentication_status"):
        # Use columns to center the login box
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            st.markdown("### 관리자 로그인")
            auth.login(location='main')
            
            st.markdown("---")
            st.markdown("<div style='text-align: center; color: #888; font-size: 0.9em; margin-bottom: 10px;'>또는</div>", unsafe_allow_html=True)
            
            auth_url = band_auth.get_authorization_url()
            # Full width button for better mobile/desktop visuals
            st.link_button("🟩 네이버 밴드로 로그인 (리더/공동리더 권한)", auth_url, use_container_width=True)
            
    if st.session_state["authentication_status"]:
        # 3. Initialize Services
        db_service = DBService()
        ai_service = AIService()
        analysis_service = AnalysisService(db_service)

        # 4. Apply Global Styles
        # Styles.apply_custom_css() # Moved to global scope

        # 5. Render Layout & Navigation
        choice = Layout.render_sidebar(ai_service.model_name)

        # 6. Route to Page
        if choice == "🏠 홈":
            HomePage(db_service, ai_service, analysis_service).render()
        elif choice == "👥 회원 관리":
            MembersPage(db_service).render()
        elif choice == "📅 공지 관리":
            EventsPage(db_service).render()
        elif choice == "🏃 참가 체크":
            AttendancePage(db_service).render()
        elif choice == "📊 보고서 생성":
            ReportPage(db_service).render()
        # Logout Button in Sidebar
        auth.logout("로그아웃", "sidebar")
        
    elif st.session_state["authentication_status"] is False:
        st.error("비밀번호가 틀렸습니다.")
    elif st.session_state["authentication_status"] is None:
        st.warning("로그인이 필요합니다.")

if __name__ == "__main__":
    main()