import os
import sys

input_file = "bg.b64"
output_file = "src/ui/assets.py"

try:
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        sys.exit(1)

    # Certutil output ensures basic ascii usually, but let's be safe
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # Strip headers/footers and newlines
    b64_content = "".join([line.strip() for line in lines if "-----" not in line])
    
    if not b64_content:
        print("Error: Extracted content is empty.")
        sys.exit(1)
        
    # Write to assets.py
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f'BG_B64 = "{b64_content}"\n')
        
    print(f"SUCCESS: Wrote {len(b64_content)} chars to {output_file}")

except Exception as e:
    print(f"Exception: {e}")
    sys.exit(1)
