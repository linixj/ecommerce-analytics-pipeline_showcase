import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def refresh_access_token():
    """用 refresh token 换新的 access token"""
    refresh_token = os.getenv("ETSY_REFRESH_TOKEN")
    api_key = os.getenv("ETSY_API_KEY")

    if not refresh_token:
        print("没有找到 ETSY_REFRESH_TOKEN，请先运行 etsy_auth.py 授权")
        return None

    response = requests.post(
        "https://api.etsy.com/v3/public/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": api_key,
            "refresh_token": refresh_token,
        }
    )

    if response.ok:
        data = response.json()
        new_access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token")

        # 更新环境变量（当前进程生效）
        os.environ["ETSY_ACCESS_TOKEN"] = new_access_token
        os.environ["ETSY_REFRESH_TOKEN"] = new_refresh_token

        # 更新本地 .env 文件
        _update_env_file("ETSY_ACCESS_TOKEN", new_access_token)
        _update_env_file("ETSY_REFRESH_TOKEN", new_refresh_token)

        print("Etsy token 刷新成功")

        # 如果在 GitHub Actions 里，更新 Secrets
        if os.getenv("GITHUB_ACTIONS"):
            _update_github_secrets(new_access_token, new_refresh_token)

        return new_access_token
    else:
        print(f"Token refresh 失败: {response.status_code}")
        print(response.text)
        return None


def _update_env_file(key, value):
    """更新本地 .env 文件里的某个 key"""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
    )

    if not os.path.exists(env_path):
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)


def _update_github_secrets(new_access_token, new_refresh_token):
    """在 GitHub Actions 里更新 Secrets"""
    import base64
    from nacl import encoding, public

    gh_token = os.getenv("GH_PAT")
    repo = os.getenv("GITHUB_REPOSITORY")

    if not gh_token or not repo:
        print("缺少 GH_PAT 或 GITHUB_REPOSITORY，跳过 GitHub Secrets 更新")
        return

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    # 拿到 repo 的公钥（用来加密 secret）
    pub_key_resp = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers=headers
    )
    pub_key_data = pub_key_resp.json()
    pub_key = pub_key_data["key"]
    key_id = pub_key_data["key_id"]

    def encrypt_secret(public_key_str, secret_value):
        pk = public.PublicKey(public_key_str.encode(), encoding.Base64Encoder())
        box = public.SealedBox(pk)
        encrypted = box.encrypt(secret_value.encode())
        return base64.b64encode(encrypted).decode()

    # 更新两个 secrets
    for secret_name, secret_value in [
        ("ETSY_ACCESS_TOKEN", new_access_token),
        ("ETSY_REFRESH_TOKEN", new_refresh_token),
    ]:
        encrypted = encrypt_secret(pub_key, secret_value)
        resp = requests.put(
            f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
            headers=headers,
            json={"encrypted_value": encrypted, "key_id": key_id}
        )
        if resp.status_code in [201, 204]:
            print(f"GitHub Secret {secret_name} 更新成功")
        else:
            print(f"GitHub Secret {secret_name} 更新失败: {resp.status_code}")


if __name__ == "__main__":
    token = refresh_access_token()
    if token:
        print("新 token 已写入 .env")
    else:
        sys.exit(1)