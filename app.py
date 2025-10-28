import os
import tempfile
import shutil
import time
import random
from instabot import Bot

# متغير البيئة يجب أن يكون بالشكل "username:password"
SINGLE_ACCOUNT = os.getenv("SINGLE_ACCOUNT")  # مثال: "test_user:test_pass"
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")      # الحساب الذي تريد أن يتبعه الحساب التجريبي

if not SINGLE_ACCOUNT or not MAIN_ACCOUNT:
    raise SystemExit("Please set SINGLE_ACCOUNT and MAIN_ACCOUNT environment variables (format: user:pass).")

username, password = SINGLE_ACCOUNT.split(":", 1)
username = username.strip()
password = password.strip()

def follow_main_with_account(user, pwd):
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{user}_")
    try:
        # بعض نسخ instabot تستخدم param اسمه base_path أو config_path
        bot = Bot(base_path=session_dir)
        success = bot.login(username=user, password=pwd)
        if not success:
            print(f"[{user}] تسجيل الدخول فشل")
            return

        try:
            # الحصول على id الهدف ومحاولة المتابعة
            target_id = bot.get_user_id_from_username(MAIN_ACCOUNT)
            if not target_id:
                print(f"[{user}] لم أجد المستخدم {MAIN_ACCOUNT}")
            else:
                # بعض الإصدارات ترجع قائمة متابعة بأشكال مختلفة، لذلك نتعامل ببساطة بمحاولة follow مباشرة
                res = bot.follow(MAIN_ACCOUNT)
                print(f"[{user}] نتيجة المتابعة: {res}")
        except Exception as e:
            print(f"[{user}] خطأ أثناء المتابعة: {e}")

        # تأخير عشوائي لحركة أكثر "طبيعية"
        time.sleep(random.uniform(6, 20))

        bot.logout()
    except Exception as e:
        print(f"[{user}] خطأ غير متوقع: {e}")
    finally:
        # حذف مجلد الجلسة
        try:
            shutil.rmtree(session_dir)
        except Exception:
            pass

if __name__ == "__main__":
    follow_main_with_account(username, password)
