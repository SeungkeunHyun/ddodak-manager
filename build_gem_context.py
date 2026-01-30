
import os

# Configuration
PROJECT_ROOT = r"d:\myCoding\python\band\ddodak\docker"
OUTPUT_FILE = r"C:\Users\SeungkeunHyun\.gemini\antigravity\brain\c3d6301f-cf58-4b6f-aafb-6f43c9f84411\gem_context.md"

# Header is already written by previous step, but let's overwrite to be safe and clean.
HEADER = """# Project Context: Ddodak Mountain Club (또닥또닥 산악회)
# Version: v4.27 (Stable)
# Generated on: 2026-01-29

## 1. Project Overview
This is a Streamlit-based web application for managing a mountain climbing club. 
Stack: Streamlit, Docker, SQLite, Naver Band API.

## 2. Directory Structure & File Contents
"""

def should_include(filename):
    if filename.endswith(".py") or filename.endswith("Dockerfile") or filename.endswith("requirements.txt"):
        return True
    return False

def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(HEADER)
        
        # Traverse directory
        for root, dirs, files in os.walk(PROJECT_ROOT):
            for file in files:
                if should_include(file):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, PROJECT_ROOT)
                    
                    # Skip venv or .git if any (though unlikely in docker dir root)
                    if ".git" in rel_path or "__pycache__" in rel_path:
                        continue

                    try:
                        with open(full_path, "r", encoding="utf-8") as infile:
                            content = infile.read()
                            
                        outfile.write(f"\n\n# ==========================================\n")
                        outfile.write(f"# File: {rel_path}\n")
                        outfile.write(f"# ==========================================\n")
                        outfile.write(f"```python\n{content}\n```\n")
                        print(f"Included: {rel_path}")
                    except Exception as e:
                        print(f"Skipped {rel_path}: {e}")

    print(f"Successfully created context file at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
