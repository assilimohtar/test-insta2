# app.py
# Web UI لطلب متابعة حساب من عدة حسابات Instagram (shared password)
# ملاحظة: تأكد من ضبط متغيرات البيئة في Render كما في أسفل هذه الصفحة.

from flask import Flask, render_template_string, request, redirect, url_for
import os, sys, types, tempfile, shutil, time, random

# --- إصلاح مبدئي لتوافق instabot مع Python 3.13 ---
if "imghdr" not in sys.modules:
    fake_imghdr = types.ModuleType("imghdr")
    fake_imghdr.what = lambda *args, **kwargs: None
    sys.modules["imghdr"] = fake_imghdr
# ---------------------------------------------------

from instabot import Bot

app = Flask(__name__)

# قراءة حسابات المستخدمين وكلمة السر المشتركة من متغيرات البيئة
# ACCOUNTS: "user1;user2;user3;user4;user5;user6"
# COMMON_PASSWORD: "same_password_for_all"
accounts_env = os.getenv("ACCOUNTS", "")
COMMON_PASSWORD = os.getenv("COMMON_PASSWORD", "")

ACCOUNTS = [u.strip() for u in accounts_env.split(";") if u.strip()]

# تأكد من مجلد مؤقت للـ instabot لتفادي مشاكل الكتابة في /opt/render/project/src
TMP_CONFIG_DIR = "/tmp/instabot_config"
os.makedirs(TMP_CONFIG_DIR, exist_ok=True)
os.environ["TMPDIR"] = TMP_CONFIG_DIR

# قالب HTML بسيط
INDEX_HTML = """
<!doctype html>
<html lang="ar">
  <head>
    <meta charset="utf-8">
    <title>Instagram Multi-Follow</title>
    <style>
      body { font-family: Arial, Helvetica, sans-serif; direction: rtl; padding: 20px; }
      input, select { padding: 8px; margin: 6px 0; width: 100%; box-sizing: border-box; }
      button { padding: 10px 14px; }
      .result { background:#f7f7f7; padding:10px; margin-top:10px; border-radius:6px;}
      .ok { color: green; }
      .fail { color: red; }
      .warn { color: orange; }
    </style>
  </head>
  <body>
    <h2>تابع حسابك باستخدام عدة حسابات</h2>

    {% if not accounts %}
      <p class="warn">لم يتم تعيين أي حسابات. عيّن متغير البيئة <code>ACCOUNTS</code> في لوحة Render (مثال: <code>acc1;acc2;acc3</code>).</p>
    {% endif %}

    <form method="post" action="{{ url_for('do_follow') }}">
      <label>اسم الحساب الهدف (Username):</label>
      <input name="target" required placeholder="مثال: instagram" value="{{ target or '' }}" />
      <label>كم عدد الحسابات التي تريد استخدامها؟ (أقصى {{ accounts|length }})</label>
      <select name="count">
        {% for n in range(1, accounts|length + 1) %}
          <option value="{{ n }}" {% if n==default_count %}selected{% endif %}>{{ n }}</option>
        {% endfor %}
      </select>
      <p>قائمة الحسابات المستخدمة (من اليمين لليسار):</p>
      <ul>
        {% for a in accounts %}
          <li>{{ a }}</li>
        {% endfor %}
      </ul>
      <button type="submit">ابدأ المتابعة</button>
    </form>

    {% if results %}
      <h3>النتائج:</h3>
      {% for r in results %}
        <div class="result">
          <strong>{{ r.account }}</strong> —
          {% if r.status == 'ok' %}
            <span class="ok">تمت المتابعة بنجاح</span>
          {% elif r.status == 'challenge' %}
            <span class="fail">فشل: تم طلب تحقق من إنستغرام (challenge_required). افتح تطبيق إنستغرام ووافق على الدخول.</span>
          {% else %}
            <span class="fail">فشل: {{ r.error }}</span>
          {% endif %}
        </div>
      {% endfor %}
      <p>إجمالي الحسابات التي أضافت المتابعة: <strong>{{ results|selectattr('status','equalto','ok')|list|length }}</strong></p>
    {% endif %}
  </body>
</html>
"""

def follow_one(account_username, password, target_username, session_dir_base):
    """
    يحاول تسجيل الدخول بحساب واحد ومتابعة الهدف.
    يرجع dict يحتوي على account, status, error (إن وجد)
    status: 'ok' | 'challenge' | 'fail'
    """
    session_dir = None
    try:
        session_dir = tempfile.mkdtemp(prefix=f"instabot_{account_username}_", dir=session_dir_base)
        bot = Bot(base_path=session_dir, save_logfile=False)
        # تُبطئ الطلبات قليلًا لتبدو طبيعية
        try:
            bot.api.delay_range = [3, 6]
        except Exception:
            pass

        success = bot.login(username=account_username, password=password)
        if not success:
            # حاول قراءة رسالة من logs / api (instabot يطبعها في لوج)
            # لكن هنا نكتفي بإرجاع فشل عام
            # أيضاً قد يكون سبب الفشل هو 'challenge_required'
            last_error = getattr(bot, "last_error", None)
            return {"account": account_username, "status": "fail", "error": f"login failed ({last_error})"}

        # حاول الحصول على id الهدف ثم المتابعة
        try:
            target_id = bot.get_user_id_from_username(target_username)
            if not target_id:
                bot.logout()
                return {"account": account_username, "status": "fail", "error": "target not found"}
            # متابعة
            res = bot.follow(target_username)
            bot.logout()
            if res:
                return {"account": account_username, "status": "ok", "error": None}
            else:
                # قد يكون هناك خطأ متعلّق بالـ API أو challenge
                return {"account": account_username, "status": "fail", "error": "follow API returned False"}
        except Exception as e:
            # تفحّص رسالة الخطأ للتعرّف إن كانت challenge_required
            msg = str(e)
            if "challenge_required" in msg or "checkpoint" in msg or "challenge" in msg:
                return {"account": account_username, "status": "challenge", "error": msg}
            return {"account": account_username, "status": "fail", "error": msg}
    finally:
        # حذف جلسة مؤقتة
        if session_dir:
            try:
                shutil.rmtree(session_dir)
            except Exception:
                pass

@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML, accounts=ACCOUNTS, results=None, target=None, default_count=min(3, max(1, len(ACCOUNTS))))

@app.route("/do_follow", methods=["POST"])
def do_follow():
    target = request.form.get("target", "").strip()
    try:
        count = int(request.form.get("count", "1"))
    except:
        count = 1
    count = max(1, min(count, len(ACCOUNTS)))

    if not ACCOUNTS:
        return render_template_string(INDEX_HTML, accounts=ACCOUNTS, results=None, target=target, default_count=count)

    if not COMMON_PASSWORD:
        # لا نستطيع المتابعة بدون كلمة السر المشتركة
        results = [{"account": a, "status": "fail", "error": "COMMON_PASSWORD not set in environment"} for a in ACCOUNTS[:count]]
        return render_template_string(INDEX_HTML, accounts=ACCOUNTS, results=results, target=target, default_count=count)

    # Sequential execution: نحاول واحدًا تلو الآخر (آمن ويُقلل احتمال الحظر)
    results = []
    for account in ACCOUNTS[:count]:
        r = follow_one(account, COMMON_PASSWORD, target, TMP_CONFIG_DIR)
        results.append(r)
        # تأخير بين الحسابات لتقليل نمط الآلية
        time.sleep(random.uniform(4, 10))

    return render_template_string(INDEX_HTML, accounts=ACCOUNTS, results=results, target=target, default_count=count)

if __name__ == "__main__":
    # تشغيل محلي (debug=True للتطوير فقط)
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
