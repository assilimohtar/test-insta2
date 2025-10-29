# --- إصلاح مبدئي لتوافق instabot مع Python 3.13 ---
import sys, types
if "imghdr" not in sys.modules:
    fake_imghdr = types.ModuleType("imghdr")
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
# ACCOUNTS = "user1:pass1,user2:pass2,user3:pass3"
# MAIN_ACCOUNT = "target_to_follow"

ACCOUNTS = os.getenv("ACCOUNTS")
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")

if not ACCOUNTS or not MAIN_ACCOUNT:
    raise SystemExit("⚠️ يجب ضبط متغيرات البيئة ACCOUNTS و MAIN_ACCOUNT")

def parse_accounts(accounts_str):
    """تحويل سلسلة الحسابات إلى قائمة"""
    accounts = []
    for account in accounts_str.split(','):
        if ':' in account:
            user, pwd = account.split(':', 1)
            accounts.append({
                'username': user.strip(),
                'password': pwd.strip()
            })
    return accounts

def follow_main_with_account(user, pwd):
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{user}_")
    try:
        bot = Bot(base_path=session_dir)
        success = bot.login(username=user, password=pwd)
        if not success:
            print(f"[{user}] فشل تسجيل الدخول")
            return False

        try:
            target_id = bot.get_user_id_from_username(MAIN_ACCOUNT)
            if not target_id:
                print(f"[{user}] لم يتم العثور على المستخدم {MAIN_ACCOUNT}")
                return False
            
            # التحقق إذا كان يتابع بالفعل
            following = bot.get_user_following(bot.user_id)
            if target_id in following:
                print(f"[{user}] يتابع {MAIN_ACCOUNT} بالفعل")
                return True
            
            # إجراء المتابعة
            res = bot.follow(target_id)
            if res:
                print(f"[{user}] ✅ تم متابعة {MAIN_ACCOUNT} بنجاح")
            else:
                print(f"[{user}] ❌ فشل في متابعة {MAIN_ACCOUNT}")
            return res
            
        except Exception as e:
            print(f"[{user}] خطأ أثناء المتابعة: {e}")
            return False

        time.sleep(random.uniform(10, 30))
        bot.logout()
        return True
        
    except Exception as e:
        print(f"[{user}] خطأ غير متوقع: {e}")
        return False
    finally:
        try:
            shutil.rmtree(session_dir)
        except Exception:
            pass

def run_all_accounts():
    """تشغيل المتابعة لجميع الحسابات"""
    accounts = parse_accounts(ACCOUNTS)
    
    if not accounts:
        print("❌ لم يتم العثور على حسابات صحيحة")
        return
    
    print(f"🎯 بدء المتابعة للحساب: {MAIN_ACCOUNT}")
    print(f"📊 عدد الحسابات: {len(accounts)}")
    
    success_count = 0
    for i, account in enumerate(accounts, 1):
        print(f"\n--- [{i}/{len(accounts)}] معالجة {account['username']} ---")
        
        success = follow_main_with_account(account['username'], account['password'])
        if success:
            success_count += 1
        
        # وقت انتظار بين الحسابات (تجنب الاكتشاف)
        if i < len(accounts):
            wait_time = random.uniform(60, 180)  # 1-3 دقائق
            print(f"⏳ انتظار {wait_time:.0f} ثانية للحساب التالي...")
            time.sleep(wait_time)
    
    print(f"\n🎊 الانتهاء! نجح {success_count} من أصل {len(accounts)} حسابات")

if __name__ == "__main__":
    run_all_accounts()
