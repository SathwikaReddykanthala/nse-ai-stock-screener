import os
import pyotp
from dotenv import load_dotenv
from SmartApi import SmartConnect

load_dotenv()

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_CODE")
PASSWORD = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")

required = {
    "ANGEL_API_KEY": API_KEY,
    "ANGEL_CLIENT_CODE": CLIENT_CODE,
    "ANGEL_PASSWORD": PASSWORD,
    "ANGEL_TOTP_SECRET": TOTP_SECRET,
}

missing = [name for name, value in required.items() if not value]

if missing:
    raise RuntimeError(
        "Missing values in .env: " + ", ".join(missing)
    )

print("Connecting to Angel One...")

smart_api = SmartConnect(api_key=API_KEY)

try:
    current_totp = pyotp.TOTP(TOTP_SECRET).now()

    response = smart_api.generateSession(
        CLIENT_CODE,
        PASSWORD,
        current_totp
    )

    if not response.get("status"):
        print("\nLOGIN FAILED")
        print(response)
        raise SystemExit(1)

    data = response.get("data", {})

    jwt_token = data.get("jwtToken")
    refresh_token = data.get("refreshToken")
    feed_token = smart_api.getfeedToken()

    print("\n================================")
    print("ANGEL ONE LOGIN SUCCESS")
    print("================================")
    print("Client Code :", CLIENT_CODE)
    print("JWT Token   :", "OK" if jwt_token else "MISSING")
    print("Refresh     :", "OK" if refresh_token else "MISSING")
    print("Feed Token  :", "OK" if feed_token else "MISSING")
    print("================================")

except Exception as e:
    print("\nLOGIN ERROR:")
    print(type(e).__name__)
    print(str(e))