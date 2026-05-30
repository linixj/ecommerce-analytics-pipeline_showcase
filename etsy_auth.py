import hashlib
import secrets
import base64
import urllib.parse
import requests
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ETSY_API_KEY")
SHARED_SECRET = os.getenv("ETSY_SHARED_SECRET")
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "transactions_r listings_r profile_r"

# 生成 PKCE code verifier 和 challenge
code_verifier = secrets.token_urlsafe(64)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()

state = secrets.token_urlsafe(16)

auth_url = (
    f"https://www.etsy.com/oauth/connect"
    f"?response_type=code"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope={urllib.parse.quote(SCOPES)}"
    f"&client_id={API_KEY}"
    f"&state={state}"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
)

print("\n请在浏览器里打开这个 URL 完成授权：")
print(f"\n{auth_url}\n")

# 本地服务器等待 callback
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authorization successful! You can close this window.")
        print("\n收到授权码，正在获取 access token...")

    def log_message(self, format, *args):
        pass  # 静默日志

server = HTTPServer(("localhost", 3000), CallbackHandler)
print("等待 Etsy 授权回调...")
server.handle_request()

# 用授权码换 access token
if auth_code:
    response = requests.post(
        "https://api.etsy.com/v3/public/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": API_KEY,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
            "code_verifier": code_verifier,
        }
    )

    if response.ok:
        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        print(f"\n成功！请把以下内容加到 .env 文件里：")
        print(f"\nETSY_ACCESS_TOKEN={access_token}")
        print(f"ETSY_REFRESH_TOKEN={refresh_token}")

        # 自动写入 .env
        with open(".env", "a") as f:
            f.write(f"\nETSY_ACCESS_TOKEN={access_token}")
            f.write(f"\nETSY_REFRESH_TOKEN={refresh_token}")
        print("\n已自动写入 .env 文件！")
    else:
        print(f"获取 token 失败: {response.status_code}")
        print(response.text)
else:
    print("没有收到授权码")