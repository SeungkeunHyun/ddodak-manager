import streamlit as st
import base64

# =========================================================
# 3. UI Layer - Styles & Visuals
# CSS 및 시각적 요소(배경, 폰트, 애니메이션)를 관리합니다.
# =========================================================

class Styles:
    @staticmethod
    def apply_custom_css():
        """
        Applies global CSS styles to the Streamlit app.
        Uses ThemeManager to inject dynamic colors.
        """
        from src.ui.themes import ThemeManager
        
        theme = ThemeManager.current
        c = theme.colors

        st.markdown(f"""
        <style>
            /* 1. Google Fonts Import */
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

            /* 2. Global Typography */
            html, body, [class*="css"] {{
                font-family: '{theme.font_body}', sans-serif;
                color: {c.text_primary};
                background-color: {c.background};
            }}
            h1, h2, h3 {{
                font-family: '{theme.font_header}', '{theme.font_body}', sans-serif !important;
                font-weight: 700;
                letter-spacing: 0.5px;
                color: {c.primary} !important;
                text-transform: uppercase;
                background: none;
                -webkit-text-fill-color: initial;
                text-shadow: none;
            }}
            
            /* 3. Animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            @keyframes pulse-glow {{
                0% {{ box-shadow: 0 0 0 0 rgba(0, 0, 0, 0.2); }}
                70% {{ box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }}
            }}
            
            @keyframes shimmer {{
                0% {{ background-position: -1000px 0; }}
                100% {{ background-position: 1000px 0; }}
            }}

            /* Custom Premium Scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            ::-webkit-scrollbar-track {{
                background: rgba(0, 0, 0, 0.05); 
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb {{
                background: {c.primary}; 
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: {c.secondary}; 
            }}

            /* 4. Glassmorphism Card Style (Themed) */
            .glass-card {{
                background: {c.card_bg} !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1px solid {c.border} !important;
                border-top: 1px solid rgba(255, 255, 255, 0.3) !important;
                border-left: 1px solid rgba(255, 255, 255, 0.3) !important;
                border-radius: 20px !important;
                padding: 24px !important;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07) !important;
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                color: {c.text_primary} !important;
            }}
            
            .glass-card * {{
                color: inherit !important;
            }}
            
            /* 3D Hover Effect */
            .hover-3d:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1) !important;
                border-color: {c.primary} !important;
            }}

            /* Neon/Accent Borders */
            .neon-border-cyan {{ border-bottom: 3px solid {c.primary} !important; }}
            .neon-border-magenta {{ border-bottom: 3px solid {c.accent} !important; }}
            .neon-border-green {{ border-bottom: 3px solid {c.secondary} !important; }}

            /* 5. Streamlit Component Overrides */
            /* 탭 스타일 */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 10px;
                background: transparent;
                padding: 8px;
                border-radius: 12px;
            }}
            .stTabs [data-baseweb="tab"] {{
                background-color: transparent;
                border-radius: 8px;
                padding: 8px 20px;
                color: {c.text_secondary};
                font-weight: 500;
                border: none;
            }}
            .stTabs [data-baseweb="tab"]:hover {{
                color: {c.primary};
                background-color: rgba(0,0,0,0.05);
            }}
            .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background: {c.primary_gradient};
                color: white !important;
                font-weight: bold;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            /* 버튼 스타일 */
            .stButton > button {{
                border-radius: 12px;
                background: linear-gradient(135deg, {c.primary} 0%, {c.secondary} 100%);
                border: none;
                color: white;
                transition: all 0.3s ease;
                font-family: '{theme.font_header}', sans-serif;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .stButton > button:hover {{
                transform: translateY(-2px);
                filter: brightness(1.1);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: white !important;
            }}
            
            /* Toggle Switch Active Color */
            .stToggle [data-testid="stToggleText"] {{
                 color: {c.text_primary} !important;
            }}

            /* 6. Typography Helpers */
            .readable-subtext {{
                font-size: 14px !important;
                color: {c.text_secondary} !important;
                font-weight: 500 !important;
                line-height: 1.5 !important;
            }}
            .readable-caption {{
                font-size: 13px !important;
                color: {c.text_secondary} !important;
                opacity: 0.8 !important;
            }}
            
            /* 7. Print Optimization */
            @media print {{
                .stApp {{ background: white !important; }}
                .glass-card {{
                    background: white !important;
                    border: 1px solid #ddd !important;
                    box-shadow: none !important;
                    color: black !important;
                }}
                 h1, h2, h3 {{ color: black !important; -webkit-text-fill-color: black !important; }}
                 .no-print, header, .stSidebar {{ display: none !important; }}
            }}
            
            /* 8. Application Background - Solid Clean Look */
            .stApp {{
                background-color: {c.background} !important;
                background-image: none !important;
            }}
            
            [data-testid="stAppViewContainer"] {{
                background-color: {c.background} !important;
                background-image: none !important;
            }}
            
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def card_template(content, height="100%", extra_classes=""):
        """
        Themed Glassmorphism Card Wrapper.
        """
        return f"""<div class="glass-card hover-3d {extra_classes}" style="height: {height}; display: flex; flex-direction: column; justify-content: center;">
            {content}
        </div>"""
