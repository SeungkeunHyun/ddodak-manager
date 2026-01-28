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
        애플리케이션 전반의 CSS 스타일을 정의합니다.
        폰트, 애니메이션, 카드 스타일 등을 포함합니다.
        """
        st.markdown("""
        <style>
            /* 1. Google Fonts Import (Noto Sans KR, Poppins) */
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Poppins:wght@400;600;700&display=swap');

            /* 2. Global Typography */
            html, body, [class*="css"] {
                font-family: 'Noto Sans KR', 'Poppins', sans-serif;
            }
            h1, h2, h3 {
                font-family: 'Poppins', 'Noto Sans KR', sans-serif;
                font-weight: 700;
                letter-spacing: -0.5px;
            }
            
            /* 3. Animations */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes pulseGlow {
                0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
                100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
            }

            /* 4. Glassmorphism Card Style */
            .glass-card {
                background: rgba(0, 0, 0, 0.6) !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 16px !important;
                padding: 24px !important;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                animation: fadeIn 0.6s ease-out;
            }
            
            .glass-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
            }

            /* 5. Streamlit Component Overrides */
            /* 탭 스타일 */
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px 20px;
                color: #ccc;
            }
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
            }
            
            /* 버튼 스타일 */
            .stButton > button {
                border-radius: 8px;
                transition: all 0.2s;
            }
            .stButton > button:hover {
                transform: scale(1.02);
            }

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
    def card_template(content, height="100%"):
        """
        Glassmorphism 스타일의 카드 HTML 래퍼를 반환합니다.
        """
        return f"""<div class="glass-card" style="height: {height}; display: flex; flex-direction: column; justify-content: center;">
            {content}
        </div>"""
