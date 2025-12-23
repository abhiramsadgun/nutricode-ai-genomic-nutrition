from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, DNASample, ReportAnalysis
from ai.pdf_analyzer import extract_text_from_pdf
from ai.diet_engine import infer_condition_from_text, diet_for_condition
from ai.health_rules import triage_reply, DISCLAIMER
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.cli.command("db-init")
def db_init():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="admin@example.com").first():
            u = User(name="Admin", email="admin@example.com", password_hash=generate_password_hash("Pass@123"))
            db.session.add(u)
            db.session.commit()
            print("Created default user: admin@example.com / Pass@123")
        print("DB ready.")

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password") or ""
        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        elif phone:
            user = User.query.filter_by(phone=phone).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        password = request.form.get("password")
        if not password:
            flash("Password required", "error")
            return redirect(url_for("register"))
        if email and User.query.filter_by(email=email).first():
            flash("Email already in use", "error")
            return redirect(url_for("register"))
        if phone and User.query.filter_by(phone=phone).first():
            flash("Phone already in use", "error")
            return redirect(url_for("register"))
        u = User(name=name, email=email, phone=phone, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        flash("Account created. Please login.", "ok")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/dna-portal", methods=["GET","POST"])
@login_required
def dna_portal():
    plan = None
    inferred = None
    if request.method == "POST":
        sample_id = request.form["sample_id"]
        collection_date = request.form["collection_date"]
        collector_name = request.form["collector_name"]
        sample_type = request.form["sample_type"]
        assumed_text = f"Sample type: {sample_type}. Markers: LDL borderline."
        inferred = infer_condition_from_text(assumed_text)
        plan = diet_for_condition(inferred, sample_type=sample_type, pref="vegetarian")
        sample = DNASample(
            sample_id=sample_id,
            collection_date=collection_date,
            collector_name=collector_name,
            sample_type=sample_type,
            user_id=current_user.id,
            inferred_condition=inferred,
            diet_json=json.dumps(plan),
        )
        db.session.add(sample)
        db.session.commit()
    return render_template("dna_portal.html", plan=plan, inferred_condition=inferred)

@app.route("/analyze-pdf", methods=["GET","POST"])
@login_required
def analyze_pdf():
    plan = None
    inferred = None
    if request.method == "POST":
        file = request.files.get("pdf")
        if not file:
            flash("Please upload a PDF", "error")
            return redirect(url_for("analyze_pdf"))
        text = extract_text_from_pdf(file)
        inferred = infer_condition_from_text(text or "")
        plan = diet_for_condition(inferred, pref="vegetarian")
        ra = ReportAnalysis(
            filename=file.filename,
            extracted_text=text[:10000],
            inferred_condition=inferred,
            diet_json=json.dumps(plan),
            user_id=current_user.id,
        )
        db.session.add(ra)
        db.session.commit()
    return render_template("analyze_pdf.html", plan=plan, inferred_condition=inferred)

@app.route("/diet")
@login_required
def diet_view():
    ra = ReportAnalysis.query.filter_by(user_id=current_user.id).order_by(ReportAnalysis.id.desc()).first()
    if ra:
        return render_template("diet_view.html", plan=json.loads(ra.diet_json), inferred_condition=ra.inferred_condition)
    ds = DNASample.query.filter_by(user_id=current_user.id).order_by(DNASample.id.desc()).first()
    if ds:
        return render_template("diet_view.html", plan=json.loads(ds.diet_json), inferred_condition=ds.inferred_condition)
    return render_template("diet_view.html", plan=None, inferred_condition=None)

@app.route("/contact-doctor")
@login_required
def contact_doctor():
    return render_template("contact_doctor.html")

@app.route("/register-dna-test")
@login_required
def register_dna_test():
    return render_template("register_dna_test.html")

@app.route("/about-us")
@login_required
def about_us():
    return render_template("about_us.html")

@app.route("/health-chat")
@login_required
def health_chat():
    return render_template("health_chat.html")

@app.route("/api/health-chat", methods=["POST"])
@login_required
def api_health_chat():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": "Please type your symptom or question."})
    reply = triage_reply(msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)
