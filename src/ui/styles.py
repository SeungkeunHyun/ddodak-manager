import streamlit as st
import base64

# =========================================================
# 3. UI Layer - Styles & Visuals  (v5.0 Enhanced)
# =========================================================

class Styles:
    @staticmethod
    def apply_custom_css():
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
                line-height: 1.7;
                font-size: 16px;
            }}
            p, span, li, .markdown-text-container {{
                font-family: '{theme.font_body}', sans-serif;
                color: {c.text_primary};
                background-color: transparent !important;
                line-height: 1.7;
                font-size: 16px;
            }}
            h1, h2, h3 {{
                font-family: '{theme.font_header}', '{theme.font_body}', sans-serif !important;
                font-weight: 700;
                letter-spacing: 0.8px;
                color: {c.primary} !important;
                text-transform: uppercase;
                background: none;
                -webkit-text-fill-color: initial;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }}

            /* 3. Animations */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(30px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes float {{
                0%   {{ transform: translateY(0px); }}
                50%  {{ transform: translateY(-6px); }}
                100% {{ transform: translateY(0px); }}
            }}
            @keyframes pulse-glow {{
                0%   {{ box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.4); }}
                70%  {{ box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }}
            }}
            @keyframes shimmer {{
                0%   {{ background-position: -1000px 0; }}
                100% {{ background-position: 1000px 0; }}
            }}
            @keyframes gradient-shift {{
                0%   {{ background-position: 0% 50%; }}
                50%  {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
            @keyframes badge-pulse {{
                0%   {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }}
                70%  {{ transform: scale(1.05); box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }}
                100% {{ transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
            }}

            /* Animation Classes */
            .animate-fadein     {{ animation: fadeInUp 0.6s ease forwards; }}
            .animate-float      {{ animation: float 3s ease-in-out infinite; }}
            .animate-pulse-glow {{ animation: pulse-glow 2s infinite; }}
            .animate-badge      {{ animation: badge-pulse 1.5s infinite; }}

            /* Custom Premium Scrollbar */
            ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
            ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.05); border-radius: 4px; }}
            ::-webkit-scrollbar-thumb {{ background: {c.primary}; border-radius: 4px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: {c.secondary}; }}

            /* 4. Glassmorphism Card Style */
            .glass-card {{
                background: {c.card_bg} !important;
                backdrop-filter: blur(20px) !important;
                -webkit-backdrop-filter: blur(20px) !important;
                border: 1px solid {c.border} !important;
                border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-left: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 24px !important;
                padding: 28px !important;
                min-height: 130px !important;
                box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
                transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
                color: {c.text_primary} !important;
                animation: fadeInUp 0.6s ease forwards;
            }}
            .glass-card * {{ color: inherit !important; }}

            /* Chart Section Title */
            .chart-title {{
                font-size: 14px !important;
                font-weight: 700 !important;
                letter-spacing: 2px !important;
                text-transform: uppercase !important;
                color: {c.text_secondary} !important;
                margin: 0 0 12px 0 !important;
                opacity: 0.95 !important;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            /* Insight Context Card */
            .insight-card {{
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.12);
                border-left: 4px solid {c.accent};
                border-radius: 16px;
                padding: 24px 28px;
                line-height: 1.8;
            }}
            .insight-card .highlight {{
                color: {c.secondary};
                font-weight: 700;
            }}
            .insight-card .title {{
                font-size: 18px;
                font-weight: 700;
                color: {c.accent};
                margin-bottom: 12px;
                display: block;
            }}

            /* Stat Badge */
            .stat-badge {{
                display: inline-block;
                padding: 4px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 700;
                letter-spacing: 0.5px;
                background: rgba(255,255,255,0.08); /* theme agnostic if possible */
                color: {c.primary};
                border: 1px solid rgba(255,255,255,0.15);
            }}

            /* KPI Value Style */
            .kpi-value {{
                font-size: 46px !important;
                font-weight: 800 !important;
                color: #ffffff !important;
                line-height: 1.1;
                letter-spacing: -1px;
            }}
            .kpi-label {{
                font-size: 14px !important;
                color: {c.text_secondary} !important;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1.2px;
            }}
            .kpi-trend-up   {{ color: #4ade80 !important; font-size: 14px; font-weight: 700; }}
            .kpi-trend-down {{ color: #f87171 !important; font-size: 14px; font-weight: 700; }}

            /* Section Divider */
            .section-divider {{
                height: 2px;
                border: none;
                background: linear-gradient(90deg, transparent, {c.primary}, {c.secondary}, transparent);
                background-size: 200% 200%;
                animation: gradient-shift 3s ease infinite;
                margin: 24px 0;
                border-radius: 2px;
            }}

            /* 3D Hover Effect */
            .hover-3d:hover {{
                transform: translateY(-6px) scale(1.01);
                box-shadow: 0 20px 48px rgba(0, 0, 0, 0.35) !important;
                border-color: {c.primary} !important;
            }}

            /* Neon/Accent Borders */
            .neon-border-cyan    {{ border-bottom: 3px solid {c.primary} !important; }}
            .neon-border-magenta {{ border-bottom: 3px solid {c.accent} !important; }}
            .neon-border-green   {{ border-bottom: 3px solid {c.secondary} !important; }}

            /* Podium Styles */
            .podium-container {{
                display: flex;
                align-items: flex-end;
                justify-content: center;
                gap: 12px;
                margin: 20px 0;
            }}
            .podium-block {{
                display: flex;
                flex-direction: column;
                align-items: center;
                border-radius: 12px 12px 0 0;
                padding: 14px 18px 10px;
                min-width: 100px;
                transition: all 0.3s ease;
            }}
            .podium-block:hover {{ transform: translateY(-4px); }}

            /* Badge Pulse for D-Day */
            .badge-dday {{ animation: badge-pulse 1.5s infinite; display: inline-block; }}

            /* 5. Streamlit Component Overrides */
            
            /* Tighter Spacing & Block Margins */
            .element-container, .stMarkdown {{
                margin-bottom: 0px;
            }}
            .block-container {{
                padding-top: 2rem !important;
                padding-bottom: 2rem !important;
            }}
            
            /* Form Inputs / Selectboxes Premiumization */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > div {{
                border-radius: 12px;
                border: 1px solid {c.border};
                background: rgba(255, 255, 255, 0.03);
                color: {c.text_primary};
                padding: 10px 16px;
                transition: all 0.3s ease;
            }}
            .stTextInput > div > div > input:focus,
            .stSelectbox > div > div > div:focus-within {{
                box-shadow: 0 0 0 2px {c.primary}40 !important;
                border-color: {c.primary} !important;
                background: rgba(255, 255, 255, 0.08);
            }}

            .stTabs [data-baseweb="tab-list"] {{
                gap: 12px;
                background: rgba(255, 255, 255, 0.05) !important;
                padding: 10px;
                border-radius: 16px;
                border-bottom: none !important;
            }}
            .stTabs [data-baseweb="tab"] {{
                background-color: transparent !important;
                border-radius: 10px !important;
                padding: 10px 24px !important;
                color: {c.text_secondary} !important;
                font-weight: 600 !important;
                border: none !important;
                transition: all 0.3s ease !important;
            }}
            .stTabs [data-baseweb="tab-highlight"] {{
                display: none !important;
            }}
            .stTabs [data-baseweb="tab"]:hover {{
                color: {c.primary} !important;
                background-color: rgba(255, 255, 255, 0.08) !important;
            }}
            .stTabs [data-baseweb="tab"][aria-selected="true"] {{
                background: {c.primary_gradient} !important;
                color: white !important;
                font-weight: 700 !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
            }}
            .stTabs [data-baseweb="tab"][aria-selected="true"] p {{
                color: white !important;
            }}

            /* Button */
            .stButton > button {{
                border-radius: 14px;
                background: linear-gradient(135deg, {c.primary} 0%, {c.secondary} 100%);
                border: none;
                color: white !important;
                transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
                font-family: '{theme.font_header}', sans-serif;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
                padding: 0.6rem 1.2rem;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            .stButton > button p, .stButton > button span, .stButton > button div {{
                color: white !important;
                background-color: transparent !important;
            }}
            .stButton > button:hover {{
                transform: translateY(-3px);
                filter: brightness(1.15);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.35);
                color: white !important;
            }}

            /* Toggle */
            .stToggle [data-testid="stToggleText"] {{ color: {c.text_primary} !important; }}

            /* DataFrame / Data Editor Enhancements */
            div[data-testid="stDataFrame"] div[data-testid="stDataFrame"] {{
                font-size: 15px;
            }}
            div[data-testid="stDataFrame"] [data-testid="StyledTableCell"] {{
                padding: 14px 18px !important;
                vertical-align: middle;
            }}

            /* Data Editor Dropdown (selectbox in st.data_editor) Fix */
            div[data-baseweb="popover"] > div,
            div[role="listbox"],
            ul[role="listbox"] {{
                background-color: {c.card_bg} !important;
                color: {c.text_primary} !important;
                border: 1px solid {c.border} !important;
            }}
            li[role="option"] {{
                color: {c.text_primary} !important;
            }}
            li[role="option"]:hover, li[role="option"][aria-selected="true"] {{
                background-color: rgba(255, 255, 255, 0.1) !important;
                color: {c.primary} !important;
            }}

            /* Typography Helpers */
            .readable-subtext {{
                font-size: 15px !important;
                color: {c.text_secondary} !important;
                font-weight: 500 !important;
                line-height: 1.6 !important;
            }}
            .readable-caption {{
                font-size: 14px !important;
                color: {c.text_secondary} !important;
                opacity: 0.85 !important;
            }}

            /* Print Optimization */
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

            /* Application Background */
            .stApp {{
                background-color: {c.background} !important;
                background-image: none !important;
            }}
            [data-testid="stAppViewContainer"] {{
                background-color: {c.background} !important;
                background-image: none !important;
            }}
            [data-testid="stHeader"] {{ background: transparent !important; }}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def card_template(content, height="100%", extra_classes=""):
        return f'<div class="glass-card hover-3d {extra_classes}" style="height: {height}; display: flex; flex-direction: column; justify-content: center;">{content}</div>'

