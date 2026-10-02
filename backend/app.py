import io
import json
import secrets
import smtplib
import uuid
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from openpyxl import Workbook, load_workbook
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

import config
from db import get_db, init_db

app = Flask(__name__)
CORS(app)
init_db()

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def current_user():
    token = request.headers.get("Authorization", "")
    if not token:
        return None
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
    conn.close()
    return row


def send_verification_email(to_addr, code):
    subject = "问卷系统 - 邮箱验证码"
    body = f"你的验证码是：{code}，10 分钟内有效。请勿泄露给他人。"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((config.SMTP_FROM, config.SMTP_USER))
    msg["To"] = to_addr

    server = smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT)
    server.login(config.SMTP_USER, config.SMTP_PASSWORD)
    server.sendmail(config.SMTP_USER, [to_addr], msg.as_string())
    server.quit()


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400

    conn = get_db()
    exists = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if exists:
        conn.close()
        return jsonify({"error": "用户名已存在"}), 400

    token = secrets.token_hex(16)
    conn.execute(
        "INSERT INTO users (username, password_hash, token) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), token),
    )
    conn.commit()
    conn.close()

    return jsonify({"token": token, "username": username})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if row is None or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": "用户名或密码错误"}), 400

    return jsonify({"token": row["token"], "username": row["username"]})


@app.route("/api/me", methods=["GET", "PUT"])
def me():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    if request.method == "PUT":
        data = request.get_json(silent=True) or {}
        conn = get_db()

        username = (data.get("username") or "").strip()
        if username and username != user["username"]:
            exists = conn.execute(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (username, user["id"]),
            ).fetchone()
            if exists:
                conn.close()
                return jsonify({"error": "昵称已被占用"}), 400
            conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, user["id"]))

        avatar = data.get("avatar")
        if avatar is not None:
            conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user["id"]))

        email = data.get("email")
        if email is not None:
            conn.execute("UPDATE users SET email = ? WHERE id = ?", ((email or "").strip(), user["id"]))

        phone = data.get("phone")
        if phone is not None:
            conn.execute("UPDATE users SET phone = ? WHERE id = ?", ((phone or "").strip(), user["id"]))

        new_password = data.get("new_password")
        if new_password:
            old_password = data.get("old_password") or ""
            if not check_password_hash(user["password_hash"], old_password):
                conn.close()
                return jsonify({"error": "旧密码错误"}), 400
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), user["id"]),
            )

        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        conn.close()
        return jsonify({
            "id": row["id"],
            "username": row["username"],
            "avatar": row["avatar"],
            "email": row["email"],
            "phone": row["phone"],
        })

    return jsonify({
        "id": user["id"],
        "username": user["username"],
        "avatar": user["avatar"],
        "email": user["email"],
        "phone": user["phone"],
    })


@app.route("/api/upload", methods=["POST"])
def upload_image():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "未选择文件"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return jsonify({"error": "仅支持图片格式"}), 400

    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(UPLOAD_DIR / filename)
    return jsonify({"url": f"/uploads/{filename}"})


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


EXAM_TEMPLATE_HEADERS = ["题型", "题干", "选项A", "选项B", "选项C", "选项D", "正确答案", "分值"]
EXAM_TEMPLATE_ROWS = [
    ["单选", "星露谷物语中，第一年春季可以种植的作物是？", "防风草", "草莓", "南瓜", "玉米", "A", 5],
    ["多选", "以下哪些是星露谷的节日？", "复活节", "月光水母节", "冬星节", "万圣节", "ABC", 10],
    ["判断", "星露谷中，钓鱼可以在任何季节进行。", "对", "错", "", "", "A", 5],
    ["填空", "星露谷中，冬天举办的大型节日叫____。", "", "", "", "", "冬星节", 5],
]

EXAM_TYPE_MAP = {
    "单选": "single", "单选题": "single",
    "多选": "multiple", "多选题": "multiple",
    "判断": "judge", "判断题": "judge",
    "填空": "fill", "填空题": "fill",
}


@app.route("/api/exam/template", methods=["GET"])
def exam_template():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    wb = Workbook()
    ws = wb.active
    ws.title = "考试试卷"
    ws.append(EXAM_TEMPLATE_HEADERS)
    for row in EXAM_TEMPLATE_ROWS:
        ws.append(row)

    widths = [10, 40, 14, 14, 14, 14, 12, 8]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="考试试卷模板.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/exam/parse", methods=["POST"])
def exam_parse():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "未选择文件"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("xlsx", "xlsm"):
        return jsonify({"error": "仅支持 .xlsx 文件"}), 400

    try:
        wb = load_workbook(file, read_only=True, data_only=True)
    except Exception:
        return jsonify({"error": "文件无法解析，请使用模板格式"}), 400

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return jsonify({"error": "文件为空"}), 400

    header = [str(c).strip() if c is not None else "" for c in rows[0]]

    def col(name):
        return header.index(name) if name in header else -1

    type_col = col("题型")
    title_col = col("题干")
    ans_col = col("正确答案")
    score_col = col("分值")
    opt_cols = [col("选项A"), col("选项B"), col("选项C"), col("选项D")]

    if type_col < 0 or title_col < 0 or ans_col < 0:
        return jsonify({"error": "缺少必要列：题型 / 题干 / 正确答案"}), 400

    questions = []
    warnings = []
    for idx, row in enumerate(rows[1:], start=2):
        if row is None:
            continue
        cells = list(row) + [None] * 8
        type_raw = str(cells[type_col]).strip() if cells[type_col] is not None else ""
        title = str(cells[title_col]).strip() if cells[title_col] is not None else ""
        if not type_raw and not title:
            continue
        if type_raw not in EXAM_TYPE_MAP:
            warnings.append(f"第{idx}行：未知题型「{type_raw}」，已跳过")
            continue
        if not title:
            warnings.append(f"第{idx}行：缺少题干，已跳过")
            continue

        qtype = EXAM_TYPE_MAP[type_raw]

        options = []
        for cidx in opt_cols:
            if cidx < 0:
                continue
            text = str(cells[cidx]).strip() if cells[cidx] is not None else ""
            if text:
                options.append(text)

        answer = str(cells[ans_col]).strip() if cells[ans_col] is not None else ""
        score_val = cells[score_col] if score_col >= 0 else None
        try:
            score = int(score_val) if score_val not in (None, "") else 0
        except (ValueError, TypeError):
            score = 0

        if qtype == "judge":
            letter = answer.upper()
            if letter and letter not in ("A", "B"):
                warnings.append(f"第{idx}行：判断题正确答案应为 A（对）或 B（错）")
                letter = "A"
            correct = letter == "A"
            q = {
                "type": "judge", "title": title, "score": score,
                "options": [
                    {"text": "对", "is_correct": correct},
                    {"text": "错", "is_correct": not correct},
                ],
            }
        elif qtype == "fill":
            ref = str(cells[ans_col]).strip() if cells[ans_col] is not None else ""
            if not ref:
                warnings.append(f"第{idx}行：填空题缺少参考答案")
            q = {"type": "fill", "title": title, "score": score, "answer": ref}
        else:
            if not options:
                warnings.append(f"第{idx}行：缺少选项，已跳过")
                continue
            letters = "".join(ch for ch in answer.upper() if ch in "ABCD")
            correct_set = set(letters)
            if not letters:
                warnings.append(f"第{idx}行：缺少正确答案")
            opt_objs = []
            for oi, text in enumerate(options):
                letter = "ABCD"[oi] if oi < 4 else ""
                opt_objs.append({"text": text, "is_correct": letter in correct_set})
            q = {"type": qtype, "title": title, "score": score, "options": opt_objs}

        questions.append(q)

    if not questions:
        first_warn = warnings[0] if warnings else ""
        return jsonify({"error": "未解析到任何题目" + (f"（{first_warn}）" if first_warn else "")}), 400

    return jsonify({"questions": questions, "warnings": warnings})


@app.route("/api/me/email/send-code", methods=["POST"])
def send_email_code():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        return jsonify({"error": "SMTP 未配置，请在 config.py 中填写邮箱和授权码"}), 500

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "邮箱格式不正确"}), 400

    conn = get_db()
    exists = conn.execute(
        "SELECT id FROM users WHERE email = ? AND id != ?", (email, user["id"])
    ).fetchone()
    if exists:
        conn.close()
        return jsonify({"error": "该邮箱已被绑定"}), 400

    code = f"{secrets.randbelow(1000000):06d}"
    conn.execute("DELETE FROM email_codes WHERE user_id = ?", (user["id"],))
    conn.execute(
        "INSERT INTO email_codes (user_id, email, code, expires_at) "
        "VALUES (?, ?, ?, datetime('now', '+10 minutes'))",
        (user["id"], email, code),
    )
    conn.commit()
    conn.close()

    try:
        send_verification_email(email, code)
    except Exception as e:
        return jsonify({"error": f"邮件发送失败：{e}"}), 500

    return jsonify({"ok": True})


@app.route("/api/me/email/verify", methods=["POST"])
def verify_email_code():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM email_codes WHERE user_id = ? AND email = ? "
        "AND expires_at > datetime('now') ORDER BY id DESC LIMIT 1",
        (user["id"], email),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "验证码已过期，请重新发送"}), 400
    if row["code"] != code:
        conn.close()
        return jsonify({"error": "验证码错误"}), 400

    exists = conn.execute(
        "SELECT id FROM users WHERE email = ? AND id != ?", (email, user["id"])
    ).fetchone()
    if exists:
        conn.close()
        return jsonify({"error": "该邮箱已被绑定"}), 400

    conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user["id"]))
    conn.execute("DELETE FROM email_codes WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()

    return jsonify({"ok": True, "email": email})


@app.route("/api/password/forgot", methods=["POST"])
def forgot_password():
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        return jsonify({"error": "SMTP 未配置，请在 config.py 中填写邮箱和授权码"}), 500

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"error": "邮箱格式不正确"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({"error": "该邮箱未绑定账号"}), 400

    code = f"{secrets.randbelow(1000000):06d}"
    conn.execute("DELETE FROM email_codes WHERE user_id = ?", (user["id"],))
    conn.execute(
        "INSERT INTO email_codes (user_id, email, code, expires_at) "
        "VALUES (?, ?, ?, datetime('now', '+10 minutes'))",
        (user["id"], email, code),
    )
    conn.commit()
    conn.close()

    try:
        send_verification_email(email, code)
    except Exception as e:
        return jsonify({"error": f"邮件发送失败：{e}"}), 500

    return jsonify({"ok": True})


@app.route("/api/password/reset", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    new_password = data.get("new_password") or ""

    if not new_password:
        return jsonify({"error": "新密码不能为空"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None:
        conn.close()
        return jsonify({"error": "该邮箱未绑定账号"}), 400

    if check_password_hash(user["password_hash"], new_password):
        conn.close()
        return jsonify({"error": "新密码不能与旧密码相同"}), 400

    row = conn.execute(
        "SELECT * FROM email_codes WHERE user_id = ? AND email = ? "
        "AND expires_at > datetime('now') ORDER BY id DESC LIMIT 1",
        (user["id"], email),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "验证码已过期，请重新发送"}), 400
    if row["code"] != code:
        conn.close()
        return jsonify({"error": "验证码错误"}), 400

    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), user["id"]),
    )
    conn.execute("DELETE FROM email_codes WHERE user_id = ?", (user["id"],))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/questionnaires", methods=["POST"])
def create_questionnaire():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json(silent=True) or {}
    qtype = data.get("type") or ""
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    result_mode = data.get("result_mode") or "score"
    if not title:
        return jsonify({"error": "问卷名不能为空"}), 400

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO questionnaires (user_id, type, title, description, result_mode) VALUES (?, ?, ?, ?, ?)",
        (user["id"], qtype, title, description, result_mode),
    )
    conn.commit()
    qid = cur.lastrowid
    conn.close()

    return jsonify({"id": qid, "type": qtype, "title": title, "description": description, "status": "draft", "result_mode": result_mode})


@app.route("/api/questionnaires/mine", methods=["GET"])
def list_mine():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT id, type, title, status, updated_at, published_at, "
        "(SELECT COUNT(*) FROM responses WHERE questionnaire_id = questionnaires.id) AS response_count "
        "FROM questionnaires "
        "WHERE user_id = ? ORDER BY updated_at DESC",
        (user["id"],),
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/api/questionnaires/<int:qid>", methods=["GET"])
def get_questionnaire(qid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    q = conn.execute("SELECT * FROM questionnaires WHERE id = ?", (qid,)).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404

    questions = conn.execute(
        "SELECT * FROM questions WHERE questionnaire_id = ? ORDER BY order_index",
        (qid,),
    ).fetchall()
    question_list = []
    for question in questions:
        opts = conn.execute(
            "SELECT text, score, is_correct, jump_to FROM options WHERE question_id = ? ORDER BY order_index",
            (question["id"],),
        ).fetchall()
        question_list.append({
            "type": question["type"],
            "title": question["title"],
            "score": question["score"],
            "answer": question["answer"],
            "options": [
                {"text": o["text"], "score": o["score"], "is_correct": bool(o["is_correct"]), "jump_to": o["jump_to"] or ""}
                for o in opts
            ],
        })

    cards = conn.execute(
        "SELECT min_score, max_score, text, label FROM result_cards "
        "WHERE questionnaire_id = ? ORDER BY order_index",
        (qid,),
    ).fetchall()
    conn.close()

    return jsonify({
        "id": q["id"],
        "type": q["type"],
        "title": q["title"],
        "description": q["description"],
        "status": q["status"],
        "full_score": q["full_score"],
        "result_mode": q["result_mode"],
        "questions": question_list,
        "result_cards": [dict(c) for c in cards],
    })


@app.route("/api/questionnaires/<int:qid>", methods=["PUT"])
def update_questionnaire(qid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    try:
        q = conn.execute("SELECT * FROM questionnaires WHERE id = ?", (qid,)).fetchone()
        if q is None:
            return jsonify({"error": "问卷不存在"}), 404
        if q["user_id"] != user["id"]:
            return jsonify({"error": "无权限"}), 403

        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        description = (data.get("description") or "").strip()
        questions = data.get("questions") or []
        result_cards = data.get("result_cards") or []
        status = data.get("status")
        full_score = data.get("full_score")
        if full_score in (None, ""):
            full_score = None
        else:
            full_score = int(full_score)
        result_mode = data.get("result_mode") or "score"

        if status in ("draft", "published", "stopped"):
            if status == "published":
                conn.execute(
                    "UPDATE questionnaires SET title = ?, description = ?, status = ?, full_score = ?, result_mode = ?, updated_at = datetime('now'), published_at = datetime('now') WHERE id = ?",
                    (title, description, status, full_score, result_mode, qid),
                )
            else:
                conn.execute(
                    "UPDATE questionnaires SET title = ?, description = ?, status = ?, full_score = ?, result_mode = ?, updated_at = datetime('now') WHERE id = ?",
                    (title, description, status, full_score, result_mode, qid),
                )
        else:
            conn.execute(
                "UPDATE questionnaires SET title = ?, description = ?, full_score = ?, result_mode = ?, updated_at = datetime('now') WHERE id = ?",
                (title, description, full_score, result_mode, qid),
            )
        conn.execute(
            "DELETE FROM options WHERE question_id IN "
            "(SELECT id FROM questions WHERE questionnaire_id = ?)",
            (qid,),
        )
        conn.execute("DELETE FROM questions WHERE questionnaire_id = ?", (qid,))
        conn.execute("DELETE FROM result_cards WHERE questionnaire_id = ?", (qid,))

        for qi, qq in enumerate(questions):
            cur = conn.execute(
                "INSERT INTO questions (questionnaire_id, type, title, order_index, score, answer) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (qid, qq.get("type"), qq.get("title"), qi, qq.get("score") or 0, qq.get("answer") or ""),
            )
            question_id = cur.lastrowid
            for oi, o in enumerate(qq.get("options") or []):
                conn.execute(
                    "INSERT INTO options (question_id, text, score, order_index, is_correct, jump_to) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (question_id, o.get("text"), o.get("score") or 0, oi, 1 if o.get("is_correct") else 0, o.get("jump_to") or ""),
                )

        for ci, c in enumerate(result_cards):
            conn.execute(
                "INSERT INTO result_cards (questionnaire_id, min_score, max_score, text, order_index, label) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (qid, c.get("min_score") or 0, c.get("max_score") or 0, c.get("text"), ci, c.get("label") or ""),
            )

        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.route("/api/questionnaires/<int:qid>/status", methods=["POST"])
def set_questionnaire_status(qid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    q = conn.execute("SELECT * FROM questionnaires WHERE id = ?", (qid,)).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404
    if q["user_id"] != user["id"]:
        conn.close()
        return jsonify({"error": "无权限"}), 403

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status == "published":
        conn.execute(
            "UPDATE questionnaires SET status = 'published', updated_at = datetime('now'), published_at = datetime('now') WHERE id = ?",
            (qid,),
        )
    elif status == "stopped":
        conn.execute(
            "UPDATE questionnaires SET status = 'stopped', updated_at = datetime('now') WHERE id = ?",
            (qid,),
        )
    else:
        conn.close()
        return jsonify({"error": "无效状态"}), 400

    conn.commit()
    conn.close()
    return jsonify({"ok": True, "status": status})


@app.route("/api/questionnaires/<int:qid>", methods=["DELETE"])
def delete_questionnaire(qid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    q = conn.execute("SELECT * FROM questionnaires WHERE id = ?", (qid,)).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404
    if q["user_id"] != user["id"]:
        conn.close()
        return jsonify({"error": "无权限"}), 403

    conn.execute(
        "DELETE FROM options WHERE question_id IN "
        "(SELECT id FROM questions WHERE questionnaire_id = ?)",
        (qid,),
    )
    conn.execute("DELETE FROM questions WHERE questionnaire_id = ?", (qid,))
    conn.execute("DELETE FROM result_cards WHERE questionnaire_id = ?", (qid,))
    conn.execute("DELETE FROM questionnaires WHERE id = ?", (qid,))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/api/questionnaires/public", methods=["GET"])
def public_questionnaires():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT q.id, q.title, q.type, q.description, q.status, q.updated_at, q.user_id, u.username AS author, "
        "(SELECT COUNT(*) FROM user_actions WHERE questionnaire_id = q.id AND action = 'favorite') AS favorite_count, "
        "(SELECT COUNT(*) FROM user_actions WHERE questionnaire_id = q.id AND action = 'like') AS like_count, "
        "EXISTS(SELECT 1 FROM user_actions WHERE user_id = ? AND questionnaire_id = q.id AND action = 'favorite') AS favorited, "
        "EXISTS(SELECT 1 FROM user_actions WHERE user_id = ? AND questionnaire_id = q.id AND action = 'like') AS liked "
        "FROM questionnaires q JOIN users u ON u.id = q.user_id "
        "WHERE q.status = 'published' ORDER BY q.updated_at DESC",
        (user["id"], user["id"]),
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["favorited"] = bool(d["favorited"])
        d["liked"] = bool(d["liked"])
        d["is_owner"] = d["user_id"] == user["id"]
        d.pop("user_id", None)
        result.append(d)
    return jsonify(result)


@app.route("/api/questionnaires/<int:qid>/public", methods=["GET"])
def public_questionnaire(qid):
    user = current_user()
    conn = get_db()
    q = conn.execute(
        "SELECT q.id, q.type, q.title, q.description, q.status, q.result_mode, q.user_id, u.username AS author "
        "FROM questionnaires q JOIN users u ON u.id = q.user_id WHERE q.id = ?",
        (qid,),
    ).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404
    is_owner = user is not None and q["user_id"] == user["id"]
    if q["status"] != "published" and not is_owner:
        conn.close()
        return jsonify({"error": "问卷未发布"}), 404

    questions = conn.execute(
        "SELECT * FROM questions WHERE questionnaire_id = ? ORDER BY order_index",
        (qid,),
    ).fetchall()
    question_list = []
    for question in questions:
        opts = conn.execute(
            "SELECT text, jump_to FROM options WHERE question_id = ? ORDER BY order_index",
            (question["id"],),
        ).fetchall()
        question_list.append({
            "type": question["type"],
            "title": question["title"],
            "options": [{"text": o["text"], "jump_to": o["jump_to"] or ""} for o in opts],
        })
    conn.close()

    return jsonify({
        "id": q["id"],
        "type": q["type"],
        "title": q["title"],
        "description": q["description"],
        "author": q["author"],
        "status": q["status"],
        "result_mode": q["result_mode"],
        "is_owner": is_owner,
        "questions": question_list,
    })


@app.route("/api/questionnaires/<int:qid>/action", methods=["POST"])
def questionnaire_action(qid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("favorite", "like", "browse"):
        return jsonify({"error": "无效操作"}), 400

    conn = get_db()
    q = conn.execute("SELECT id FROM questionnaires WHERE id = ?", (qid,)).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404

    existing = conn.execute(
        "SELECT id FROM user_actions WHERE user_id = ? AND questionnaire_id = ? AND action = ?",
        (user["id"], qid, action),
    ).fetchone()

    if action in ("favorite", "like"):
        if existing:
            conn.execute("DELETE FROM user_actions WHERE id = ?", (existing["id"],))
            active = False
        else:
            conn.execute(
                "INSERT INTO user_actions (user_id, questionnaire_id, action) VALUES (?, ?, ?)",
                (user["id"], qid, action),
            )
            active = True
        conn.commit()
        conn.close()
        return jsonify({"active": active})

    if not existing:
        conn.execute(
            "INSERT INTO user_actions (user_id, questionnaire_id, action) VALUES (?, ?, ?)",
            (user["id"], qid, action),
        )
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/me/actions", methods=["GET"])
def my_actions():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT ua.action, q.id, q.title, q.type, q.status, q.updated_at "
        "FROM user_actions ua JOIN questionnaires q ON q.id = ua.questionnaire_id "
        "WHERE ua.user_id = ? ORDER BY ua.created_at DESC",
        (user["id"],),
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/api/me/notifications", methods=["GET"])
def my_notifications():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM ("
        "SELECT 'submit' AS kind, r.created_at, u.username AS actor, q.id AS qid, q.title "
        "FROM responses r "
        "JOIN questionnaires q ON q.id = r.questionnaire_id "
        "LEFT JOIN users u ON u.id = r.user_id "
        "WHERE q.user_id = ? "
        "UNION ALL "
        "SELECT ua.action AS kind, ua.created_at, u2.username AS actor, q.id AS qid, q.title "
        "FROM user_actions ua "
        "JOIN questionnaires q ON q.id = ua.questionnaire_id "
        "JOIN users u2 ON u2.id = ua.user_id "
        "WHERE q.user_id = ? AND ua.action IN ('like', 'favorite')"
        ") ORDER BY created_at DESC",
        (user["id"], user["id"]),
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route("/api/me/responses", methods=["GET"])
def my_responses():
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT q.id, q.title, q.type, q.user_id AS author_id, q.full_score "
        "FROM responses r JOIN questionnaires q ON q.id = r.questionnaire_id "
        "WHERE r.user_id = ? GROUP BY q.id ORDER BY MAX(r.created_at) DESC",
        (user["id"],),
    ).fetchall()

    result = []
    for row in rows:
        resp_rows = conn.execute(
            "SELECT id, total_score, result_text, answers, created_at FROM responses "
            "WHERE questionnaire_id = ? AND user_id = ? ORDER BY created_at DESC, id DESC",
            (row["id"], user["id"]),
        ).fetchall()
        responses = []
        for rr in resp_rows:
            answers = []
            if rr["answers"]:
                try:
                    answers = json.loads(rr["answers"])
                except Exception:
                    answers = []
            responses.append({
                "id": rr["id"],
                "total_score": rr["total_score"],
                "result_text": rr["result_text"],
                "answers": answers,
                "created_at": rr["created_at"],
            })

        full_score = row["full_score"]
        if full_score is None and row["type"] == "exam":
            full_score = conn.execute(
                "SELECT COALESCE(SUM(score), 0) FROM questions WHERE questionnaire_id = ?",
                (row["id"],),
            ).fetchone()[0]

        result.append({
            "id": row["id"],
            "title": row["title"],
            "type": row["type"],
            "mine": row["author_id"] == user["id"],
            "full_score": full_score,
            "responses": responses,
        })

    conn.close()
    return jsonify(result)


@app.route("/api/responses/<int:rid>", methods=["DELETE"])
def delete_response(rid):
    user = current_user()
    if not user:
        return jsonify({"error": "未登录"}), 401

    conn = get_db()
    r = conn.execute(
        "SELECT id FROM responses WHERE id = ? AND user_id = ?", (rid, user["id"])
    ).fetchone()
    if r is None:
        conn.close()
        return jsonify({"error": "记录不存在"}), 404

    conn.execute("DELETE FROM responses WHERE id = ?", (rid,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/questionnaires/<int:qid>/submit", methods=["POST"])
def submit_questionnaire(qid):
    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or []
    user = current_user()
    user_id = user["id"] if user else None

    conn = get_db()
    q = conn.execute("SELECT * FROM questionnaires WHERE id = ?", (qid,)).fetchone()
    if q is None:
        conn.close()
        return jsonify({"error": "问卷不存在"}), 404
    if q["status"] != "published":
        conn.close()
        return jsonify({"error": "问卷未发布"}), 404

    questions = conn.execute(
        "SELECT * FROM questions WHERE questionnaire_id = ? ORDER BY order_index",
        (qid,),
    ).fetchall()

    if q["type"] == "exam":
        total_score = 0
        answer_detail = []
        for i, question in enumerate(questions):
            qtype = question["type"]
            qscore = question["score"] or 0
            ans = answers[i] if i < len(answers) else None
            got = 0
            opts = conn.execute(
                "SELECT is_correct FROM options WHERE question_id = ? ORDER BY order_index",
                (question["id"],),
            ).fetchall()
            if qtype in ("single", "judge"):
                if isinstance(ans, int) and 0 <= ans < len(opts) and opts[ans]["is_correct"]:
                    got = qscore
            elif qtype == "multiple":
                if isinstance(ans, list):
                    correct = {oi for oi, o in enumerate(opts) if o["is_correct"]}
                    chosen = {oi for oi in ans if isinstance(oi, int)}
                    if chosen == correct:
                        got = qscore
            elif qtype == "fill":
                refs = [a.strip() for a in (question["answer"] or "").split("|") if a.strip()]
                if isinstance(ans, str) and ans.strip() in refs:
                    got = qscore
            total_score += got
            answer_detail.append({
                "title": question["title"],
                "answer": ans,
                "correct": got > 0,
                "score": got,
            })

        sum_score = sum((qq["score"] or 0) for qq in questions)
        full_score = q["full_score"] if q["full_score"] else sum_score

        conn.execute(
            "INSERT INTO responses (questionnaire_id, user_id, answers, total_score, result_text) VALUES (?, ?, ?, ?, ?)",
            (qid, user_id, json.dumps(answer_detail, ensure_ascii=False), total_score, ""),
        )

        if user_id is not None:
            existing = conn.execute(
                "SELECT id FROM user_actions WHERE user_id = ? AND questionnaire_id = ? AND action = 'use'",
                (user_id, qid),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO user_actions (user_id, questionnaire_id, action) VALUES (?, ?, 'use')",
                    (user_id, qid),
                )

        conn.commit()
        conn.close()

        return jsonify({
            "type": "exam",
            "total_score": total_score,
            "full_score": full_score,
        })

    if q["result_mode"] == "jump":
        result_label = data.get("result_label") or ""
        answer_detail = []
        for i, question in enumerate(questions):
            opts = conn.execute(
                "SELECT text FROM options WHERE question_id = ? ORDER BY order_index",
                (question["id"],),
            ).fetchall()
            ans = answers[i] if i < len(answers) else None
            selected = None
            if isinstance(ans, int) and 0 <= ans < len(opts):
                selected = opts[ans]["text"]
            answer_detail.append({
                "title": question["title"],
                "selected": selected,
            })
        card = conn.execute(
            "SELECT text FROM result_cards WHERE questionnaire_id = ? AND label = ?",
            (qid, result_label),
        ).fetchone()
        result_text = card["text"] if card else "暂无匹配的结果"

        conn.execute(
            "INSERT INTO responses (questionnaire_id, user_id, answers, total_score, result_text) VALUES (?, ?, ?, ?, ?)",
            (qid, user_id, json.dumps(answer_detail, ensure_ascii=False), 0, result_text),
        )

        if user_id is not None:
            existing = conn.execute(
                "SELECT id FROM user_actions WHERE user_id = ? AND questionnaire_id = ? AND action = 'use'",
                (user_id, qid),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO user_actions (user_id, questionnaire_id, action) VALUES (?, ?, 'use')",
                    (user_id, qid),
                )

        conn.commit()
        conn.close()

        return jsonify({
            "label": result_label,
            "result_text": result_text,
        })

    total_score = 0
    answer_detail = []
    for i, question in enumerate(questions):
        opts = conn.execute(
            "SELECT text, score FROM options WHERE question_id = ? ORDER BY order_index",
            (question["id"],),
        ).fetchall()
        oi = answers[i] if i < len(answers) else None
        selected = None
        if oi is not None and 0 <= oi < len(opts):
            selected = opts[oi]
        score = selected["score"] if selected else 0
        total_score += score
        answer_detail.append({
            "title": question["title"],
            "selected": selected["text"] if selected else None,
            "score": score,
        })

    cards = conn.execute(
        "SELECT min_score, max_score, text FROM result_cards WHERE questionnaire_id = ? ORDER BY order_index",
        (qid,),
    ).fetchall()
    result_text = None
    for c in cards:
        if c["min_score"] <= total_score <= c["max_score"]:
            result_text = c["text"]
            break
    if result_text is None:
        result_text = "暂无匹配的结果"

    conn.execute(
        "INSERT INTO responses (questionnaire_id, user_id, answers, total_score, result_text) VALUES (?, ?, ?, ?, ?)",
        (qid, user_id, json.dumps(answer_detail, ensure_ascii=False), total_score, result_text),
    )

    if user_id is not None:
        existing = conn.execute(
            "SELECT id FROM user_actions WHERE user_id = ? AND questionnaire_id = ? AND action = 'use'",
            (user_id, qid),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO user_actions (user_id, questionnaire_id, action) VALUES (?, ?, 'use')",
                (user_id, qid),
            )

    conn.commit()
    conn.close()

    return jsonify({
        "total_score": total_score,
        "result_text": result_text,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
