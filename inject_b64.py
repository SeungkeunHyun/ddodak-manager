import os

# Modified to read local background.png (AI Generated)
b64_file = "background.png"
target_file = "src/ui/styles.py"

if not os.path.exists(b64_file):
    print("Background file not found!")
    exit(1)

with open(b64_file, "rb") as f:
    import base64
    # Read binary and encode to base64 string
    b64_str = base64.b64encode(f.read()).decode("utf-8")

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

# Marker 
target_marker = "/* Placeholder to be replaced by injection script */"

# New CSS content
new_css = f"""/* 8. Background Overlay & AI Image Fix (Local Base64) */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
                background: transparent !important;
            }}
            
            [data-testid="stAppViewContainer"] {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('data:image/png;base64,{b64_str}') !important;
                background-size: cover !important;
                background-position: center center !important;
                background-attachment: fixed !important;
                background-repeat: no-repeat !important;
            }}
"""

if target_marker in content:
    new_content = content.replace(target_marker, new_css)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("SUCCESS: Injected AI Background.")
else:
    print("FAIL: Placeholder not found.")
