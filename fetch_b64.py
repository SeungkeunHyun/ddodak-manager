import requests
import base64

# Use 1280px thumbnail for better performance/size
url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Ulsanbawi_Seoraksan_Korea.JPG/1280px-Ulsanbawi_Seoraksan_Korea.JPG"

try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        b64 = base64.b64encode(response.content).decode()
        with open("bg_b64.txt", "w") as f:
            f.write(b64)
        print("SUCCESS")
    else:
        print(f"FAIL: {response.status_code}")
except Exception as e:
    print(f"ERROR: {e}")
