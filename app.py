# --- إصلاح مبدئي لتوافق instabot مع Python 3.13 ---
import sys, types
if "imghdr" not in sys.modules:
    fake_imghdr = types.ModuleType("imghdr")
    fake_imghdr.what = lambda *args, **kwargs: None
    sys.modules["imghdr"] = fake_imghdr
# ---------------------------------------------------

from flask import Flask, request, render_template_string
import threading
import tempfile
import shutil
import os
import time
import random
from instabot import Bot

app = Flask(__name__)

# ================== إعداد واجهة HTML ==================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>نظام المتابعة الآلي 🤖</title>
    <style>
        body { font-family: Tahoma; background: #f2f2f2; text-align: center; margin-top: 70px; }
        form { background: white; display: inline-block; padding: 25px; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.2); }
        input, button { padding: 10px; margin: 8px; border-radius: 8px; border: 1px solid #ccc; }
        button { background: #008CBA; color: white; cursor: pointer; font-weight: bold; }
        button:hover { background: #005f73; }
        .msg { margin-top: 20px; font-weight: bold; color: green; }
    </style>
</head>
<body>
    <h2>🚀 نظام المتابعة الآلي (Render)</h2>
    <form method="POST">
        <label>اسم الحساب الهدف:</label><br>
        <input name="target" placeholder="مثال: instagram" required><br><br>
        <label>عدد الحسابات التي ستتابع:</label><br>
        <input name="count" type="number" min="1" max="6" value="1"><br><br>
        <button type="submit">ابدأ المتابعة ✅</button>
    </form>
    {% if message %}
        <div class="msg">{{ message }}</div>
    {% endif %}
</body>
</html>
"""

# ================== دالة تنفيذ المتابعة ==================
def follow_main_with_account(username, password, target):
    session_dir = tempfile.mkdtemp(prefix=f"instabot_{username}_")
    try:
        bot = Bot(base_path=session_dir)
        success = bot.login(username=username, password=password)
        if not success:
            print(f"[{username}] فشل تسجيل الدخول ❌")
            return False

        target_id = bot.get_user_id_from_username(target)
        if not target_id:
            print(f"[{username}] لم يتم العثور على المستخدم {target}")
            return False

        res = bot.follow(target)
        print(f"[{username}] تمت المتابعة ✅ => النتيجة: {res}")
        time.sleep(random.uniform(5, 10))
        bot.logout()
        return True
    except Exception as e:
        print(f"[{username}] خطأ أثناء التنفيذ: {e}")
        return False
    finally:
        shutil.rmtree(session_dir, ignore_errors=True)

# ================== دالة إدارة المهمة ==================
def start_follow_job(target, count):
    accounts_raw = os.getenv("ACCOUNTS", "")
    password = os.getenv("COMMON_PASSWORD", "")
    if not accounts_raw or not password:
        print("⚠️ تأكد من ضبط متغيرات البيئة ACCOUNTS و COMMON_PASSWORD")
        return

    accounts = [a.strip() for a in accounts_raw.split(";") if a.strip()]
    selected = accounts[:count]
    print(f"🚀 بدء المهمة: {target} عبر {len(selected)} حسابات")

    success_count = 0
    for acc in selected:
        ok = follow_main_with_account(acc, password, target)
        if ok:
            success_count += 1

    print(f"✅ انتهت العملية: {success_count}/{len(selected)} حساب تابع {target}")

# ================== واجهة Flask ==================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        target = request.form.get("target")
        count = int(request.form.get("count", 1))

        # تشغيل المهمة في خيط مستقل داخل Render
        thread = threading.Thread(target=start_follow_job, args=(target, count))
        thread.start()

        msg = f"🚀 تم بدء المهمة لمتابعة الحساب ({target}) باستخدام {count} حسابات. العملية تعمل الآن في الخلفية على Render."
        return render_template_string(HTML_PAGE, message=msg)

    return render_template_string(HTML_PAGE)

# ================== تشغيل الخدمة ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
