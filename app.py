import os
import time
import random
from flask import Flask, jsonify
from instagram_private_api import Client, ClientError

app = Flask(__name__)

class InstagramManager:
    def __init__(self):
        self.user_agents = [
            'Instagram 219.0.0.12.117 Android',
            'Instagram 267.0.0.19.301 iOS',
            'Instagram 276.0.0.17.92 Android'
        ]
    
    def create_client(self, username, password):
        """إنشاء عميل Instagram مع إعدادات متقدمة"""
        try:
            device_settings = {
                'app_version': '267.0.0.19.301',
                'android_version': 25,
                'android_release': '7.1.1',
                'phone_manufacturer': 'samsung',
                'phone_device': 'herolte',
                'phone_model': 'SM-G930F'
            }
            
            api = Client(
                username=username,
                password=password,
                settings=None,
                **device_settings
            )
            
            return api
        except ClientError as e:
            print(f"🚨 خطأ في إنشاء العميل: {e}")
            return None
    
    def follow_user(self, api, target_username):
        """متابعة مستخدم بإعدادات أمان"""
        try:
            search_result = api.username_info(target_username)
            target_user_id = search_result['user']['pk']
            
            friendship_status = api.friendships_show(target_user_id)
            
            if friendship_status['following']:
                return True, "متابع بالفعل"
            
            time.sleep(random.uniform(5, 10))
            
            api.friendships_create(target_user_id)
            
            time.sleep(2)
            new_status = api.friendships_show(target_user_id)
            
            if new_status['following']:
                return True, "تم المتابعة بنجاح"
            else:
                return False, "فشل في المتابعة"
                
        except ClientError as e:
            error_msg = str(e)
            if "challenge_required" in error_msg:
                return False, "يحتاج تحقق أمني - سجل دخول يدوي"
            elif "rate_limit" in error_msg:
                return False, "تم حظر الطلبات مؤقتاً"
            else:
                return False, f"خطأ: {error_msg}"

manager = InstagramManager()

@app.route('/smart-follow')
def smart_follow():
    """المتابعة الذكية مع معالجة الأخطاء"""
    ACCOUNTS = os.getenv("ACCOUNTS", "")
    MAIN_ACCOUNT = os.getenv("MAIN_ACCOUNT", "")
    
    if not ACCOUNTS or not MAIN_ACCOUNT:
        return jsonify({"error": "تأكد من ضبط ACCOUNTS و MAIN_ACCOUNT"})
    
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
        print(f"🎯 معالجة الحساب {i+1}/{len(accounts_list)}: {account['username']}")
        
        try:
            api = manager.create_client(account['username'], account['password'])
            
            if api:
                success, message = manager.follow_user(api, MAIN_ACCOUNT)
                
                results.append({
                    'account': account['username'],
                    'status': 'success' if success else 'failed',
                    'message': message
                })
                
                api.logout()
            else:
                results.append({
                    'account': account['username'],
                    'status': 'failed',
                    'message': 'فشل في تهيئة العميل'
                })
            
        except Exception as e:
            results.append({
                'account': account['username'],
                'status': 'failed',
                'message': f'خطأ غير متوقع: {str(e)}'
            })
        
        if i < len(accounts_list) - 1:
            wait_time = random.uniform(120, 300)
            print(f"⏳ انتظار {wait_time/60:.1f} دقائق...")
            time.sleep(wait_time)
    
    return jsonify({
        'target_account': MAIN_ACCOUNT,
        'total_accounts': len(accounts_list),
        'successful': len([r for r in results if r['status'] == 'success']),
        'results': results
    })

@app.route('/')
def home():
    return jsonify({
        'message': 'Instagram Smart Bot - استخدم /smart-follow',
        'status': 'active'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
