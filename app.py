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
from instabot import Bot

# ⚡ تحسينات الأمان والأداء
class AdvancedInstagramBot:
    def __init__(self):
        # إعدادات مضادة للحظر
        self.delay_ranges = {
            'login': [5, 10],
            'search': [3, 7], 
            'follow': [8, 15],
            'between_accounts': [120, 300]  # 2-5 دقائق
        }
        
        # تقليل التسجيل المفرط
        logging.getLogger("instabot").setLevel(logging.ERROR)
    
    def safe_login(self, bot, username, password, max_retries=2):
        """تسجيل دخول آمن مع إعادة محاولة"""
        for attempt in range(max_retries):
            try:
                print(f"🔐 محاولة تسجيل الدخول ({attempt + 1}/{max_retries}) لـ {username}")
                
                # إعدادات البوت المضادة للحظر
                bot.api.delay_range = self.delay_ranges['login']
                bot.api.timeout = 30
                
                success = bot.login(username=username, password=password, use_cookie=False)
                
                if success:
                    print(f"✅ تم تسجيل الدخول بنجاح: {username}")
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
    
    def safe_follow(self, bot, target_username):
        """متابعة آمنة مع معالجة الأخطاء"""
        try:
            print(f"🎯 البحث عن المستخدم: {target_username}")
            
            # انتظار عشوائي قبل البحث
            time.sleep(random.uniform(*self.delay_ranges['search']))
            
            target_id = bot.get_user_id_from_username(target_username)
            if not target_id:
                return False, f"لم يتم العثور على المستخدم {target_username}"
            
            # التحقق من المتابعة الحالية
            print("🔍 التحقق من حالة المتابعة...")
            try:
                following = bot.get_user_following(bot.user_id)
                if target_id in following:
                    return True, f"يتبع {target_username} بالفعل"
            except Exception as e:
                print(f"⚠️ خطأ في التحقق من المتابعة: {e}")
            
            # انتظار عشوائي قبل المتابعة
            time.sleep(random.uniform(*self.delay_ranges['follow']))
            
            # تنفيذ المتابعة
            print(f"🔄 محاولة متابعة {target_username}...")
            result = bot.follow(target_id)
            
            if result:
                return True, f"تم متابعة {target_username} بنجاح"
            else:
                return False, f"فشل في متابعة {target_username}"
                
        except Exception as e:
            error_msg = str(e)
            if "challenge_required" in error_msg:
                return False, "يحتاج تحقق أمني - سجل دخول يدوي من الهاتف"
            elif "rate_limit" in error_msg:
                return False, "تم حظر الطلبات مؤقتاً - جرب لاحقاً"
            else:
                return False, f"خطأ غير متوقع: {error_msg}"

# 🟢 متغيرات البيئة في Render:
ACCOUNTS = os.getenv("ACCOUNTS")  # دعم متعدد الحسابات
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")

if not ACCOUNTS or not MAIN_ACCOUNT:
    raise SystemExit("⚠️ يجب ضبط متغيرات البيئة ACCOUNTS و MAIN_ACCOUNT (مثال: user1:pass1,user2:pass2)")

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

def follow_main_with_account(user, pwd):
    """الدالة الرئيسية المحسنة"""
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{user}_")
    advanced_bot = AdvancedInstagramBot()
    
    try:
        bot = Bot(base_path=session_dir)
        
        # تسجيل الدخول الآمن
        login_success = advanced_bot.safe_login(bot, user, pwd)
        if not login_success:
            print(f"❌ فشل تسجيل الدخول النهائي لـ {user}")
            return False, "فشل تسجيل الدخول"

        # المتابعة الآمنة
        follow_success, message = advanced_bot.safe_follow(bot, MAIN_ACCOUNT)
        
        print(f"📊 نتيجة {user}: {message}")
        
        # انتظار نهائي قبل تسجيل الخروج
        time.sleep(random.uniform(10, 20))
        
        # تسجيل الخروج الآمن
        try:
            bot.logout()
            print(f"🚪 تم تسجيل الخروج: {user}")
        except Exception as e:
            print(f"⚠️ خطأ في تسجيل الخروج: {e}")
        
        return follow_success, message
        
    except Exception as e:
        print(f"🚨 خطأ غير متوقع في {user}: {e}")
        return False, f"خطأ غير متوقع: {str(e)}"
    finally:
        # تنظيف الملفات المؤقتة
        try:
            shutil.rmtree(session_dir)
            print(f"🧹 تم تنظيف الملفات المؤقتة لـ {user}")
        except Exception as e:
            print(f"⚠️ خطأ في التنظيف: {e}")

def run_all_accounts():
    """تشغيل جميع الحسابات مع إدارة ذكية"""
    accounts = parse_accounts(ACCOUNTS)
    
    if not accounts:
        print("❌ لم يتم العثور على حسابات صحيحة")
        return
    
    print(f"\n🎯 بدء عملية المتابعة المتقدمة")
    print(f"📌 الحساب المستهدف: {MAIN_ACCOUNT}")
    print(f"👥 عدد الحسابات: {len(accounts)}")
    print("=" * 50)
    
    success_count = 0
    total_accounts = len(accounts)
    
    for i, account in enumerate(accounts, 1):
        print(f"\n--- [{i}/{total_accounts}] معالجة {account['username']} ---")
        
        success, message = follow_main_with_account(account['username'], account['password'])
        
        if success:
            success_count += 1
            print(f"✅ نجح الحساب {i}")
        else:
            print(f"❌ فشل الحساب {i}: {message}")
        
        # انتظار ذكي بين الحسابات
        if i < total_accounts:
            wait_time = random.uniform(*advanced_bot.delay_ranges['between_accounts'])
            minutes = wait_time / 60
            print(f"⏳ انتظار {minutes:.1f} دقائق للحساب التالي...")
            time.sleep(wait_time)
    
    # تقرير نهائي
    print(f"\n{'='*50}")
    print(f"🎊 الانتهاء من جميع الحسابات!")
    print(f"✅ نجح: {success_count}/{total_accounts}")
    print(f"❌ فشل: {total_accounts - success_count}/{total_accounts}")
    print(f"📈 نسبة النجاح: {(success_count/total_accounts)*100:.1f}%")
    print(f"{'='*50}")

if __name__ == "__main__":
    print("🚀 بدء تشغيل بوت Instagram المتقدم")
    print("⚡ إصدار محسّن - مضاد للحظر - إدارة أخطاء متقدمة")
    run_all_accounts()
    print("🏁 انتهى التنفيذ")
