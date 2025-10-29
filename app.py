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
import logging
from flask import Flask, jsonify
from instabot import Bot

# ⚠️ تقليل التسجيل المفرط
logging.getLogger("instabot").setLevel(logging.ERROR)

# 🟢 متغيرات البيئة في Render
ACCOUNTS = os.getenv("ACCOUNTS")
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")

# إنشاء تطبيق Flask
app = Flask(__name__)

def check_environment():
    """التحقق من متغيرات البيئة"""
    if not ACCOUNTS:
        return False, "ACCOUNTS environment variable not set"
    
    if not MAIN_ACCOUNT:
        return False, "MAIN_ACCOUNT environment variable not set"
    
    return True, "Environment variables are set"

def parse_accounts(accounts_str):
    """تحويل سلسلة الحسابات إلى قائمة"""
    accounts = []
    for account in accounts_str.split(','):
        account = account.strip()
        if ':' in account:
            user, pwd = account.split(':', 1)
            accounts.append({
                'username': user.strip(),
                'password': pwd.strip()
            })
    return accounts

def safe_login(bot, username, password, max_retries=2):
    """تسجيل دخول آمن مع إعادة المحاولة"""
    for attempt in range(max_retries):
        try:
            print(f"🔐 محاولة تسجيل الدخول ({attempt + 1}/{max_retries}) لـ {username}")
            
            # إعدادات لتجنب الحظر
            bot.api.delay_range = [5, 10]
            bot.api.timeout = 30
            
            success = bot.login(username=username, password=password, use_cookie=False)
            
            if success:
                print(f"✅ تم تسجيل الدخول: {username}")
                return True
            else:
                print(f"❌ فشل تسجيل الدخول: {username}")
                
                if attempt < max_retries - 1:
                    wait_time = random.uniform(30, 60)
                    print(f"⏳ انتظار {wait_time:.0f} ثانية قبل إعادة المحاولة...")
                    time.sleep(wait_time)
                    
        except Exception as e:
            print(f"🚨 خطأ في تسجيل الدخول: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(30, 60))
    
    return False

def follow_main_with_account(user, pwd):
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{user}_")
    try:
        bot = Bot(base_path=session_dir)
        
        # تسجيل الدخول الآمن
        if not safe_login(bot, user, pwd):
            return False, "فشل تسجيل الدخول"
        
        try:
            print(f"🎯 البحث عن الحساب: {MAIN_ACCOUNT}")
            time.sleep(random.uniform(3, 8))
            
            target_id = bot.get_user_id_from_username(MAIN_ACCOUNT)
            if not target_id:
                return False, f"لم يتم العثور على {MAIN_ACCOUNT}"
            
            time.sleep(random.uniform(3, 8))
            
            # التحقق إذا كان يتابع بالفعل
            print(f"🔍 التحقق من المتابعة الحالية...")
            try:
                following = bot.get_user_following(bot.user_id)
                if target_id in following:
                    return True, f"يتابع {MAIN_ACCOUNT} بالفعل"
            except Exception as e:
                print(f"⚠️ خطأ في التحقق من المتابعة: {e}")
            
            time.sleep(random.uniform(5, 15))
            
            # إجراء المتابعة
            print(f"🔄 محاولة متابعة {MAIN_ACCOUNT}...")
            res = bot.follow(target_id)
            
            if res:
                return True, f"تم متابعة {MAIN_ACCOUNT} بنجاح"
            else:
                return False, f"فشل في متابعة {MAIN_ACCOUNT}"
            
        except Exception as e:
            return False, f"خطأ أثناء المتابعة: {str(e)}"

        finally:
            time.sleep(random.uniform(5, 10))
            try:
                bot.logout()
                print(f"🚪 تم تسجيل الخروج: {user}")
            except:
                pass

    except Exception as e:
        return False, f"خطأ غير متوقع: {str(e)}"
    finally:
        try:
            shutil.rmtree(session_dir)
        except Exception:
            pass

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    env_check, env_message = check_environment()
    
    status = {
        "status": "running",
        "service": "Instagram Bot",
        "environment_check": env_check,
        "environment_message": env_message,
        "main_account": MAIN_ACCOUNT if MAIN_ACCOUNT else "Not set",
        "accounts_count": len(parse_accounts(ACCOUNTS)) if ACCOUNTS else 0
    }
    return jsonify(status)

@app.route('/run-bot')
def run_bot():
    """تشغيل البوت"""
    try:
        env_check, env_message = check_environment()
        if not env_check:
            return jsonify({"success": False, "message": env_message})
        
        accounts = parse_accounts(ACCOUNTS)
        
        if not accounts:
            return jsonify({"success": False, "message": "No valid accounts found"})
        
        results = []
        success_count = 0
        
        for i, account in enumerate(accounts, 1):
            account_result = {
                "account": account['username'],
                "number": f"{i}/{len(accounts)}"
            }
            
            print(f"\n--- [{i}/{len(accounts)}] معالجة {account['username']} ---")
            
            success, message = follow_main_with_account(account['username'], account['password'])
            
            account_result["success"] = success
            account_result["message"] = message
            
            if success:
                success_count += 1
            
            results.append(account_result)
            
            # وقت انتظار بين الحسابات
            if i < len(accounts):
                wait_time = random.uniform(120, 300)  # 2-5 دقائق
                print(f"⏳ انتظار {wait_time/60:.1f} دقائق للحساب التالي...")
                time.sleep(wait_time)
        
        return jsonify({
            "success": True,
            "message": f"تم الانتهاء! نجح {success_count} من أصل {len(accounts)}",
            "results": results
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"خطأ: {str(e)}"})

@app.route('/health')
def health():
    """نقطة فحص الصحة"""
    return jsonify({"status": "healthy", "timestamp": time.time()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
