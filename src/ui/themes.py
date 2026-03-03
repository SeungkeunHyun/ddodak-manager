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

import random

def get_random_korean_mountain():
    mountains = [
        "https://upload.wikimedia.org/wikipedia/commons/e/e0/Ulsanbawi_Seoraksan_Korea.JPG",
        "https://upload.wikimedia.org/wikipedia/commons/5/52/Hallasan_Baengnokdam.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/1/13/Bukhansan_National_Park.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/0/07/Jirisan_Cheonwangbong_Peak.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/9/91/Naejangsan_National_Park.jpg"
    ]
    return random.choice(mountains)

# 1. Nature & Green — v5.0 Enhanced Palette
NatureTheme = Theme(
    name="Nature",
    colors=ThemeColors(
        primary="#2ecc71",          # Vivid Emerald Green
        primary_gradient="linear-gradient(135deg, #27ae60 0%, #2ecc71 60%, #1abc9c 100%)",
        secondary="#1abc9c",        # Turquoise
        accent="#f39c12",           # Warm Amber
        background="#141c18",       # Deep Forest Dark
        card_bg="rgba(30, 45, 38, 0.75)",  # Richer green-dark glass
        text_primary="#eaf7f0",     # Soft white-green
        text_secondary="#8fb8a0",   # Muted sage
        border="rgba(46, 204, 113, 0.15)",  # Subtle green border
        chart_colors=["#2ecc71", "#1abc9c", "#3498db", "#9b59b6", "#f39c12", "#e74c3c"]
    ),
    font_header="Noto Sans KR",
    font_body="Noto Sans KR",
    bg_image_url="RANDOM_KOREAN_MOUNTAIN"
)

# 2. Cyberpunk/Dark
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
        chart_colors=["#06b6d4", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#3b82f6"]
    ),
    font_header="Orbitron",
    font_body="Outfit"
)

class ThemeManager:
    # Active Theme Selection
    current: Theme = NatureTheme
