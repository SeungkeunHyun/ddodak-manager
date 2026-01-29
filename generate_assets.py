import base64
import os
import glob

output_path = "src/ui/assets.py"
bg_files = glob.glob("bg_*.png")
bg_list = []

print(f"Found {len(bg_files)} images: {bg_files}")

try:
    for img_path in bg_files:
        with open(img_path, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode("utf-8")
            bg_list.append(b64_str)
    
    # Write python list structure
    content = f"# Generated Assets\nBG_IMAGES = {bg_list}\n"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"SUCCESS: Generated {output_path} with {len(bg_list)} images.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
