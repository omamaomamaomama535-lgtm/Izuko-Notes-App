from flask import Flask, request, redirect, url_for, session, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import DictLoader
import functools
import json  # لاستخدام JSON للحفظ الدائم
import os    # للتحقق من وجود الملف

# اسم ملف قاعدة البيانات الخاص بنا (سيتم إنشاؤه في نفس المجلد)
NOTES_FILE = 'notes_data.json'

# --- دوال حفظ وتحميل البيانات (Persistence) ---

def load_notes():
    """تحميل الملاحظات من ملف JSON إذا كان موجودًا."""
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            try:
                # التحقق إذا كان الملف فارغًا قبل محاولة التحليل
                if os.path.getsize(NOTES_FILE) > 0:
                    return json.load(f)
                else:
                    return []
            except json.JSONDecodeError:
                print("تحذير: ملف JSON تالف أو فارغ. يتم البدء بقائمة ملاحظات فارغة.")
                return []
    return []

def save_notes(data):
    """حفظ الملاحظات في ملف JSON."""
    # نستخدم ensure_ascii=False لدعم اللغة العربية بشكل صحيح
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# 1. تهيئة التطبيق
app = Flask(__name__)
app.secret_key = 'مفتاح_سري_غاية_في_التعقيد' 

# المستخدم الوحيد المصرح له
AUTHORIZED_USER = {
    'username': 'izuko',
    'password_hash': generate_password_hash('izuko12345') 
}

# تحميل الملاحظات عند بدء تشغيل التطبيق لضمان الحفظ الدائم
notes = load_notes() 

# --- دوال الأمان ---
def is_logged_in():
    return session.get('logged_in', False)

def required_login(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash('الرجاء تسجيل الدخول للوصول إلى هذه الصفحة.', 'danger')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

# --- قوالب HTML كمتغيرات (Styles & Structure) ---

BASE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
    <title>{% block title %}تطبيق الملاحظات{% endblock %}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        body { 
            font-family: 'Cairo', sans-serif; 
            background: linear-gradient(to right, #eceff1, #cfd8dc); 
            margin: 0; 
            padding: 0; 
            color: #333;
            min-height: 100vh;
            display: flex; 
            flex-direction: column;
        }
        .container { 
            width: 95%; 
            max-width: 1200px; 
            margin: 20px auto; 
            flex-grow: 1; 
            background: white; 
            padding: 25px 35px; 
            border-radius: 12px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1); 
            border-top: 5px solid #4a90e2; 
        }
        
        /* شريط التنقل */
        .nav { 
            background: #2c3e50; 
            color: white; 
            padding: 10px 0; 
            overflow: hidden; 
            border-radius: 8px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 25px;
            flex-wrap: wrap; 
        }
        .nav-left, .nav-right {
            display: flex;
            align-items: center;
        }
        .nav-left a, .nav-right a {
            color: white; 
            text-align: center; 
            padding: 14px 18px; 
            text-decoration: none; 
            transition: background-color 0.3s, color 0.3s;
            font-weight: bold;
        }
        .nav-left a:hover { 
            background-color: #34495e; 
            color: #ecf0f1; 
            border-radius: 8px;
        }
        .nav .user-info { 
            padding: 14px 16px; 
            color: #ecf0f1; 
            font-weight: bold; 
            display: flex;
            align-items: center;
        }
        .nav .user-info i {
            margin-left: 8px; 
            color: #4a90e2;
        }
        .nav .logout-btn { 
            background-color: #e74c3c; 
            color: white;
            border-radius: 8px; 
            margin: 8px 15px 8px 0; 
            padding: 8px 15px; 
            text-decoration: none;
            transition: background-color 0.3s;
            font-weight: bold;
        }
        .nav .logout-btn:hover { 
            background-color: #c0392b; 
        }
        /* تعديلات لـ Responsive */
        @media (max-width: 768px) {
            .nav {
                flex-direction: column;
                align-items: stretch;
            }
            .nav-left, .nav-right {
                flex-direction: column;
                width: 100%;
                margin-top: 5px;
            }
            .nav-left a, .nav-right a, .nav .user-info, .nav .logout-btn {
                width: 100%;
                text-align: center;
                margin: 0;
                padding: 10px;
                border-radius: 0;
            }
            .nav .logout-btn {
                border-radius: 0 0 8px 8px; 
            }
            .nav-left a:first-child {
                 border-radius: 8px 8px 0 0; 
            }
        }

        /* رسائل Flash */
        .flash { 
            padding: 12px; 
            margin-bottom: 20px; 
            border-radius: 8px; 
            font-weight: bold; 
            text-align: right; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); 
            display: flex;
            align-items: center;
        }
        .flash i {
            margin-left: 10px;
            font-size: 1.2em;
        }
        .success { background-color: #e6ffed; color: #1a6d2c; border: 1px solid #b3e6c3; }
        .success i { color: #28a745; }
        .danger { background-color: #ffe6e6; color: #a32a2a; border: 1px solid #e6b3b3; }
        .danger i { color: #dc3545; }
        .info { background-color: #e6f7ff; color: #1a6d91; border: 1px solid #b3e0ff; }
        .info i { color: #007bff; }
        
        h1 { 
            color: #4a90e2; 
            border-bottom: 2px solid #e0e0e0; 
            padding-bottom: 15px; 
            margin-bottom: 25px;
            text-align: right; 
            font-size: 2em; 
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: flex-end; 
        }
        h1 i {
            margin-right: 15px; 
            color: #2c3e50;
        }
        
        /* تصميم النماذج */
        input[type="text"], input[type="password"], textarea { 
            width: 100%; 
            padding: 12px; 
            margin-bottom: 18px; 
            border: 1px solid #cfd8dc; 
            border-radius: 8px; 
            box-sizing: border-box; 
            text-align: right;
            font-family: 'Cairo', sans-serif;
            font-size: 1em;
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        input[type="text"]:focus, input[type="password"]:focus, textarea:focus {
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
            outline: none;
        }
        label { 
            display: block; 
            text-align: right; 
            margin-bottom: 8px; 
            font-weight: bold; 
            color: #555;
            font-size: 1.1em;
        }
        button[type="submit"] { 
            background-color: #4a90e2; 
            color: white; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 1.1em; 
            transition: background-color 0.3s, transform 0.2s; 
            float: right;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        button[type="submit"]:hover { 
            background-color: #3a7bd2; 
            transform: translateY(-2px); 
        }
        
        /* تصميم بطاقات الملاحظات */
        .notes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
            gap: 25px; 
            margin-top: 30px;
        }
        .note-card { 
            background: #fdfdfd; 
            padding: 20px; 
            border-radius: 10px; 
            border-right: 6px solid #4a90e2; 
            box-shadow: 0 6px 18px rgba(0,0,0,0.08); 
            text-align: right;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        .note-card:hover {
            transform: translateY(-5px); 
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        .note-card h2 { 
            margin-top: 0; 
            color: #2c3e50; 
            font-size: 1.5em; 
            margin-bottom: 10px;
        }
        .note-card p {
            color: #555;
            line-height: 1.7; 
            margin-bottom: 15px;
        }
        .note-card small {
            color: #7f8c8d;
            font-size: 0.9em;
            display: block; 
            margin-top: 10px;
        }

        .no-notes-message {
            font-size: 1.2em; 
            text-align: center; 
            padding: 30px; 
            border: 2px dashed #b0c4de; 
            border-radius: 10px; 
            background-color: #f8faff;
            color: #666;
            margin-top: 30px;
        }
        .no-notes-message a {
            color: #4a90e2;
            text-decoration: none;
            font-weight: bold;
            transition: color 0.3s;
        }
        .no-notes-message a:hover {
            color: #3a7bd2;
            text-decoration: underline;
        }

        .clearfix::after { content: ""; clear: both; display: table; }

        /* تعديلات لصفحة تسجيل الدخول */
        .login-form-container {
            max-width: 450px; 
            margin: 30px auto; 
            padding: 35px; 
            border: 1px solid #e0e0e0; 
            border-radius: 12px; 
            box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            background-color: #fdfdfd;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <div class="nav-left">
                <a href="{{ url_for('index') }}"><i class="fas fa-home"></i> الرئيسية</a>
                {% if session.get('logged_in') %}
                    <a href="{{ url_for('add_note') }}"><i class="fas fa-plus-circle"></i> إضافة ملاحظة</a>
                {% endif %}
            </div>
            <div class="nav-right">
                {% if session.get('logged_in') %}
                    <span class="user-info"><i class="fas fa-user-circle"></i> المستخدم: {{ session.get('username') }}</span>
                    <a href="{{ url_for('logout') }}" class="logout-btn"><i class="fas fa-sign-out-alt"></i> تسجيل الخروج</a>
                {% else %}
                    <a href="{{ url_for('login') }}" class="logout-btn" style="background-color: #4a90e2;"><i class="fas fa-sign-in-alt"></i> تسجيل الدخول</a>
                {% endif %}
            </div>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">
                        {% if category == 'success' %}<i class="fas fa-check-circle"></i>{% endif %}
                        {% if category == 'danger' %}<i class="fas fa-exclamation-triangle"></i>{% endif %}
                        {% if category == 'info' %}<i class="fas fa-info-circle"></i>{% endif %}
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
        <div class="clearfix"></div>
    </div>
</body>
</html>
"""

LOGIN_CONTENT = """
{% extends "base.html" %}
{% block title %}تسجيل الدخول{% endblock %}
{% block content %}
    <h1 style="text-align: center;"><i class="fas fa-user-lock"></i> تسجيل الدخول إلى تطبيق الملاحظات</h1>
    <form method="POST" action="{{ url_for('login') }}" class="login-form-container">
        <label for="username">اسم المستخدم:</label>
        <input type="text" id="username" name="username" required placeholder="izuko"><br>
        
        <label for="password">كلمة المرور:</label>
        <input type="password" id="password" name="password" required placeholder="izuko12345"><br>
        
        <button type="submit" style="width: 100%;">تسجيل الدخول</button>
    </form>
{% endblock %}
"""

INDEX_CONTENT = """
{% extends "base.html" %}
{% block title %}ملاحظاتي{% endblock %}
{% block content %}
    <h1><i class="fas fa-book-open"></i> ملاحظاتي الحالية</h1>
    {% if notes %}
        <div class="notes-grid">
            {% for note in notes %}
                <div class="note-card">
                    <h2>{{ note.title }}</h2>
                    <p>{{ note.content }}</p>
                    <small style="color: #7f8c8d;">تمت الإضافة بواسطة: **{{ note.author }}**</small>
                </div>
            {% endfor %}
        </div>
    {% else %}
        <p class="no-notes-message">لا توجد ملاحظات حاليًا. <a href="{{ url_for('add_note') }}">اضغط هنا لإضافة ملاحظة جديدة!</a></p>
    {% endif %}
{% endblock %}
"""

ADD_NOTE_CONTENT = """
{% extends "base.html" %}
{% block title %}إضافة ملاحظة{% endblock %}
{% block content %}
    <h1><i class="fas fa-edit"></i> إضافة ملاحظة جديدة</h1>
    <form method="POST" action="{{ url_for('add_note') }}">
        <label for="title">عنوان الملاحظة:</label>
        <input type="text" id="title" name="title" required placeholder="اكتب العنوان هنا"><br>
        
        <label for="content">محتوى الملاحظة:</label>
        <textarea id="content" name="content" required rows="7" placeholder="اكتب محتوى الملاحظة..." style="resize: vertical;"></textarea><br>
        
        <button type="submit">حفظ الملاحظة</button>
    </form>
{% endblock %}
"""

# 2. إنشاء محمل (Loader) للقوالب المدمجة
app.jinja_loader = DictLoader({
    'base.html': BASE_HTML,
    'login.html': LOGIN_CONTENT,
    'index.html': INDEX_CONTENT,
    'add_note.html': ADD_NOTE_CONTENT,
})

# --- المسارات (Routes) ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == AUTHORIZED_USER['username'] and \
           check_password_hash(AUTHORIZED_USER['password_hash'], password):
            
            session['logged_in'] = True
            session['username'] = username
            flash('تم تسجيل الدخول بنجاح! مرحباً بك يا izuko.', 'success')
            return redirect(url_for('index'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'danger')
    
    return render_template('login.html') 


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('تم تسجيل الخروج بنجاح.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@required_login 
def index():
    return render_template('index.html', notes=notes)


@app.route('/add_note', methods=['GET', 'POST'])
@required_login
def add_note():
    global notes  # الإشارة إلى القائمة العالمية

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            # 1. إضافة الملاحظة إلى القائمة في الذاكرة
            notes.append({'title': title, 'content': content, 'author': session['username']})
            
            # 2. حفظ القائمة المحدثة إلى ملف JSON
            save_notes(notes) 
            
            flash('تم إضافة الملاحظة بنجاح!', 'success')
            return redirect(url_for('index'))
        else:
            flash('الرجاء تعبئة جميع الحقول.', 'danger')
    
    return render_template('add_note.html')

# --- تشغيل التطبيق ---
if __name__ == '__main__':
    # تأكد من تثبيت: pip install Flask Werkzeug bcrypt
    app.run(debug=True)
