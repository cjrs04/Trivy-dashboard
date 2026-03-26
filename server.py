from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import subprocess, json, os, sqlite3
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DB_PATH = os.path.expanduser("~/.trivy-dashboard.db")

# database and table creation
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
#database connection - create a "scans" table
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_name TEXT NOT NULL,
            scanned_at TEXT NOT NULL,
            duration REAL,
            total INTEGER,
            critical INTEGER,
            high INTEGER,
            medium INTEGER,
            low INTEGER,
            unknown INTEGER,
            fixable INTEGER,
            results JSON NOT NULL
        )
    """)
    conn.commit()
    conn.close()
#initialise db
@app.on_event("startup")
async def startup():
    init_db()
    # Update Trivy DB once on startup
    subprocess.run(
        ["trivy", "image", "--download-db-only",
         "--cache-dir", os.path.expanduser("~/.cache/trivy")],
        capture_output=True
    )
#build a list of running containers using "docker ps" and return as JSON 
@app.get("/containers")
def list_containers():
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"],
        capture_output=True, text=True
    )
    containers = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            containers.append({
                "id": parts[0],
                "image": parts[1],
                "name": parts[2],
                "status": parts[3]
            })
    return containers
#runs trivy sec scan based on the target and type returns as JSON
@app.get("/scan")
def scan(
    target: str,
    scan_type: str = "image",   # image | container | fs | repo
    scanners: str = "vuln",
    hide_unfixed: bool = False
):
    t0 = datetime.now()

    type_cmd = {
        "image":     "image",
        "container": "image",   # trivy uses --input or container ID via image cmd
        "fs":        "fs",
        "repo":      "repo",
    }.get(scan_type, "image")

    cmd = [
        "trivy", type_cmd,
        "--format", "json",
        "--quiet",
        "--cache-dir", os.path.expanduser("~/.cache/trivy"),
        "--skip-db-update",
        "--scanners", scanners,
    ]

    if hide_unfixed:
        cmd.append("--ignore-unfixed")

    cmd.append(target)
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = (datetime.now() - t0).total_seconds()

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse Trivy output", "raw": result.stderr}

    # Count severities
    vulns = []
    if data.get("Results"):
        for r in data["Results"]:
            if r.get("Vulnerabilities"):
                vulns.extend(r["Vulnerabilities"])

    counts = {"CRITICAL":0,"HIGH":0,"MEDIUM":0,"LOW":0,"UNKNOWN":0} 
    fixable = 0
    for v in vulns:
        sev = v.get("Severity","UNKNOWN")
        counts[sev] = counts.get(sev, 0) + 1
        if v.get("FixedVersion"):
            fixable += 1

    # Save to DB
    conn = get_db()
    conn.execute("""
        INSERT INTO scans
        (image_name, scanned_at, duration, total, critical, high, medium, low, unknown, fixable, results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        target,
        datetime.now().isoformat(),
        round(duration, 2),
        len(vulns),
        counts["CRITICAL"], counts["HIGH"], counts["MEDIUM"],
        counts["LOW"], counts["UNKNOWN"],
        fixable,
        json.dumps(data)
    ))
    conn.commit()
    conn.close()

    return {**data, "_meta": {"duration": round(duration, 2), "total": len(vulns), "fixable": fixable}}
#quires database for history (last 50 scans, any more and it slows)
@app.get("/history")
def get_history():
    conn = get_db()
    rows = conn.execute("""
        SELECT id, image_name, scanned_at, duration, total,
               critical, high, medium, low, unknown, fixable, results
        FROM scans ORDER BY scanned_at DESC LIMIT 50
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
#delete history
@app.delete("/history/{scan_id}")
def delete_scan(scan_id: int):
    conn = get_db()
    conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    conn.commit()
    conn.close()
    return {"deleted": scan_id}

app.mount("/", StaticFiles(directory=".", html=True), name="static")
