import os
import time
import random
from flask import Flask, jsonify
from instagram_private_api import Client, ClientError

app = Flask(__name__)

# 🟢 متغيرات البيئة
ACCOUNTS = os.getenv("ACCOUNTS")
MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT")

class InstagramBot:
    def __init__(self):
        self.device_settings = {
            'app_version': '267.0.0.19.301',
            'android_version': 25,
            'android_release': '7.1.1',
            'phone_manufacturer': 'samsung', 
            'phone_device': 'herolte',
            'phone_model': 'SM-G930F'
        }
    
    def login(self, username, password):
        """تسجيل الدخول الفعلي"""
        try:
            print(f"🔐 محاولة تسجيل الدخول لـ: {username}")
            api = Client(
                username=username,
                password=password, 
                settings=None,
                **self.device_settings
            )
            print(f"✅ تم تسجيل الدخول: {username}")
            return api
        except ClientError as e:
            print(f"❌ فشل تسجيل الدخول لـ {username}: {e}")
            return None
    
    def follow_user(self, api, target_username):
        """متابعة فعلية للمستخدم"""
        try:
            print(f"🎯 البحث عن المستخدم: {target_username}")
            
            # الحصول على معلومات المستخدم
            user_info = api.username_info(target_username)
            target_user_id = user_info['user']['pk']
            
            print(f"📋 التحقق من حالة المتابعة...")
            friendship_status = api.friendships_show(target_user_id)
            
            if friendship_status['following']:
                return True, "يتبع المستخدم بالفعل"
            
            print(f"🔄 إرسال طلب المتابعة...")
            # انتظار عشوائي قبل المتابعة
            time.sleep(random.uniform(5, 10))
            
            # المتابعة الفعلية
            api.friendships_create(target_user_id)
            
            # تأكيد المتابعة
            time.sleep(3)
            new_status = api.friendships_show(target_user_id)
            
            if new_status['following']:
                return True, "تمت المتابعة بنجاح"
            else:
                return False, "فشل في المتابعة"
                
        except ClientError as e:
            error_msg = str(e)
            if "challenge_required" in error_msg:
                return False, "يحتاج تحقق أمني"
            elif "rate_limit" in error_msg:
                return False, "تم حظر الطلبات مؤقتاً"
            else:
                return False, f"خطأ: {error_msg}"

# إنشاء كائن البوت
bot = InstagramBot()

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "message": "Instagram Bot - استخدم /follow",
        "main_account": MAIN_ACCOUNT
    })

@app.route('/follow')
def follow():
    """التنفيذ الفعلي للمتابعة"""
    try:
        if not ACCOUNTS or not MAIN_ACCOUNT:
            return jsonify({
                "success": False,
                "message": "تأكد من ضبط ACCOUNTS و MAIN_ACCOUNT"
            })
        
        # تحليل الحسابات
        accounts_list = []
        for acc in ACCOUNTS.split(','):
            if ':' in acc:
                user, pwd = acc.split(':', 1)
                accounts_list.append({
                    'username': user.strip(),
                    'password': pwd.strip()
                })
        
        results = []
        
        for i, account in enumerate(accounts_list):
            print(f"🔧 معالجة الحساب {i+1}: {account['username']}")
            
            # التسجيل الفعلي
            api = bot.login(account['username'], account['password'])
            
            if api:
                # المتابعة الفعلية
                success, message = bot.follow_user(api, MAIN_ACCOUNT)
                
                results.append({
                    "account": account['username'],
                    "status": "success" if success else "failed", 
                    "message": message
                })
                
                # تسجيل الخروج
                try:
                    api.logout()
                    print(f"🚪 تم تسجيل الخروج: {account['username']}")
                except:
                    pass
                    
            else:
                results.append({
                    "account": account['username"],
                    "status": "failed",
                    "message": "فشل في تسجيل الدخول"
                })
            
            # انتظار بين الحسابات
            if i < len(accounts_list) - 1:
                wait_time = random.uniform(60, 120)
                print(f"⏳ انتظار {wait_time} ثانية للحساب التالي...")
                time.sleep(wait_time)
        
        return jsonify({
            "success": True,
            "message": "تم الانتهاء من المتابعة",
            "target_account": MAIN_ACCOUNT, 
            "results": results
        })
        
    except Exception as e:
        print(f"💥 خطأ رئيسي: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
