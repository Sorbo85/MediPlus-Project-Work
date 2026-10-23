from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mediplus.db"
app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            doctor_id INTEGER NOT NULL REFERENCES doctors(id),
            appointment_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Prenotata'
              CHECK(status IN ('Prenotata','Confermata','Completata','Annullata')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        if db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
            db.executemany("INSERT INTO doctors(name,specialty,email) VALUES(?,?,?)", [
                ("Dott.ssa Giulia Bianchi", "Cardiologia", "giulia.bianchi@demo.local"),
                ("Dott. Marco Rossi", "Dermatologia", "marco.rossi@demo.local"),
                ("Dott.ssa Sara Conti", "Medicina generale", "sara.conti@demo.local")
            ])
        if db.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            db.executemany("INSERT INTO patients(name,email,phone) VALUES(?,?,?)", [
                ("Luca Verdi", "luca.verdi@example.test", "3330000001"),
                ("Anna Neri", "anna.neri@example.test", "3330000002"),
                ("Paolo Gallo", "paolo.gallo@example.test", "3330000003")
            ])
        if db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
            db.executemany("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,reason,status)
                              VALUES(?,?,?,?,?)""", [
                (1,1,"2026-10-14T09:30","Controllo cardiologico","Confermata"),
                (2,2,"2026-10-14T11:00","Visita dermatologica","Prenotata"),
                (3,3,"2026-10-15T15:30","Visita di controllo","Confermata")
            ])

def error(message, code=400):
    return jsonify({"error": message}), code

@app.get("/")
def home():
    return send_from_directory("frontend", "index.html")

@app.get("/api/health")
def health():
    return jsonify({"status":"ok","service":"MediPlus API"})

@app.get("/api/doctors")
def doctors():
    with connect() as db:
        rows = db.execute("SELECT id,name,specialty,email FROM doctors ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/patients")
def patients():
    with connect() as db:
        rows = db.execute("SELECT id,name,email,phone FROM patients ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/appointments")
def list_appointments():
    status = request.args.get("status")
    search = request.args.get("q", "").strip()
    query = """SELECT a.id,a.patient_id,a.doctor_id,a.appointment_date,a.reason,a.status,
                      p.name AS patient_name,d.name AS doctor_name,d.specialty
               FROM appointments a
               JOIN patients p ON p.id=a.patient_id
               JOIN doctors d ON d.id=a.doctor_id
               WHERE 1=1"""
    args = []
    if status and status != "Tutte":
        query += " AND a.status=?"; args.append(status)
    if search:
        query += " AND (p.name LIKE ? OR d.name LIKE ? OR a.reason LIKE ?)"
        term = f"%{search}%"; args.extend([term,term,term])
    query += " ORDER BY a.appointment_date ASC"
    with connect() as db:
        rows = db.execute(query, args).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/appointments")
def create_appointment():
    data = request.get_json(silent=True) or {}
    required = ["patient_id","doctor_id","appointment_date","reason"]
    missing = [k for k in required if data.get(k) in (None, "")]
    if missing:
        return error("Campi obbligatori mancanti: " + ", ".join(missing))
    try:
        patient_id, doctor_id = int(data["patient_id"]), int(data["doctor_id"])
    except (ValueError, TypeError):
        return error("patient_id e doctor_id devono essere numeri interi.")
    date_value = str(data["appointment_date"]).strip()
    try:
        parsed = datetime.fromisoformat(date_value)
        if parsed < datetime.now():
            return error("La data della visita deve essere futura.")
    except ValueError:
        return error("Formato data non valido. Usa YYYY-MM-DDTHH:MM.")
    reason = str(data["reason"]).strip()
    if len(reason) < 3:
        return error("La motivazione deve contenere almeno 3 caratteri.")
    with connect() as db:
        if not db.execute("SELECT 1 FROM patients WHERE id=?", (patient_id,)).fetchone():
            return error("Paziente non trovato.", 404)
        if not db.execute("SELECT 1 FROM doctors WHERE id=?", (doctor_id,)).fetchone():
            return error("Medico non trovato.", 404)
        conflict = db.execute("""SELECT 1 FROM appointments
            WHERE doctor_id=? AND appointment_date=? AND status!='Annullata'""",
            (doctor_id,date_value)).fetchone()
        if conflict:
            return error("Il medico ha già una visita in quell'orario.", 409)
        cur = db.execute("""INSERT INTO appointments(patient_id,doctor_id,appointment_date,reason,status)
                            VALUES(?,?,?,?, 'Prenotata')""",
                         (patient_id,doctor_id,date_value,reason))
        new_id = cur.lastrowid
    return jsonify({"id":new_id,"message":"Prenotazione creata"}), 201

@app.patch("/api/appointments/<int:appointment_id>")
def update_appointment(appointment_id):
    data = request.get_json(silent=True) or {}
    allowed = {"status": {"Prenotata","Confermata","Completata","Annullata"}}
    if "status" not in data:
        return error("Specificare il campo status.")
    if data["status"] not in allowed["status"]:
        return error("Stato non valido.")
    with connect() as db:
        cur = db.execute("UPDATE appointments SET status=? WHERE id=?",
                         (data["status"],appointment_id))
        if cur.rowcount == 0:
            return error("Prenotazione non trovata.", 404)
    return jsonify({"message":"Stato aggiornato","id":appointment_id,"status":data["status"]})

@app.delete("/api/appointments/<int:appointment_id>")
def delete_appointment(appointment_id):
    with connect() as db:
        cur = db.execute("DELETE FROM appointments WHERE id=?", (appointment_id,))
        if cur.rowcount == 0:
            return error("Prenotazione non trovata.", 404)
    return jsonify({"message":"Prenotazione eliminata"})

@app.get("/api/dashboard")
def dashboard():
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        upcoming = db.execute("""SELECT COUNT(*) FROM appointments
                                 WHERE appointment_date >= ? AND status!='Annullata'""",
                              (datetime.now().isoformat(timespec="minutes"),)).fetchone()[0]
        confirmed = db.execute("SELECT COUNT(*) FROM appointments WHERE status='Confermata'").fetchone()[0]
        doctors = db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    return jsonify({"total_appointments":total,"upcoming_appointments":upcoming,
                    "confirmed_appointments":confirmed,"doctors":doctors})

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith("/api/"):
        return jsonify({"error":"Risorsa API non trovata"}),404
    return "Pagina non trovata",404

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5000)
