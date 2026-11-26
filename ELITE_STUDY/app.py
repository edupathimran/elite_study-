import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, jsonify
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "elite-study-portal-key-2026")
app.permanent_session_lifetime = timedelta(days=30)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# 3-4 ghante tak ke high-bitrate lectures ke liye 4 GB limit
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024 * 1024

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "edupath.db")

UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
VIDEO_DIR = os.path.join(UPLOAD_ROOT, "videos")
PDF_DIR = os.path.join(UPLOAD_ROOT, "pdfs")
CAPTION_DIR = os.path.join(UPLOAD_ROOT, "captions")
AVATAR_DIR = os.path.join(UPLOAD_ROOT, "avatars")

for folder in (VIDEO_DIR, PDF_DIR, CAPTION_DIR, AVATAR_DIR):
    os.makedirs(folder, exist_ok=True)

ALLOWED_VIDEOS = {"mp4", "mkv", "webm", "mov", "avi", "m4v"}
ALLOWED_PDFS = {"pdf"}
ALLOWED_CAPTIONS = {"vtt"}
ALLOWED_IMAGES = {"png", "jpg", "jpeg", "webp"}

ADMIN_ID = os.environ.get("EDUPATH_ADMIN_ID", "ELITE")
ADMIN_PASS = os.environ.get("EDUPATH_ADMIN_PASS", "2233")

SYLLABUS_DATA = {
    "english": {
        "name": "English",
        "tag": "Footprints & First Flight • 2 Portals",
        "subportals": [
            {
                "slug": "footprints",
                "title": "Footprints",
                "desc": "Footprints Without Feet supplementary book ke saare chapters",
                "chapters": [
                    "A Triumph of Surgery",
                    "The Thief's Story",
                    "The Midnight Visitor",
                    "A Question of Trust",
                    "Footprints without Feet",
                    "The Making of a Scientist",
                    "The Necklace",
                    "Bholi",
                    "The Book That Saved the Earth"
                ]
            },
            {
                "slug": "first-flight",
                "title": "First Flight",
                "desc": "First Flight main book ke saare prose aur poems chapters",
                "chapters": [
                    "A Letter to God",
                    "Nelson Mandela: Long Walk to Freedom",
                    "Two Stories about Flying",
                    "From the Diary of Anne Frank",
                    "Glimpses of India",
                    "Mijbil the Otter",
                    "Madam Rides the Bus",
                    "The Sermon at Benares",
                    "The Proposal (Play)",
                    "Dust of Snow & Fire and Ice",
                    "A Tiger in the Zoo",
                    "How to Tell Wild Animals & The Ball Poem",
                    "Amanda!",
                    "The Trees & Fog",
                    "The Tale of Custard the Dragon",
                    "For Anne Gregory"
                ]
            }
        ]
    },
    "hindi": {
        "name": "Hindi",
        "tag": "Course A & Course B • Part A & Part B Portals",
        "courses": [
            {
                "slug": "course-a",
                "title": "Course A",
                "desc": "Hindi Course A — Kshitij Bhag-2 (Part A) aur Kritika Bhag-2 (Part B)",
                "subportals": [
                    {
                        "slug": "course-a-kshitij",
                        "title": "Part A — Kshitij Bhag-2",
                        "desc": "Hindi Course A gadya aur kavya khand ke saare chapters",
                        "chapters": [
                            "Surdas ke Pad",
                            "Ram-Lakshman-Parshuram Samvad",
                            "Savaiya aur Kavitt",
                            "Atmakathya",
                            "Utsah aur At Nahi Rahi Hai",
                            "Yah Danturit Muskan aur Fasal",
                            "Chhaya Mat Chhoona",
                            "Kanyadaan",
                            "Sangatkar",
                            "Netaji ka Chashma",
                            "Balgobin Bhagat",
                            "Lakhnavi Andaz",
                            "Ek Kahani Yah Bhi",
                            "Naubatkhane mein Ibadat",
                            "Sanskriti"
                        ]
                    },
                    {
                        "slug": "course-a-kritika",
                        "title": "Part B — Kritika Bhag-2",
                        "desc": "Hindi Course A supplementary book ke saare chapters",
                        "chapters": [
                            "Mata ka Anchal",
                            "Sana-Sana Hath Jodi",
                            "Main Kyon Likhta Hoon"
                        ]
                    }
                ]
            },
            {
                "slug": "course-b",
                "title": "Course B",
                "desc": "Hindi Course B — Sparsh Bhag-2 (Part A) aur Sanchayan Bhag-2 (Part B)",
                "subportals": [
                    {
                        "slug": "course-b-sparsh",
                        "title": "Part A — Sparsh Bhag-2",
                        "desc": "Hindi Course B prose aur poetry ke saare chapters",
                        "chapters": [
                            "Kabir ki Sakhi",
                            "Meera ke Pad",
                            "Manushyata",
                            "Parvat Pradesh mein Pavas",
                            "Top",
                            "Kar Chale Hum Fida",
                            "Aatmtran",
                            "Bade Bhai Sahab",
                            "Diary ka Ek Panna",
                            "Tantara-Vamiro Katha",
                            "Teesri Kasam ke Shilpkar Shailendra",
                            "Ab Kahan Doosre ke Dukh se Dukhi Hone Wale",
                            "Patjhar mein Tooti Pattiyan",
                            "Kartoos"
                        ]
                    },
                    {
                        "slug": "course-b-sanchayan",
                        "title": "Part B — Sanchayan Bhag-2",
                        "desc": "Hindi Course B supplementary book ke saare chapters",
                        "chapters": [
                            "Harihar Kaka",
                            "Sapnon ke Se Din",
                            "Topi Shukla"
                        ]
                    }
                ]
            }
        ],
        "subportals": [
            {
                "slug": "course-a-kshitij",
                "course_slug": "course-a",
                "title": "Course A — Part A (Kshitij Bhag-2)",
                "desc": "Hindi Course A gadya aur kavya khand chapters",
                "chapters": [
                    "Surdas ke Pad",
                    "Ram-Lakshman-Parshuram Samvad",
                    "Savaiya aur Kavitt",
                    "Atmakathya",
                    "Utsah aur At Nahi Rahi Hai",
                    "Yah Danturit Muskan aur Fasal",
                    "Chhaya Mat Chhoona",
                    "Kanyadaan",
                    "Sangatkar",
                    "Netaji ka Chashma",
                    "Balgobin Bhagat",
                    "Lakhnavi Andaz",
                    "Ek Kahani Yah Bhi",
                    "Naubatkhane mein Ibadat",
                    "Sanskriti"
                ]
            },
            {
                "slug": "course-a-kritika",
                "course_slug": "course-a",
                "title": "Course A — Part B (Kritika Bhag-2)",
                "desc": "Hindi Course A supplementary book chapters",
                "chapters": [
                    "Mata ka Anchal",
                    "Sana-Sana Hath Jodi",
                    "Main Kyon Likhta Hoon"
                ]
            },
            {
                "slug": "course-b-sparsh",
                "course_slug": "course-b",
                "title": "Course B — Part A (Sparsh Bhag-2)",
                "desc": "Hindi Course B prose aur poetry chapters",
                "chapters": [
                    "Kabir ki Sakhi",
                    "Meera ke Pad",
                    "Manushyata",
                    "Parvat Pradesh mein Pavas",
                    "Top",
                    "Kar Chale Hum Fida",
                    "Aatmtran",
                    "Bade Bhai Sahab",
                    "Diary ka Ek Panna",
                    "Tantara-Vamiro Katha",
                    "Teesri Kasam ke Shilpkar Shailendra",
                    "Ab Kahan Doosre ke Dukh se Dukhi Hone Wale",
                    "Patjhar mein Tooti Pattiyan",
                    "Kartoos"
                ]
            },
            {
                "slug": "course-b-sanchayan",
                "course_slug": "course-b",
                "title": "Course B — Part B (Sanchayan Bhag-2)",
                "desc": "Hindi Course B supplementary chapters",
                "chapters": [
                    "Harihar Kaka",
                    "Sapnon ke Se Din",
                    "Topi Shukla"
                ]
            }
        ]
    },
    "sst": {
        "name": "SST",
        "tag": "History, Civics, Geography & Economics • 4 Portals",
        "subportals": [
            {
                "slug": "history",
                "title": "History",
                "desc": "India and the Contemporary World-II ke saare chapters",
                "chapters": [
                    "The Rise of Nationalism in Europe",
                    "Nationalism in India",
                    "The Making of a Global World",
                    "The Age of Industrialisation",
                    "Print Culture and the Modern World"
                ]
            },
            {
                "slug": "civics",
                "title": "Civics (Political Science)",
                "desc": "Democratic Politics-II ke saare chapters",
                "chapters": [
                    "Power-sharing",
                    "Federalism",
                    "Gender, Religion and Caste",
                    "Political Parties",
                    "Outcomes of Democracy"
                ]
            },
            {
                "slug": "geography",
                "title": "Geography",
                "desc": "Contemporary India-II ke saare chapters",
                "chapters": [
                    "Resources and Development",
                    "Forest and Wildlife Resources",
                    "Water Resources",
                    "Agriculture",
                    "Minerals and Energy Resources",
                    "Manufacturing Industries",
                    "Lifelines of National Economy"
                ]
            },
            {
                "slug": "economics",
                "title": "Economics",
                "desc": "Understanding Economic Development ke saare chapters",
                "chapters": [
                    "Development",
                    "Sectors of the Indian Economy",
                    "Money and Credit",
                    "Globalisation and the Indian Economy"
                ]
            }
        ]
    },
    "maths": {
        "name": "Maths",
        "tag": "Standard & Basic CBSE",
        "subportals": [
            {
                "slug": "algebra-number",
                "title": "Number System & Algebra",
                "desc": "Real numbers, polynomials, linear equations, quadratic & AP",
                "chapters": [
                    "Real Numbers",
                    "Polynomials",
                    "Pair of Linear Equations in Two Variables",
                    "Quadratic Equations",
                    "Arithmetic Progressions"
                ]
            },
            {
                "slug": "geometry-trig-stats",
                "title": "Geometry, Trigonometry & Mensuration",
                "desc": "Triangles, coordinate geometry, trigonometry, circles, areas & stats",
                "chapters": [
                    "Triangles",
                    "Coordinate Geometry",
                    "Introduction to Trigonometry",
                    "Some Applications of Trigonometry",
                    "Circles",
                    "Areas Related to Circles",
                    "Surface Areas and Volumes",
                    "Statistics",
                    "Probability"
                ]
            }
        ]
    },
    "science": {
        "name": "Science",
        "tag": "Physics, Chemistry & Biology",
        "subportals": [
            {
                "slug": "physics",
                "title": "Physics",
                "desc": "Light reflection-refraction, human eye, electricity & magnetic effects",
                "chapters": [
                    "Light – Reflection and Refraction",
                    "The Human Eye and the Colourful World",
                    "Electricity",
                    "Magnetic Effects of Electric Current"
                ]
            },
            {
                "slug": "chemistry",
                "title": "Chemistry",
                "desc": "Chemical reactions, acids-bases-salts, metals-nonmetals & carbon",
                "chapters": [
                    "Chemical Reactions and Equations",
                    "Acids, Bases and Salts",
                    "Metals and Non-metals",
                    "Carbon and its Compounds"
                ]
            },
            {
                "slug": "biology",
                "title": "Biology",
                "desc": "Life processes, control-coordination, reproduction & heredity",
                "chapters": [
                    "Life Processes",
                    "Control and Coordination",
                    "How do Organisms Reproduce?",
                    "Heredity",
                    "Our Environment"
                ]
            }
        ]
    },
    "sanskrit": {
        "name": "Sanskrit",
        "tag": "Shemushi Bhag-2 & Vyakaran",
        "subportals": [
            {
                "slug": "shemushi-sahitya",
                "title": "Shemushi Bhag-2",
                "desc": "Sanskrit chapters, anuvad aur prashn-uttar",
                "chapters": [
                    "Shuchiparyavaranam",
                    "Buddhir Balavati Sada",
                    "Shishulalanam",
                    "Janani Tulyavatsala",
                    "Subhashitani",
                    "Sauhardam Prakruteh Shobha",
                    "Vichitra Sakshi",
                    "Sukti Mauktikam"
                ]
            },
            {
                "slug": "sanskrit-vyakaran",
                "title": "Vyakaran & Rachna",
                "desc": "Sandhi, samas, pratyay, avyay aur patra",
                "chapters": [
                    "Sandhi & Samas",
                    "Pratyay & Avyay",
                    "Vachya Parivartan & Samay",
                    "Patra Lekhan & Chitravarnan"
                ]
            }
        ]
    },
    "it": {
        "name": "IT (402)",
        "tag": "Information Technology",
        "subportals": [
            {
                "slug": "it-employability-skills",
                "title": "Part A — Employability Skills",
                "desc": "Communication, self-management, ICT, entrepreneurship aur green skills",
                "chapters": [
                    "Communication Skills-II",
                    "Self-Management Skills-II",
                    "ICT Skills-II",
                    "Entrepreneurial Skills-II",
                    "Green Skills-II"
                ]
            },
            {
                "slug": "it-subject-skills",
                "title": "Part B — Digital Doc, Spreadsheet, DBMS & Web",
                "desc": "Writer, Calc, Base (SQL) aur Web Applications",
                "chapters": [
                    "Digital Documentation (Advanced)",
                    "Electronic Spreadsheet (Advanced)",
                    "Database Management System (RDBMS & SQL)",
                    "Maintain Healthy, Safe and Secure Working Environment"
                ]
            }
        ]
    },
    "ai": {
        "name": "AI (417)",
        "tag": "Artificial Intelligence",
        "subportals": [
            {
                "slug": "ai-foundations-cycle",
                "title": "AI Project Cycle & Problem Scoping",
                "desc": "Problem scoping, data, modelling aur evaluation",
                "chapters": [
                    "Revisiting AI Project Cycle & Ethical Frameworks",
                    "Advanced Concepts of Modeling in AI",
                    "Evaluating Models"
                ]
            },
            {
                "slug": "ai-cv-nlp",
                "title": "Computer Vision & NLP",
                "desc": "Computer Vision aur Natural Language Processing",
                "chapters": [
                    "Computer Vision",
                    "Natural Language Processing (NLP)"
                ]
            }
        ]
    }
}


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
    except sqlite3.Error:
        pass
    return conn


def init_db():
    conn = get_db()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                avatar TEXT DEFAULT '',
                is_blocked INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lectures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_key TEXT NOT NULL,
                subportal_slug TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                video_filename TEXT NOT NULL,
                caption_filename TEXT DEFAULT '',
                likes_count INTEGER DEFAULT 0,
                unlikes_count INTEGER DEFAULT 0,
                views_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lecture_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lecture_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                UNIQUE(user_id, lecture_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lecture_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lecture_id INTEGER NOT NULL,
                viewed_at TEXT NOT NULL,
                UNIQUE(user_id, lecture_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_lectures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                lecture_id INTEGER NOT NULL,
                UNIQUE(user_id, lecture_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pdfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_key TEXT NOT NULL,
                subportal_slug TEXT NOT NULL,
                chapter_name TEXT NOT NULL,
                title TEXT NOT NULL,
                pdf_filename TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lecture_id INTEGER NOT NULL,
                user_id INTEGER DEFAULT NULL,
                parent_id INTEGER DEFAULT NULL,
                author_name TEXT NOT NULL,
                author_avatar TEXT DEFAULT '',
                is_admin INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                comment_text TEXT NOT NULL,
                likes_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (lecture_id) REFERENCES lectures(id) ON DELETE CASCADE
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                link_url TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        user_cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "is_blocked" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
        if "avatar" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT ''")

        lec_cols = [r[1] for r in cur.execute("PRAGMA table_info(lectures)").fetchall()]
        if "caption_filename" not in lec_cols:
            cur.execute("ALTER TABLE lectures ADD COLUMN caption_filename TEXT DEFAULT ''")
        if "unlikes_count" not in lec_cols:
            cur.execute("ALTER TABLE lectures ADD COLUMN unlikes_count INTEGER DEFAULT 0")
        if "views_count" not in lec_cols:
            cur.execute("ALTER TABLE lectures ADD COLUMN views_count INTEGER DEFAULT 0")

        cmt_cols = [r[1] for r in cur.execute("PRAGMA table_info(comments)").fetchall()]
        if "user_id" not in cmt_cols:
            cur.execute("ALTER TABLE comments ADD COLUMN user_id INTEGER DEFAULT NULL")
        if "parent_id" not in cmt_cols:
            cur.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL")
        if "is_pinned" not in cmt_cols:
            cur.execute("ALTER TABLE comments ADD COLUMN is_pinned INTEGER DEFAULT 0")

        if cur.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO notifications (title, message, link_url, created_at) VALUES (?, ?, ?, ?)",
                (
                    "ELITE STUDY Ready",
                    "Footprints, First Flight, Hindi Course A/B (Part A & B) aur SST ke 4 portals active hain.",
                    "/dashboard",
                    datetime.now().strftime("%d %b, %I:%M %p")
                )
            )

        conn.commit()
    finally:
        conn.close()


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


def get_current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    try:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        return dict(user) if user else None
    finally:
        conn.close()


@app.before_request
def keep_session_persistent():
    if session.get("user_id") or session.get("is_admin"):
        session.permanent = True


def require_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for("entry"))
        if user.get("is_blocked"):
            session.pop("user_id", None)
            flash("Aapka account admin dwara block kar diya gaya hai.", "error")
            return redirect(url_for("entry"))
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin access ke liye sahi ID aur Password zaroori hai.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated


@app.context_processor
def inject_globals():
    user = get_current_user()
    conn = get_db()
    try:
        notices = [
            dict(row) for row in conn.execute(
                "SELECT * FROM notifications ORDER BY id DESC LIMIT 15"
            ).fetchall()
        ]
        saved_ids = []
        if user:
            saved_ids = [
                r["lecture_id"] for r in conn.execute(
                    "SELECT lecture_id FROM saved_lectures WHERE user_id = ?", (user["id"],)
                ).fetchall()
            ]
    finally:
        conn.close()
    return {
        "current_user": user,
        "is_admin": bool(session.get("is_admin")),
        "notifications": notices,
        "saved_lecture_ids": saved_ids,
        "syllabus_data": SYLLABUS_DATA
    }


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def entry():
    user = get_current_user()
    if user and not user.get("is_blocked"):
        session.permanent = True
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Aapka naam daalna zaroori hai.", "error")
            return render_template("entry.html")

        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT * FROM users WHERE LOWER(name) = LOWER(?) ORDER BY id DESC LIMIT 1",
                (name,)
            ).fetchone()

            if existing and existing["is_blocked"]:
                flash("Is naam ka account admin dwara block kiya gaya hai.", "error")
                return render_template("entry.html")

            if existing and not existing["is_blocked"]:
                user_id = existing["id"]
            else:
                now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (name, avatar, is_blocked, created_at) VALUES (?, '', 0, ?)",
                    (name, now_str)
                )
                user_id = cur.lastrowid
                conn.commit()
        finally:
            conn.close()

        session.permanent = True
        session["user_id"] = user_id
        session["user_name"] = name
        flash(f"Swagat hai, {name}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("entry.html")


@app.route("/dashboard")
@require_user
def dashboard():
    user = get_current_user()
    query = (request.args.get("q") or "").strip()
    conn = get_db()
    try:
        total_lectures = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
        total_pdfs = conn.execute("SELECT COUNT(*) FROM pdfs").fetchone()[0]
        total_students = conn.execute("SELECT COUNT(*) FROM users WHERE is_blocked = 0").fetchone()[0]

        saved_list = [
            dict(r) for r in conn.execute(
                """
                SELECT l.* FROM lectures l
                INNER JOIN saved_lectures s ON s.lecture_id = l.id
                WHERE s.user_id = ?
                ORDER BY s.id DESC
                """,
                (user["id"],)
            ).fetchall()
        ]

        search_lectures = []
        search_pdfs = []
        if query:
            like_q = f"%{query}%"
            search_lectures = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM lectures WHERE title LIKE ? OR chapter_name LIKE ? ORDER BY id DESC",
                    (like_q, like_q)
                ).fetchall()
            ]
            search_pdfs = [
                dict(r) for r in conn.execute(
                    "SELECT * FROM pdfs WHERE title LIKE ? OR chapter_name LIKE ? ORDER BY id DESC",
                    (like_q, like_q)
                ).fetchall()
            ]
    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        total_lectures=total_lectures,
        total_pdfs=total_pdfs,
        total_students=total_students,
        saved_list=saved_list,
        search_query=query,
        search_lectures=search_lectures,
        search_pdfs=search_pdfs
    )


@app.route("/profile/update", methods=["POST"])
@require_user
def update_profile():
    user = get_current_user()
    new_name = (request.form.get("name") or user["name"]).strip() or user["name"]
    avatar_filename = user.get("avatar") or ""

    file = request.files.get("avatar")
    if file and file.filename:
        if allowed_file(file.filename, ALLOWED_IMAGES):
            safe_name = f"u{user['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            file.save(os.path.join(AVATAR_DIR, safe_name))
            avatar_filename = safe_name
        else:
            flash("Sirf PNG, JPG, JPEG ya WEBP logo/photo upload karein.", "error")
            return redirect(request.referrer or url_for("dashboard"))

    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET name = ?, avatar = ? WHERE id = ?",
            (new_name, avatar_filename, user["id"])
        )
        conn.execute(
            "UPDATE comments SET author_avatar = ? WHERE user_id = ?",
            (avatar_filename, user["id"])
        )
        conn.commit()
    finally:
        conn.close()

    session["user_name"] = new_name
    flash("Profile aur logo update ho gaye hain.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/admin/login", methods=["GET", "POST"])
@require_user
def admin_login():
    if session.get("is_admin"):
        session.permanent = True
        return redirect(url_for("admin_panel"))

    if request.method == "POST":
        admin_id = (request.form.get("admin_id") or "").strip()
        admin_pass = (request.form.get("admin_pass") or "").strip()

        if admin_id == ADMIN_ID and admin_pass == ADMIN_PASS:
            session.permanent = True
            session["is_admin"] = True
            session.modified = True
            flash("Admin login save ho gaya hai — ab baar-baar login nahi karna padega.", "success")
            return redirect(url_for("admin_panel"))

        flash("Invalid Admin ID ya Password.", "error")
        return redirect(request.referrer or url_for("dashboard"))

    return redirect(url_for("dashboard"))


@app.route("/admin/logout")
@require_user
def admin_logout():
    session.pop("is_admin", None)
    flash("Admin session band kar diya gaya hai.", "info")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("entry"))


@app.route("/subject/<subject_key>")
@require_user
def subject_view(subject_key):
    subject = SYLLABUS_DATA.get(subject_key)
    if not subject:
        return redirect(url_for("dashboard"))

    selected_course = None
    if subject.get("courses"):
        course_slug = (request.args.get("course") or "").strip()
        if course_slug:
            selected_course = next(
                (c for c in subject["courses"] if c["slug"] == course_slug),
                None
            )

    selected_portal = None
    portal_slug = (request.args.get("portal") or "").strip()
    if portal_slug:
        pool = selected_course["subportals"] if selected_course else subject["subportals"]
        selected_portal = next((sp for sp in pool if sp["slug"] == portal_slug), None)

    conn = get_db()
    try:
        lecture_counts = {}
        pdf_counts = {}
        for row in conn.execute(
            "SELECT subportal_slug, chapter_name, COUNT(*) as cnt FROM lectures WHERE subject_key = ? GROUP BY subportal_slug, chapter_name",
            (subject_key,)
        ).fetchall():
            lecture_counts[(row["subportal_slug"], row["chapter_name"])] = row["cnt"]

        for row in conn.execute(
            "SELECT subportal_slug, chapter_name, COUNT(*) as cnt FROM pdfs WHERE subject_key = ? GROUP BY subportal_slug, chapter_name",
            (subject_key,)
        ).fetchall():
            pdf_counts[(row["subportal_slug"], row["chapter_name"])] = row["cnt"]
    finally:
        conn.close()

    return render_template(
        "subject.html",
        subject_key=subject_key,
        subject=subject,
        selected_course=selected_course,
        selected_portal=selected_portal,
        lecture_counts=lecture_counts,
        pdf_counts=pdf_counts
    )


@app.route("/chapter/<subject_key>/<subportal_slug>")
@require_user
def chapter_view(subject_key, subportal_slug):
    user = get_current_user()
    subject = SYLLABUS_DATA.get(subject_key)
    if not subject:
        return redirect(url_for("dashboard"))

    subportal = next(
        (sp for sp in subject["subportals"] if sp["slug"] == subportal_slug),
        None
    )
    if not subportal:
        return redirect(url_for("subject_view", subject_key=subject_key))

    selected_chapter = request.args.get("chapter") or subportal["chapters"][0]
    if selected_chapter not in subportal["chapters"]:
        selected_chapter = subportal["chapters"][0]
    active_lecture_id = request.args.get("lecture_id", type=int)

    conn = get_db()
    try:
        lectures = [
            dict(r) for r in conn.execute(
                """
                SELECT * FROM lectures
                WHERE subject_key = ? AND subportal_slug = ? AND chapter_name = ?
                ORDER BY id ASC
                """,
                (subject_key, subportal_slug, selected_chapter)
            ).fetchall()
        ]

        pdfs = [
            dict(r) for r in conn.execute(
                """
                SELECT * FROM pdfs
                WHERE subject_key = ? AND subportal_slug = ? AND chapter_name = ?
                ORDER BY id DESC
                """,
                (subject_key, subportal_slug, selected_chapter)
            ).fetchall()
        ]

        active_lecture = None
        if lectures:
            if active_lecture_id:
                active_lecture = next((l for l in lectures if l["id"] == active_lecture_id), lectures[0])
            else:
                active_lecture = lectures[0]

        user_reaction = None
        comments_tree = []
        if active_lecture:
            rx = conn.execute(
                "SELECT reaction FROM lecture_reactions WHERE user_id = ? AND lecture_id = ?",
                (user["id"], active_lecture["id"])
            ).fetchone()
            if rx:
                user_reaction = rx["reaction"]

            all_comments = [
                dict(c) for c in conn.execute(
                    """
                    SELECT c.*, COALESCE(u.avatar, c.author_avatar) AS live_avatar
                    FROM comments c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.lecture_id = ?
                    ORDER BY c.is_pinned DESC, c.id DESC
                    """,
                    (active_lecture["id"],)
                ).fetchall()
            ]
            replies_by_parent = {}
            top_comments = []
            for c in all_comments:
                c["author_avatar"] = c.get("live_avatar") or c.get("author_avatar") or ""
                pid = c.get("parent_id")
                if pid:
                    replies_by_parent.setdefault(pid, []).append(c)
                else:
                    top_comments.append(c)

            for tc in top_comments:
                tc["replies"] = sorted(replies_by_parent.get(tc["id"], []), key=lambda x: x["id"])
                comments_tree.append(tc)
    finally:
        conn.close()

    return render_template(
        "chapter.html",
        subject_key=subject_key,
        subject=subject,
        subportal=subportal,
        selected_chapter=selected_chapter,
        lectures=lectures,
        pdfs=pdfs,
        active_lecture=active_lecture,
        user_reaction=user_reaction,
        comments=comments_tree
    )


@app.route("/api/lecture/<int:lecture_id>/view", methods=["POST"])
@require_user
def record_unique_view(lecture_id):
    user = get_current_user()
    conn = get_db()
    try:
        lec = conn.execute("SELECT id, views_count FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
        if not lec:
            return jsonify({"error": "Not found"}), 404

        now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO lecture_views (user_id, lecture_id, viewed_at) VALUES (?, ?, ?)",
            (user["id"], lecture_id, now_str)
        )
        counted = cur.rowcount > 0
        if counted:
            conn.execute("UPDATE lectures SET views_count = views_count + 1 WHERE id = ?", (lecture_id,))
        conn.commit()
        updated = conn.execute("SELECT views_count FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
        return jsonify({"views": updated["views_count"], "counted": counted})
    finally:
        conn.close()


@app.route("/api/lecture/<int:lecture_id>/react", methods=["POST"])
@require_user
def react_lecture(lecture_id):
    user = get_current_user()
    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("like", "unlike"):
        return jsonify({"error": "Invalid action"}), 400

    conn = get_db()
    try:
        lec = conn.execute("SELECT id FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
        if not lec:
            return jsonify({"error": "Not found"}), 404

        prev = conn.execute(
            "SELECT reaction FROM lecture_reactions WHERE user_id = ? AND lecture_id = ?",
            (user["id"], lecture_id)
        ).fetchone()
        prev_rx = prev["reaction"] if prev else None

        if prev_rx == action:
            conn.execute(
                "DELETE FROM lecture_reactions WHERE user_id = ? AND lecture_id = ?",
                (user["id"], lecture_id)
            )
            active_rx = None
        else:
            conn.execute(
                """
                INSERT INTO lecture_reactions (user_id, lecture_id, reaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, lecture_id) DO UPDATE SET reaction = excluded.reaction
                """,
                (user["id"], lecture_id, action)
            )
            active_rx = action

        likes_total = conn.execute(
            "SELECT COUNT(*) FROM lecture_reactions WHERE lecture_id = ? AND reaction = 'like'",
            (lecture_id,)
        ).fetchone()[0]
        unlikes_total = conn.execute(
            "SELECT COUNT(*) FROM lecture_reactions WHERE lecture_id = ? AND reaction = 'unlike'",
            (lecture_id,)
        ).fetchone()[0]

        conn.execute(
            "UPDATE lectures SET likes_count = ?, unlikes_count = ? WHERE id = ?",
            (likes_total, unlikes_total, lecture_id)
        )
        conn.commit()
        return jsonify({
            "likes": likes_total,
            "unlikes": unlikes_total,
            "reaction": active_rx
        })
    finally:
        conn.close()


@app.route("/api/lecture/<int:lecture_id>/comment", methods=["POST"])
@require_user
def add_comment(lecture_id):
    user = get_current_user()
    data = request.get_json(silent=True) or request.form
    text = (data.get("comment_text") or "").strip()
    parent_id = data.get("parent_id")
    try:
        parent_id = int(parent_id) if parent_id not in (None, "", "null") else None
    except (TypeError, ValueError):
        parent_id = None

    if not text:
        return jsonify({"error": "Comment khali nahi ho sakta"}), 400

    is_adm = 1 if session.get("is_admin") else 0
    author_name = "Admin • " + user["name"] if is_adm else user["name"]
    now_str = datetime.now().strftime("%d %b, %I:%M %p")

    conn = get_db()
    try:
        if parent_id is not None:
            parent_row = conn.execute(
                "SELECT id, parent_id FROM comments WHERE id = ? AND lecture_id = ?",
                (parent_id, lecture_id)
            ).fetchone()
            if not parent_row:
                return jsonify({"error": "Parent comment nahi mila"}), 404
            if parent_row["parent_id"]:
                parent_id = parent_row["parent_id"]

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO comments (lecture_id, user_id, parent_id, author_name, author_avatar, is_admin, is_pinned, comment_text, likes_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, 0, ?)
            """,
            (lecture_id, user["id"], parent_id, author_name, user.get("avatar", ""), is_adm, text, now_str)
        )
        cid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "id": cid,
        "parent_id": parent_id,
        "author_name": author_name,
        "author_avatar": user.get("avatar", ""),
        "is_admin": is_adm,
        "is_pinned": 0,
        "comment_text": text,
        "likes_count": 0,
        "created_at": now_str
    })


@app.route("/admin/comment/<int:comment_id>/pin", methods=["POST"])
@require_user
@require_admin
def pin_comment(comment_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT id, lecture_id, is_pinned FROM comments WHERE id = ?", (comment_id,)).fetchone()
        if row:
            new_pin = 0 if row["is_pinned"] else 1
            if new_pin == 1:
                conn.execute("UPDATE comments SET is_pinned = 0 WHERE lecture_id = ?", (row["lecture_id"],))
            conn.execute("UPDATE comments SET is_pinned = ? WHERE id = ?", (new_pin, comment_id))
            conn.commit()
            flash("Comment pin kar diya gaya." if new_pin == 1 else "Comment unpin kar diya gaya.", "success")
    finally:
        conn.close()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/admin/comment/<int:comment_id>/delete", methods=["POST"])
@require_user
@require_admin
def delete_comment(comment_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM comments WHERE parent_id = ?", (comment_id,))
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
        flash("Comment delete kar diya gaya.", "info")
    finally:
        conn.close()
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/admin", methods=["GET", "POST"])
@require_user
@require_admin
def admin_panel():
    conn = get_db()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        if request.method == "POST":
            form_type = request.form.get("form_type")
            now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

            if form_type == "upload_lecture":
                subject_key = request.form.get("subject_key", "")
                subportal_slug = request.form.get("subportal_slug", "")
                chapter_name = request.form.get("chapter_name", "").strip()
                title = (request.form.get("title") or "").strip()
                description = (request.form.get("description") or "").strip()
                video_file = request.files.get("video_file")
                caption_file = request.files.get("caption_file")

                err = None
                if not title or not video_file or not video_file.filename:
                    err = "Lecture title aur video file dono zaroori hain."
                elif not allowed_file(video_file.filename, ALLOWED_VIDEOS):
                    err = "Supported video formats: MP4, MKV, WEBM, MOV, AVI, M4V."

                if err:
                    if is_ajax:
                        return jsonify({"ok": False, "message": err}), 400
                    flash(err, "error")
                else:
                    safe_vid = f"lec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(video_file.filename)}"
                    video_file.save(os.path.join(VIDEO_DIR, safe_vid))

                    safe_cap = ""
                    if caption_file and caption_file.filename and allowed_file(caption_file.filename, ALLOWED_CAPTIONS):
                        safe_cap = f"cap_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(caption_file.filename)}"
                        caption_file.save(os.path.join(CAPTION_DIR, safe_cap))

                    conn.execute(
                        """
                        INSERT INTO lectures
                        (subject_key, subportal_slug, chapter_name, title, description, video_filename, caption_filename, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (subject_key, subportal_slug, chapter_name, title, description, safe_vid, safe_cap, now_str)
                    )
                    link = url_for("chapter_view", subject_key=subject_key, subportal_slug=subportal_slug, chapter=chapter_name)
                    conn.execute(
                        "INSERT INTO notifications (title, message, link_url, created_at) VALUES (?, ?, ?, ?)",
                        (f"New Lecture: {title}", f"{chapter_name} mein naya lecture upload hua hai.", link, now_str)
                    )
                    conn.commit()
                    if is_ajax:
                        return jsonify({"ok": True, "message": "Lecture successfully upload ho gaya!", "redirect": url_for("admin_panel")})
                    flash("Lecture successfully upload ho gaya!", "success")

            elif form_type == "upload_pdf":
                subject_key = request.form.get("subject_key", "")
                subportal_slug = request.form.get("subportal_slug", "")
                chapter_name = request.form.get("chapter_name", "").strip()
                title = (request.form.get("title") or "").strip()
                pdf_file = request.files.get("pdf_file")

                err = None
                if not title or not pdf_file or not pdf_file.filename:
                    err = "PDF title aur PDF file zaroori hai."
                elif not allowed_file(pdf_file.filename, ALLOWED_PDFS):
                    err = "Sirf valid .PDF file upload karein."

                if err:
                    if is_ajax:
                        return jsonify({"ok": False, "message": err}), 400
                    flash(err, "error")
                else:
                    safe_pdf = f"pdf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(pdf_file.filename)}"
                    pdf_file.save(os.path.join(PDF_DIR, safe_pdf))

                    conn.execute(
                        """
                        INSERT INTO pdfs (subject_key, subportal_slug, chapter_name, title, pdf_filename, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (subject_key, subportal_slug, chapter_name, title, safe_pdf, now_str)
                    )
                    link = url_for("chapter_view", subject_key=subject_key, subportal_slug=subportal_slug, chapter=chapter_name)
                    conn.execute(
                        "INSERT INTO notifications (title, message, link_url, created_at) VALUES (?, ?, ?, ?)",
                        (f"New PDF: {title}", f"{chapter_name} ka PDF note upload ho gaya hai.", link, now_str)
                    )
                    conn.commit()
                    if is_ajax:
                        return jsonify({"ok": True, "message": "PDF note successfully upload ho gaya!", "redirect": url_for("admin_panel")})
                    flash("PDF note successfully upload ho gaya!", "success")

            elif form_type == "send_notice":
                n_title = (request.form.get("notice_title") or "").strip()
                n_msg = (request.form.get("notice_message") or "").strip()
                if n_title and n_msg:
                    conn.execute(
                        "INSERT INTO notifications (title, message, link_url, created_at) VALUES (?, ?, ?, ?)",
                        (n_title, n_msg, url_for("dashboard"), now_str)
                    )
                    conn.commit()
                    flash("Bell notification bhej diya gaya.", "success")

        users = [dict(u) for u in conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()]
        active_student_count = sum(1 for u in users if not u["is_blocked"])
        lectures = [dict(l) for l in conn.execute("SELECT * FROM lectures ORDER BY id DESC").fetchall()]
        pdfs = [dict(p) for p in conn.execute("SELECT * FROM pdfs ORDER BY id DESC").fetchall()]
    finally:
        conn.close()

    return render_template(
        "admin.html",
        users=users,
        active_student_count=active_student_count,
        lectures=lectures,
        pdfs=pdfs
    )


@app.route("/admin/user/<int:user_id>/toggle-block", methods=["POST"])
@require_user
@require_admin
def toggle_block_user(user_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT is_blocked, name FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            new_state = 0 if row["is_blocked"] else 1
            conn.execute("UPDATE users SET is_blocked = ? WHERE id = ?", (new_state, user_id))
            conn.commit()
            status_text = "block" if new_state == 1 else "unblock"
            flash(f"{row['name']} ko {status_text} kar diya gaya hai.", "info")
    finally:
        conn.close()
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete/lecture/<int:lecture_id>", methods=["POST"])
@require_user
@require_admin
def delete_lecture(lecture_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT video_filename, caption_filename FROM lectures WHERE id = ?", (lecture_id,)).fetchone()
        if row:
            for folder, fname in ((VIDEO_DIR, row["video_filename"]), (CAPTION_DIR, row["caption_filename"])):
                if fname:
                    full_p = os.path.join(folder, fname)
                    if os.path.exists(full_p):
                        os.remove(full_p)
            conn.execute("DELETE FROM lecture_views WHERE lecture_id = ?", (lecture_id,))
            conn.execute("DELETE FROM lecture_reactions WHERE lecture_id = ?", (lecture_id,))
            conn.execute("DELETE FROM saved_lectures WHERE lecture_id = ?", (lecture_id,))
            conn.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
            conn.commit()
            flash("Lecture delete kar diya gaya.", "info")
    finally:
        conn.close()
    return redirect(url_for("admin_panel"))


@app.route("/admin/delete/pdf/<int:pdf_id>", methods=["POST"])
@require_user
@require_admin
def delete_pdf(pdf_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT pdf_filename FROM pdfs WHERE id = ?", (pdf_id,)).fetchone()
        if row:
            p_path = os.path.join(PDF_DIR, row["pdf_filename"])
            if os.path.exists(p_path):
                os.remove(p_path)
            conn.execute("DELETE FROM pdfs WHERE id = ?", (pdf_id,))
            conn.commit()
            flash("PDF delete kar diya gaya.", "info")
    finally:
        conn.close()
    return redirect(url_for("admin_panel"))


@app.route("/media/video/<path:filename>")
@require_user
def serve_video(filename):
    safe_name = os.path.basename(filename or "")
    resp = send_from_directory(VIDEO_DIR, safe_name, as_attachment=False, conditional=True)
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@app.route("/media/caption/<path:filename>")
@require_user
def serve_caption(filename):
    safe_name = os.path.basename(filename or "")
    return send_from_directory(CAPTION_DIR, safe_name, mimetype="text/vtt")


@app.route("/media/pdf/<path:filename>")
@require_user
def serve_pdf(filename):
    safe_name = os.path.basename(filename or "")
    resp = send_from_directory(PDF_DIR, safe_name, as_attachment=False)
    resp.headers["Content-Disposition"] = f'inline; filename="{safe_name}"'
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


@app.route("/download/pdf/<path:filename>")
@require_user
def download_pdf(filename):
    safe_name = os.path.basename(filename or "")
    return send_from_directory(PDF_DIR, safe_name, as_attachment=True)


@app.route("/media/avatar/<path:filename>")
def serve_avatar(filename):
    safe_name = os.path.basename(filename or "")
    return send_from_directory(AVATAR_DIR, safe_name)


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)