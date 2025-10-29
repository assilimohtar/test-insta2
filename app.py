# --- إصلاح مبدئي لتوافق instabot مع Python 3.13 ---
import sys, types
if "imghdr" not in sys.modules:
    fake_imghdr = types.ModuleType("imghdr")
    # دالة وهمية لتجنّب خطأ import imghdr في instabot
    fake_imghdr.what = lambda *args, **kwargs: None
    sys.modules["imghdr"] = fake_imghdr
# ---------------------------------------------------

import os
import tempfile
import shutil
import time
import random
from instabot import Bot

# 🟢 متغيرات البيئة في Render:
# SINGLE_ACCOUNT = "username:password"
# MAIN_ACCOUNT   = "target_to_follow"

SINGLE_ACCOUNT = os.getenv("SINGLE_ACCOUNT")
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")

if not SINGLE_ACCOUNT or not MAIN_ACCOUNT:
    raise SystemExit("⚠️ يجب ضبط متغيرات البيئة SINGLE_ACCOUNT و MAIN_ACCOUNT (مثال: user:pass)")

username, password = SINGLE_ACCOUNT.split(":", 1)
username = username.strip()
password = password.strip()

def follow_main_with_account(user, pwd):
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{user}_")
    try:
        bot = Bot(base_path=session_dir)
        success = bot.login(username=user, password=pwd)
        if not success:
            print(f"[{user}] فشل تسجيل الدخول")
            return

        try:
            target_id = bot.get_user_id_from_username(MAIN_ACCOUNT)
            if not target_id:
                print(f"[{user}] لم يتم العثور على المستخدم {MAIN_ACCOUNT}")
            else:
                res = bot.follow(MAIN_ACCOUNT)
                print(f"[{user}] نتيجة المتابعة: {res}")
        except Exception as e:
            print(f"[{user}] خطأ أثناء المتابعة: {e}")

        time.sleep(random.uniform(6, 20))
        bot.logout()
    except Exception as e:
        print(f"[{user}] خطأ غير متوقع: {e}")
    finally:
        try:
            shutil.rmtree(session_dir)
        except Exception:
            pass

if __name__ == "__main__":
    follow_main_with_account(username, password)
