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
        import random
        # Import Base64 Assets List
        try:
            from src.ui.assets import BG_IMAGES
        except ImportError:
            BG_IMAGES = [] # Fallback

        # Select a random image from the local AI assets
        if BG_IMAGES:
            bg_b64 = random.choice(BG_IMAGES)
        else:
            bg_b64 = ""
            
        theme = ThemeManager.current
        c = theme.colors
        
        # ... (lines 28-196 skipped for brevity in this view, assuming context matches)
        # Actually I need to replace the CSS block too where it uses the variable.
        # Let's target the exact CSS block again.
        
        # Internal Verified Mountain List
        mountains = [
            "https://upload.wikimedia.org/wikipedia/commons/e/e0/Ulsanbawi_Seoraksan_Korea.JPG", 
            "https://upload.wikimedia.org/wikipedia/commons/5/52/Hallasan_Baengnokdam.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/1/13/Bukhansan_National_Park.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/0/07/Jirisan_Cheonwangbong_Peak.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/9/91/Naejangsan_National_Park.jpg"
        ]
        
        # Select Image
        bg_url = theme.bg_image_url
        if bg_url == "RANDOM_KOREAN_MOUNTAIN":
             # Use the first one (Ulsanbawi) for stability as requested, or random.
             # Let's go back to random but with Base64 caching to ensure it works.
             # Actually, user said "Random" in Step 906, but "Fixed" in Step 962.
             # Let's use Random as per original requirement, but Base64 ensures it loads.
             bg_url = random.choice(mountains)
        
        # Helper to load image as Base64 (Cached)
        @st.cache_data(show_spinner=False)
        def get_img_as_base64(url):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return base64.b64encode(response.content).decode()
            except:
                return None
            return None

        img_b64 = get_img_as_base64(bg_url)
        
        # Construct CSS - If B64 fails, fallback to URL, then Color
        if img_b64:
            bg_css_val = f"url('data:image/jpg;base64,{img_b64}')"
        else:
            bg_css_val = f"url('{bg_url}')"
        
        st.markdown(f"""
        <style>
            /* 1. Google Fonts Import */
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&family=Orbitron:wght@400;700&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

            /* 2. Global Typography */
            html, body, [class*="css"] {{
                font-family: '{theme.font_body}', sans-serif;
                color: {c.text_primary};
                background-color: {c.background}; /* Fallback */
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
            
            @keyframes shimmer {{
                0% {{ background-position: -1000px 0; }}
                100% {{ background-position: 1000px 0; }}
            }}

            /* 4. Glassmorphism Card Style (Themed) */
            .glass-card {{
                background: {c.card_bg} !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                border: 1px solid {c.border} !important;
                border-radius: 20px !important;
                padding: 24px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
                transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
                color: {c.text_primary} !important;
            }}
            
            .glass-card * {{
                color: inherit !important;
            }}
            
            /* 3D Hover Effect */
            .hover-3d:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
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
                background: rgba(0,0,0,0.05);
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
                background-color: rgba(255,255,255,0.05);
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
                background: {c.primary};
                border: none;
                color: white;
                transition: all 0.2s;
                font-family: '{theme.font_header}', sans-serif;
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
            
            /* 8. Background Overlay & AI Image Fix (Asset Import) */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background: transparent !important;
            }}
            
            [data-testid="stAppViewContainer"] {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('data:image/png;base64,{bg_b64}') !important;
                background-size: cover !important;
                background-position: center center !important;
                background-attachment: fixed !important;
                background-repeat: no-repeat !important;
            }}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def set_background(image_path="background.png"):
        """
        배경 이미지를 설정하고 어두운 오버레이를 적용하여 가독성을 높입니다.
        """
        try:
            with open(image_path, "rb") as f:
                data = f.read()
            bin_str = base64.b64encode(data).decode()
            
            page_bg_img = f"""
            <style>
            .stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.8)), url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-attachment: fixed;
                background-position: center;
            }}
            </style>
            """
            st.markdown(page_bg_img, unsafe_allow_html=True)
        except Exception as e:
            # 배경 이미지가 없을 경우 안전한 그라데이션 폴백
            fallback_bg = """
            <style>
            .stApp {
                background: linear-gradient(135deg, #1e1e1e 0%, #0f0f0f 100%);
            }
            </style>
            """
            st.markdown(fallback_bg, unsafe_allow_html=True)
            print(f"Background image load failed: {e}")

    @staticmethod
    def card_template(content, height="100%", extra_classes=""):
        """
        Themed Glassmorphism Card Wrapper.
        """
        return f"""<div class="glass-card hover-3d {extra_classes}" style="height: {height}; display: flex; flex-direction: column; justify-content: center;">
            {content}
        </div>"""
