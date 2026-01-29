from dataclasses import dataclass
from typing import List

@dataclass
class ThemeColors:
    primary: str
    primary_gradient: str
    secondary: str
    accent: str
    background: str
    card_bg: str
    text_primary: str
    text_secondary: str
    border: str
    chart_colors: List[str]

@dataclass
class Theme:
    name: str
    colors: ThemeColors
    font_header: str
    font_body: str
    bg_image_url: str = ""

# --- DEFINED THEMES ---

# 1. Nature & Green (Comfortable High Contrast)
import random

def get_random_korean_mountain():
    # Korean Mountains: Seoraksan, Hallasan, Jirisan, Bukhansan (Wikimedia Commons High-Res)
    mountains = [
        "https://upload.wikimedia.org/wikipedia/commons/e/e0/Ulsanbawi_Seoraksan_Korea.JPG", # Seoraksan
        "https://upload.wikimedia.org/wikipedia/commons/5/52/Hallasan_Baengnokdam.jpg",    # Hallasan
        "https://upload.wikimedia.org/wikipedia/commons/1/13/Bukhansan_National_Park.jpg", # Bukhansan
        "https://upload.wikimedia.org/wikipedia/commons/0/07/Jirisan_Cheonwangbong_Peak.jpg", # Jirisan
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Naejangsan_National_Park.jpg" # Naejangsan
    ]
    return random.choice(mountains)

NatureTheme = Theme(
    name="Nature",
    colors=ThemeColors(
        primary="#059669",       # Emerald 600 (Darker, less glaring)
        primary_gradient="linear-gradient(135deg, #047857 0%, #059669 100%)",
        secondary="#6ee7b7",     # Emerald 300 (Softer secondary)
        accent="#d97706",        # Amber 600 (Darker Warm Accent)
        background="#064e3b",    # Emerald 900
        card_bg="rgba(6, 78, 59, 0.5)", 
        text_primary="#ecfdf5",  # Emerald 50
        text_secondary="#a7f3d0",# Emerald 200
        border="rgba(16, 185, 129, 0.3)", 
        chart_colors=["#10b981", "#34d399", "#6ee7b7", "#059669", "#047857"]
    ),
    font_header="Noto Sans KR",
    font_body="Noto Sans KR",
    bg_image_url="RANDOM_KOREAN_MOUNTAIN"
)

# 2. Cyberpunk/Dark (Previous v4.7)
CyberTheme = Theme(
    name="Cyber",
    colors=ThemeColors(
        primary="#a5f3fc",
        primary_gradient="linear-gradient(to right, #fff, #a5f3fc)",
        secondary="#86efac",
        accent="#fdf023",
        background="#0f172a",
        card_bg="rgba(10, 10, 15, 0.6)",
        text_primary="#ffffff",
        text_secondary="#cbd5e1",
        border="rgba(255, 255, 255, 0.1)",
        chart_colors=["#06b6d4", "#8b5cf6", "#ec4899"]
    ),
    font_header="Orbitron",
    font_body="Outfit"
)

class ThemeManager:
    # Active Theme Selection
    current: Theme = NatureTheme
