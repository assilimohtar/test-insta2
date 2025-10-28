import time
import requests
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# إعدادات
NUM_ACCOUNTS = 10
CHROMEDRIVER_PATH = "chromedriver"  # غير المسار إذا وضعته في مجلد آخر
INSTAGRAM_URL = "https://www.instagram.com/accounts/emailsignup/"

# تهيئة متصفح بدون نافذة (Headless)
def get_browser():
    options = Options()
    options.headless = False  # اتركها False للمراقبة - ممكن تفعيلها للتحكم التلقائي على خوادم بدون display
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
    return driver

# توليد بريد مؤقت من 1secmail
def generate_temp_email():
    login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = "1secmail.com"
    email = f"{login}@{domain}"
    return login, email

# التحقق من البريد ومعرفة الرسائل الجديدة
def check_email(login):
    url = f"https://1secmail.com/api/v1/?action=getMessages&login={login}&domain=1secmail.com"
    response = requests.get(url)
    return response.json()

# قراءة الرسالة وتحليل المحتوى
def read_email(login, message_id):
    url = f"https://1secmail.com/api/v1/?action=readMessage&login={login}&domain=1secmail.com&id={message_id}"
    response = requests.get(url)
    return response.json()

# انتظار وصول رسالة التحقق
def wait_for_email(login, subject_keyword, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        messages = check_email(login)
        for msg in messages:
            if subject_keyword in msg['subject']:
                full_msg = read_email(login, msg['id'])
                return full_msg['body']
        time.sleep(10)
    return None

# إنشاء حساب انستجرام
def create_instagram_account(email, password, driver):
    driver.get(INSTAGRAM_URL)
    time.sleep(5)

    # ملء النموذج
    email_input = driver.find_element(By.NAME, 'emailOrPhone')
    email_input.send_keys(email)
    full_name = 'AutoUser' + ''.join(random.choices(string.ascii_letters, k=5))
    name_input = driver.find_element(By.NAME, 'fullName')
    name_input.send_keys(full_name)
    username = 'auto' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    username_input = driver.find_element(By.NAME, 'username')
    username_input.send_keys(username)
    password_input = driver.find_element(By.NAME, 'password')
    password_input.send_keys(password)

    # الضغط على زر التسجيل (ممكن يختلف حسب التحديثات)
    sign_up_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Sign up')]")
    sign_up_button.click()

    time.sleep(10)

    # قد يكون هناك مراحل إضافية مثل التحقق عبر الكابتشا أو الكود
    # لهذا نحتاج لدمج أدوات حل الكابتشا أو التعامل مع رسالة التحقق المرسلة للبريد الالكتروني

    return username, password

# إعداد الحساب:
def setup_account():
    login, email = generate_temp_email()
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    driver = get_browser()
    try:
        username_created, pass_created = create_instagram_account(email, password, driver)

        # انتظار وصول البريد للتحقق
        print(f"انتظار التحقق لبريد: {email}")
        email_body = wait_for_email(login, "Instagram")
        if email_body:
            # استخراج الرابط أو الكود من البريد
            verification_link = extract_verification_link(email_body)
            # زيارة الرابط أو إدخال الكود
            # يمكنك هنا أتمتة إدخال الكود أو فتح الرابط لإتمام التحقق
            print(f"تم استلام رسالة التحقق، الرابط: {verification_link}")
            # يمكن زيارة الرابط هنا
            driver.get(verification_link)
            time.sleep(5)
        else:
            print("لم تصل رسالة التحقق خلال الوقت المحدد.")
        return {
            "username": username_created,
            "password": pass_created,
            "email": email
        }
    except Exception as e:
        print(f"خطأ: {e}")
    finally:
        driver.quit()

def extract_verification_link(email_body):
    # هنا تكتب regex لاستخراج الرابط من البريد
    import re
    pattern = r'https://www.instagram.com/accounts/emailsignup/[^"\s]+'
    match = re.search(pattern, email_body)
    if match:
        return match.group(0)
    return None

# البرنامج الرئيسي
def main():
    accounts = []
    for i in range(NUM_ACCOUNTS):
        print(f"بدأ تشغيل الحساب رقم {i+1}")
        account_info = setup_account()
        if account_info:
            accounts.append(account_info)
        time.sleep(20)  # تقليل حظر الحسابات
    print("تم إنشاء جميع الحسابات:")
    for acc in accounts:
        print(acc)

if __name__ == "__main__":
    main()
