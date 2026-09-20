
MindBill Pro - Behavioral Health Denial & Appeal Manager
Run:  streamlit run app.py

Features
- Real login (PBKDF2 password hashing, lockout, session timeout, roles)
- Denial case tracker (SQLite) with deadlines and dashboard
- Appeal letter (TXT/PDF), AR call script, corrected-claim 837P export
- Payer directory (you enter verified appeal addresses / payer IDs)
- Audit log
"""
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import date, datetime, timedelta
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st

try:
    from reportlab.lib.pagesizes import letter as LETTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# ----------------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------------
DB_PATH = os.environ.get("MINDBILL_DB", "mindbill.db")
SESSION_TIMEOUT_MIN = 30
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
PBKDF2_ITERATIONS = 600_000

st.set_page_config(page_title="MindBill Pro", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px;
        padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# REFERENCE DATA
# ----------------------------------------------------------------------------
# CARC: code -> (description, category)
# categories: patient | contractual | correct | verify | appeal
CARC = {
    1: ("Deductible amount", "patient"),
    2: ("Coinsurance amount", "patient"),
    3: ("Co-payment amount", "patient"),
    4: ("Procedure code inconsistent with modifier / required modifier missing", "correct"),
    5: ("Procedure code inconsistent with place of service", "correct"),
    11: ("Diagnosis inconsistent with procedure", "correct"),
    16: ("Claim lacks information or has submission/billing error(s)", "correct"),
    18: ("Exact duplicate claim/service", "verify"),
    22: ("May be covered by another payer (coordination of benefits)", "verify"),
    26: ("Expenses incurred prior to coverage", "verify"),
    27: ("Expenses incurred after coverage terminated", "verify"),
    29: ("Time limit for filing has expired", "appeal"),
    31: ("Patient cannot be identified as our insured", "correct"),
    45: ("Charge exceeds fee schedule / contracted amount", "contractual"),
    50: ("Not deemed a medical necessity by the payer", "appeal"),
    96: ("Non-covered charge(s)", "appeal"),
    97: ("Benefit included in payment for another service already adjudicated", "correct"),
    109: ("Claim not covered by this payer - send to correct payer", "correct"),
    119: ("Benefit maximum for this time period has been reached", "verify"),
    140: ("Patient ID and name do not match", "correct"),
    151: ("Submitted information does not support this many/frequency of services", "appeal"),
    167: ("Diagnosis is not covered", "appeal"),
    197: ("Precertification/authorization/notification absent", "appeal"),
    198: ("Precertification/authorization exceeded", "appeal"),
    204: ("Service not covered under patient's current benefit plan", "appeal"),
    252: ("Attachment/other documentation required", "correct"),
}

CATEGORY_INFO = {
    "patient": ("warning", "Patient responsibility. Do not appeal; bill the patient per plan terms."),
    "contractual": ("warning", "Contractual adjustment. Normally written off. Appeal only if the payment does not match your contract's fee schedule."),
    "correct": ("info", "Usually fixed with a corrected claim (frequency code 7) or by sending the missing data, not a formal appeal. See the Corrected Claim tab."),
    "verify": ("info", "Investigate first (eligibility, COB, original claim). Appeal only if your records show the denial was wrong."),
    "appeal": ("success", "A formal appeal is appropriate. See the Appeal Letter tab."),
}

CPT_CODES = {
    "90791": "Psychiatric diagnostic evaluation",
    "90792": "Psychiatric diagnostic evaluation with medical services",
    "90832": "Psychotherapy, 30 min",
    "90834": "Psychotherapy, 45 min",
    "90837": "Psychotherapy, 60 min",
    "90839": "Psychotherapy for crisis, first 60 min",
    "90846": "Family psychotherapy without patient",
    "90847": "Family psychotherapy with patient",
    "90853": "Group psychotherapy",
    "90785": "Interactive complexity (add-on)",
    "90833": "Psychotherapy 30 min with E/M (add-on)",
    "90836": "Psychotherapy 45 min with E/M (add-on)",
    "90838": "Psychotherapy 60 min with E/M (add-on)",
    "99213": "E/M established patient, low",
    "99214": "E/M established patient, moderate",
    "99215": "E/M established patient, high",
}

POS_CODES = {
    "02": "Telehealth (patient not at home)",
    "10": "Telehealth (patient at home)",
    "11": "Office",
    "22": "On-campus outpatient hospital",
    "53": "Community mental health center",
}

STATUSES = ["New", "Appeal Drafted", "Appeal Submitted", "Corrected Claim Sent",
            "Won / Paid", "Lost", "Written Off", "Patient Responsibility"]
CLOSED_STATUSES = ["Won / Paid", "Lost", "Written Off", "Patient Responsibility"]
LEVELS = ["Initial denial", "1st-level appeal", "2nd-level appeal", "External review"]
CLAIM_FILING = ["CI", "BL", "HM", "MB", "MC", "ZZ"]  # commercial, BCBS, HMO, Medicare B, Medicaid, other

ENCLOSURE_OPTIONS = [
    "Progress note for the date of service",
    "Copy of denial / EOB / remittance advice",
    "Copy of original claim (CMS-1500)",
    "Treatment plan",
    "Authorization letter / number",
    "Proof of timely filing (clearinghouse acceptance report)",
    "Eligibility verification for date of service",
]

PW_HELP = "At least 12 characters with upper case, lower case and a number."

# ----------------------------------------------------------------------------
# DATABASE
# ----------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def q(sql, params=()):
    with closing(get_conn()) as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def x(sql, params=()):
    with closing(get_conn()) as c:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid


def init_db():
    with closing(get_conn()) as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'biller',
                pw_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS payers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                payer_id TEXT DEFAULT '',
                claim_filing TEXT DEFAULT 'CI',
                appeal_days INTEGER DEFAULT 180,
                appeal_address TEXT DEFAULT '',
                appeal_fax TEXT DEFAULT '',
                portal_url TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT, created_by TEXT,
                patient_first TEXT, patient_last TEXT, patient_dob TEXT, patient_gender TEXT,
                patient_street TEXT, patient_city TEXT, patient_state TEXT, patient_zip TEXT,
                member_id TEXT, payer TEXT, claim_number TEXT,
                dos TEXT, cpt TEXT, modifiers TEXT, pos TEXT, billed REAL, dx_code TEXT,
                group_code TEXT, carc INTEGER, denial_date TEXT, deadline TEXT,
                status TEXT DEFAULT 'New', appeal_level TEXT DEFAULT 'Initial denial',
                recovered REAL DEFAULT 0, rationale TEXT, notes TEXT
            );
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL, username TEXT, action TEXT NOT NULL, detail TEXT
            );
            """
        )
        if not c.execute("SELECT 1 FROM payers LIMIT 1").fetchone():
            for name in ["Aetna", "Cigna / Evernorth", "UnitedHealthcare / Optum",
                         "Blue Cross Blue Shield", "Medicare", "Medicaid", "Other"]:
                c.execute("INSERT INTO payers (name) VALUES (?)", (name,))
        c.commit()


def audit(action, detail="", user=None):
    if user is None:
        user = (st.session_state.get("user") or {}).get("username", "-")
    x("INSERT INTO audit (ts, username, action, detail) VALUES (?,?,?,?)",
      (datetime.now().isoformat(timespec="seconds"), user, action, detail))


def load_practice():
    rows = q("SELECT value FROM settings WHERE key='practice'")
    return json.loads(rows[0]["value"]) if rows else {}


def save_practice(data):
    x("INSERT INTO settings (key, value) VALUES ('practice', ?) "
      "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(data),))


# ----------------------------------------------------------------------------
# AUTHENTICATION
# ----------------------------------------------------------------------------
def hash_pw(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex),
                               PBKDF2_ITERATIONS).hex()


def password_error(pw):
    if len(pw) < 12:
        return "Password must be at least 12 characters."
    if not (re.search(r"[a-z]", pw) and re.search(r"[A-Z]", pw) and re.search(r"\d", pw)):
        return "Password needs upper case, lower case and a number."
    return ""


def create_user(username, full_name, password, role):
    salt = secrets.token_hex(16)
    x("INSERT INTO users (username, full_name, role, pw_hash, salt, created_at) VALUES (?,?,?,?,?,?)",
      (username.strip().lower(), full_name.strip(), role, hash_pw(password, salt),
       salt, datetime.now().isoformat(timespec="seconds")))


def set_password(user_id, password):
    salt = secrets.token_hex(16)
    x("UPDATE users SET pw_hash=?, salt=?, failed_attempts=0, locked_until=NULL WHERE id=?",
      (hash_pw(password, salt), salt, user_id))


def authenticate(username, password):
    uname = username.strip().lower()
    rows = q("SELECT * FROM users WHERE username=?", (uname,))
    if not rows:
        hash_pw(password, secrets.token_hex(16))  # equalise timing
        audit("login_failed", "unknown user", user=uname)
        return None, "Invalid username or password."
    u = rows[0]
    if not u["active"]:
        return None, "This account is disabled. Contact your administrator."
    if u["locked_until"] and datetime.fromisoformat(u["locked_until"]) > datetime.now():
        return None, "Account temporarily locked after too many attempts. Try again later."
    if hmac.compare_digest(hash_pw(password, u["salt"]), u["pw_hash"]):
        x("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?", (u["id"],))
        audit("login", user=uname)
        return u, ""
    n = u["failed_attempts"] + 1
    locked = None
    if n >= MAX_FAILED_LOGINS:
        locked = (datetime.now() + timedelta(minutes=LOCK_MINUTES)).isoformat()
        n = 0
    x("UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?", (n, locked, u["id"]))
    audit("login_failed", "bad password" + (" - account locked" if locked else ""), user=uname)
    return None, "Invalid username or password."


def enforce_session():
    u = st.session_state.get("user")
    if not u:
        return False
    last = st.session_state.get("last_active", datetime.now())
    if datetime.now() - last > timedelta(minutes=SESSION_TIMEOUT_MIN):
        audit("session_timeout", user=u["username"])
        st.session_state.clear()
        st.session_state["flash"] = "Session expired. Please sign in again."
        return False
    st.session_state["last_active"] = datetime.now()
    return True


def login_screen():
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("## 🧠 MindBill Pro")
        st.caption("Behavioral Health Denial & Appeal Manager")
        if st.session_state.get("flash"):
            st.warning(st.session_state.pop("flash"))
        st.markdown("---")

        if not q("SELECT 1 FROM users LIMIT 1"):
            st.info("First-time setup: create the administrator account.")
            with st.form("setup"):
                name = st.text_input("Full name")
                username = st.text_input("Username")
                pw = st.text_input("Password", type="password", help=PW_HELP)
                pw2 = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create admin account"):
                    err = ("Fill in all fields." if not (name.strip() and username.strip() and pw)
                           else "Passwords do not match." if pw != pw2
                           else password_error(pw))
                    if err:
                        st.error(err)
                    else:
                        create_user(username, name, pw, "admin")
                        audit("admin_created", username, user=username.strip().lower())
                        st.success("Admin created. You can sign in now.")
                        st.rerun()
        else:
            with st.form("login"):
                username = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("Sign in"):
                    user, err = authenticate(username, pw)
                    if user:
                        st.session_state["user"] = {"id": user["id"], "username": user["username"],
                                                    "full_name": user["full_name"], "role": user["role"]}
                        st.session_state["last_active"] = datetime.now()
                        st.rerun()
                    else:
                        st.error(err)
        st.caption(f"Sessions expire after {SESSION_TIMEOUT_MIN} minutes of inactivity.")


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def fmt_money(v):
    return f"${float(v or 0):,.2f}"


def valid_npi(npi):
    """NPI check digit (Luhn with 80840 prefix)."""
    if not re.fullmatch(r"\d{10}", npi or ""):
        return False
    total = 0
    for i, ch in enumerate(reversed("80840" + npi)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def valid_icd10(code):
    return bool(re.fullmatch(r"[A-TV-Z][0-9][0-9AB]\.?[0-9A-TV-Z]{0,4}", code or ""))


def get_payer(name):
    rows = q("SELECT * FROM payers WHERE name=?", (name,))
    return rows[0] if rows else {"name": name, "payer_id": "", "claim_filing": "CI",
                                 "appeal_days": 180, "appeal_address": "", "appeal_fax": "", "portal_url": ""}


def text_to_pdf(text):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=54, rightMargin=54,
                            topMargin=54, bottomMargin=54)
    style = getSampleStyleSheet()["BodyText"]
    story = []
    for block in text.split("\n\n"):
        story.append(Paragraph(escape(block).replace("\n", "<br/>"), style))
        story.append(Spacer(1, 8))
    doc.build(story)
    return buf.getvalue()


# ----------------------------------------------------------------------------
# DOCUMENT GENERATORS
# ----------------------------------------------------------------------------
def appeal_argument(case):
    code = case["carc"]
    patient = f"{case['patient_first']} {case['patient_last']}"
    rationale = case.get("rationale") or "[Add clinical rationale in the case details]"
    dos, cpt, dx = case["dos"], case["cpt"], case["dx_code"]

    if code in (50, 96, 151, 167, 204):
        return (f"The service billed under CPT {cpt} on {dos} was medically necessary. {patient} carries the "
                f"diagnosis {dx}. Clinical rationale: {rationale} The treatment is consistent with generally "
                f"accepted standards of behavioral health practice. The enclosed progress note documents the "
                f"session start/stop times, interventions delivered and the patient's response.")
    if code in (197, 198):
        return (f"Services under CPT {cpt} on {dos} were rendered for {patient} (diagnosis {dx}). "
                f"Authorization reference: [enter authorization number and approved units, or state that "
                f"retrospective authorization is requested]. Clinical rationale: {rationale} If the plan "
                f"considers authorization required for this service, please cite the plan provision.")
    if code == 29:
        return (f"The claim for {dos} was submitted within the filing limit. Proof of timely filing "
                f"(clearinghouse acceptance report / payer acknowledgment dated [enter date]) is enclosed.")
    if code in (26, 27, 22, 119, 18):
        return (f"Our records show {patient} was eligible on {dos} and this claim is not a duplicate. "
                f"Details: [describe eligibility / COB / original claim facts]. Verification is enclosed.")
    return (f"The claim for CPT {cpt} on {dos} (diagnosis {dx}) was adjudicated in error under CARC {code}. "
            f"Clinical rationale: {rationale} Supporting documentation is enclosed.")


def build_appeal_letter(case, payer, practice, enclosures):
    P = lambda k: practice.get(k) or "[NOT SET]"
    code = case["carc"]
    desc = CARC.get(code, ("", ""))[0]
    header = (f"{P('billing_name')}\n{P('billing_street')}\n"
              f"{P('billing_city')}, {P('billing_state')} {P('billing_zip')}\n"
              f"Phone: {P('phone')} | Billing NPI: {P('billing_npi')} | Tax ID: {P('tax_id')}")
    addr = payer.get("appeal_address") or "[Appeals address - set it in Payers]"
    fax = f"Fax: {payer['appeal_fax']}" if payer.get("appeal_fax") else ""
    rendering = f"{practice.get('rendering_first', '')} {practice.get('rendering_last', '')}".strip()
    if practice.get("rendering_creds"):
        rendering += f", {practice['rendering_creds']}"
    rendering = rendering or "[NOT SET]"
    enc = "\n".join(f"{i}. {e}" for i, e in enumerate(enclosures, 1)) or "None"

    parity = ""
    if code in (50, 96, 151, 167, 197, 198, 204):
        parity = ("\n\nParity: To the extent this denial reflects a limit on behavioral health benefits "
                  "(medical necessity criteria, frequency limits or authorization requirements), we request "
                  "the specific criteria applied and the comparative analysis showing these limits are no more "
                  "restrictive than those applied to comparable medical/surgical benefits, as required under "
                  "the Mental Health Parity and Addiction Equity Act (MHPAEA).")

    return f"""{header}

{date.today():%B %d, %Y}

{payer['name']} - Appeals Department
{addr}
{fax}

RE: Request for Appeal / Reconsideration of Denied Claim
Patient: {case['patient_first']} {case['patient_last']} (DOB {case['patient_dob']})
Member ID: {case['member_id']}
Claim / ICN: {case['claim_number']}
Date of service: {case['dos']}
CPT / Modifiers: {case['cpt']} / {case.get('modifiers') or 'none'}
Diagnosis: {case['dx_code']}
Billed amount: {fmt_money(case['billed'])}
Denial: {case['group_code']}-{code} ({desc}), denial date {case['denial_date']}
Rendering provider: {rendering} (NPI {P('rendering_npi')})

To the Appeals Committee:

We are formally appealing the denial of the claim referenced above and request full reconsideration.

BASIS FOR APPEAL
{appeal_argument(case)}{parity}

REQUEST
We ask that the denial be overturned and the claim reprocessed for payment. If the denial is upheld, please provide a written explanation, the criteria used, the name and credentials of the reviewer, and information on further appeal and external review rights.

ENCLOSURES
{enc}

Sincerely,

{rendering}
{P('billing_name')}"""


def build_call_script(case, payer, practice):
    return f"""1. IDENTIFY
"I'm calling from {practice.get('billing_name') or '[practice]'}, NPI {practice.get('billing_npi') or '[NPI]'}, Tax ID {practice.get('tax_id') or '[TIN]'}, about claim {case['claim_number']} for {case['patient_first']} {case['patient_last']}, member ID {case['member_id']}, date of service {case['dos']}."

2. DENIAL
"The claim for CPT {case['cpt']} was denied with {case['group_code']}-{case['carc']}: {CARC.get(case['carc'], ('',''))[0]}. Can you confirm the reason and what is needed to resolve it?"

3. ASK
- Is the claim eligible for reprocessing, or does it need a corrected claim / formal appeal?
- What is the appeal deadline and the correct fax/address/portal?
- Is any documentation missing?

4. CLOSE
Record: representative name, date/time, call reference number, promised next step.
Reference #: ______  Rep: ______  Date: ______"""


def edi_clean(v):
    return re.sub(r"[*~:^\r\n]", " ", str(v or "")).upper().strip()


REQUIRED_EDI_PRACTICE = ["billing_name", "billing_npi", "tax_id", "billing_street", "billing_city",
                         "billing_state", "billing_zip", "phone", "rendering_first", "rendering_last",
                         "rendering_npi", "taxonomy", "submitter_id", "receiver_id"]


def build_837p(case, payer, practice, freq="7", usage="T"):
    """Single-claim 837P (005010X222A1). Patient is assumed to be the subscriber.
    Validate with your clearinghouse in TEST mode before production use."""
    now = datetime.now()
    d8, t4 = now.strftime("%Y%m%d"), now.strftime("%H%M")
    ctrl = f"{case['id']:09d}"
    sender, receiver = edi_clean(practice["submitter_id"]), edi_clean(practice["receiver_id"])
    tin = re.sub(r"\D", "", practice["tax_id"])
    phone = re.sub(r"\D", "", practice["phone"])
    dob = case["patient_dob"].replace("-", "")
    dos = case["dos"].replace("-", "")
    dx = case["dx_code"].replace(".", "").upper()
    mods = [m for m in re.split(r"[,\s]+", case.get("modifiers") or "") if m][:4]
    proc = ":".join(["HC", case["cpt"]] + [m.upper() for m in mods])
    amt = f"{float(case['billed']):.2f}"
    bill_zip = re.sub(r"\D", "", practice["billing_zip"])[:9]
    pat_zip = re.sub(r"\D", "", case["patient_zip"])[:9]

    body = [
        "ST*837*0001*005010X222A1",
        f"BHT*0019*00*{ctrl}*{d8}*{t4}*CH",
        f"NM1*41*2*{edi_clean(practice['billing_name'])}*****46*{sender}",
        f"PER*IC*{edi_clean(practice['billing_name'])}*TE*{phone}",
        f"NM1*40*2*{edi_clean(payer['name'])}*****46*{receiver}",
        "HL*1**20*1",
        f"NM1*85*2*{edi_clean(practice['billing_name'])}*****XX*{practice['billing_npi']}",
        f"N3*{edi_clean(practice['billing_street'])}",
        f"N4*{edi_clean(practice['billing_city'])}*{edi_clean(practice['billing_state'])}*{bill_zip}",
        f"REF*EI*{tin}",
        "HL*2*1*22*0",
        f"SBR*P*18*******{payer.get('claim_filing') or 'CI'}",
        f"NM1*IL*1*{edi_clean(case['patient_last'])}*{edi_clean(case['patient_first'])}****MI*{edi_clean(case['member_id'])}",
        f"N3*{edi_clean(case['patient_street'])}",
        f"N4*{edi_clean(case['patient_city'])}*{edi_clean(case['patient_state'])}*{pat_zip}",
        f"DMG*D8*{dob}*{case['patient_gender']}",
        f"NM1*PR*2*{edi_clean(payer['name'])}*****PI*{edi_clean(payer['payer_id'])}",
        f"CLM*MB{case['id']:06d}*{amt}***{case['pos']}:B:{freq}*Y*A*Y*Y",
    ]
    if freq in ("7", "8"):
        body.append(f"REF*F8*{edi_clean(case['claim_number'])}")
    body += [
        f"HI*ABK:{dx}",
        f"NM1*82*1*{edi_clean(practice['rendering_last'])}*{edi_clean(practice['rendering_first'])}****XX*{practice['rendering_npi']}",
        f"PRV*PE*PXC*{edi_clean(practice['taxonomy'])}",
        "LX*1",
        f"SV1*{proc}*{amt}*UN*1***1",
        f"DTP*472*D8*{dos}",
    ]
    body.append(f"SE*{len(body) + 1}*0001")

    isa = (f"ISA*00*          *00*          *ZZ*{sender:<15}*ZZ*{receiver:<15}*"
           f"{now.strftime('%y%m%d')}*{t4}*^*00501*{ctrl}*0*{usage}*:")
    segments = [isa, f"GS*HC*{sender}*{receiver}*{d8}*{t4}*1*X*005010X222A1"] + body + \
               ["GE*1*1", f"IEA*1*{ctrl}"]
    return "~\n".join(segments) + "~\n"


# ----------------------------------------------------------------------------
# PAGES
# ----------------------------------------------------------------------------
def page_dashboard():
    st.title("Dashboard")
    rows = q("SELECT * FROM claims")
    if not rows:
        st.info("No cases yet. Add your first denial under **New Case**.")
        return
    df = pd.DataFrame(rows)
    open_df = df[~df["status"].isin(CLOSED_STATUSES)]
    won, lost = df[df["status"] == "Won / Paid"], df[df["status"] == "Lost"]
    decided = len(won) + len(lost)

    a, b, c, d = st.columns(4)
    a.metric("Open cases", len(open_df))
    b.metric("Open denied amount", fmt_money(open_df["billed"].sum()))
    c.metric("Recovered", fmt_money(won["recovered"].sum()))
    d.metric("Appeal win rate", f"{len(won) / decided:.0%}" if decided else "-")

    st.subheader("Deadlines in the next 14 days (or overdue)")
    cutoff = pd.Timestamp(date.today() + timedelta(days=14))
    soon = open_df[pd.to_datetime(open_df["deadline"]) <= cutoff].copy()
    if soon.empty:
        st.success("Nothing due soon.")
    else:
        soon["days_left"] = (pd.to_datetime(soon["deadline"]) - pd.Timestamp(date.today())).dt.days
        st.dataframe(soon.sort_values("days_left")[["id", "patient_last", "payer", "carc", "billed",
                                                     "status", "deadline", "days_left"]], hide_index=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Cases by status")
        st.bar_chart(df["status"].value_counts())
    with right:
        st.subheader("Denials by CARC")
        st.bar_chart(df["carc"].astype(str).value_counts())


def page_new_case():
    st.title("New Denial Case")
    payers = [p["name"] for p in q("SELECT name FROM payers ORDER BY name")]

    st.subheader("Patient")
    c1, c2, c3 = st.columns(3)
    first = c1.text_input("First name")
    last = c2.text_input("Last name")
    dob = c3.date_input("Date of birth", value=date(1990, 1, 1),
                        min_value=date(1900, 1, 1), max_value=date.today())
    c1, c2, c3 = st.columns(3)
    member_id = c1.text_input("Member ID")
    gender = c2.selectbox("Sex", ["F", "M", "U"])
    street = c3.text_input("Street address")
    c1, c2, c3 = st.columns(3)
    city = c1.text_input("City")
    state = c2.text_input("State (2 letters)", max_chars=2)
    zipc = c3.text_input("ZIP")

    st.subheader("Claim & denial")
    c1, c2, c3 = st.columns(3)
    payer_name = c1.selectbox("Payer", payers)
    claim_number = c2.text_input("Payer claim # / ICN")
    dos = c3.date_input("Date of service", value=date.today(), max_value=date.today())
    c1, c2, c3 = st.columns(3)
    cpt = c1.selectbox("CPT", list(CPT_CODES), format_func=lambda k: f"{k} - {CPT_CODES[k]}")
    modifiers = c2.text_input("Modifiers (comma separated)", placeholder="95, HO")
    pos = c3.selectbox("Place of service", list(POS_CODES), index=2,
                       format_func=lambda k: f"{k} - {POS_CODES[k]}")
    c1, c2, c3 = st.columns(3)
    billed = c1.number_input("Billed amount ($)", min_value=0.0, step=5.0, format="%.2f")
    dx = c2.text_input("Primary ICD-10", placeholder="F41.1")
    denial_date = c3.date_input("Denial date", value=date.today(), max_value=date.today())
    c1, c2, c3 = st.columns([1, 2, 1])
    group = c1.selectbox("Group code", ["CO", "PR", "OA", "PI"])
    carc = c2.selectbox("CARC", list(CARC), format_func=lambda k: f"{k} - {CARC[k][0]}")
    payer = get_payer(payer_name)
    default_deadline = denial_date + timedelta(days=int(payer.get("appeal_days") or 180))
    deadline = c3.date_input("Appeal deadline", value=default_deadline,
                             key=f"dl_{payer_name}_{denial_date}",
                             help="Defaults to the payer's appeal window. Confirm on your denial letter.")

    kind, msg = CATEGORY_INFO[CARC[carc][1]]
    getattr(st, kind)(msg)
    rationale = st.text_area("Clinical rationale (used in the appeal letter)", height=90)
    notes = st.text_area("Notes", height=60)

    if st.button("Save case", type="primary"):
        errors = []
        if not (first.strip() and last.strip()):
            errors.append("Patient first and last name are required.")
        if not member_id.strip():
            errors.append("Member ID is required.")
        if not claim_number.strip():
            errors.append("Claim number is required.")
        if billed <= 0:
            errors.append("Billed amount must be greater than 0.")
        if not valid_icd10(dx.strip().upper()):
            errors.append("Enter a valid ICD-10 code (e.g. F41.1).")
        if errors:
            for e in errors:
                st.error(e)
            return
        data = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "created_by": st.session_state["user"]["username"],
            "patient_first": first.strip(), "patient_last": last.strip(),
            "patient_dob": dob.isoformat(), "patient_gender": gender,
            "patient_street": street.strip(), "patient_city": city.strip(),
            "patient_state": state.strip().upper(), "patient_zip": zipc.strip(),
            "member_id": member_id.strip(), "payer": payer_name, "claim_number": claim_number.strip(),
            "dos": dos.isoformat(), "cpt": cpt, "modifiers": modifiers.strip(), "pos": pos,
            "billed": billed, "dx_code": dx.strip().upper(), "group_code": group, "carc": carc,
            "denial_date": denial_date.isoformat(), "deadline": deadline.isoformat(),
            "rationale": rationale.strip(), "notes": notes.strip(),
        }
        cols = list(data)
        cid = x(f"INSERT INTO claims ({','.join(cols)}) VALUES ({','.join(':' + c for c in cols)})", data)
        audit("case_created", f"case {cid}")
        st.success(f"Case #{cid} saved. Open it under **Denial Cases**.")


def case_label(c):
    return f"#{c['id']} · {c['patient_last']}, {c['patient_first']} · DOS {c['dos']} · {c['status']}"


def page_cases():
    st.title("Denial Cases")
    cases = q("SELECT * FROM claims ORDER BY deadline ASC")
    if not cases:
        st.info("No cases yet.")
        return
    f1, f2 = st.columns([1, 2])
    status_f = f1.multiselect("Status", STATUSES)
    search = f2.text_input("Search name / claim # / member ID").strip().lower()
    filtered = [c for c in cases
                if (not status_f or c["status"] in status_f)
                and (not search or search in f"{c['patient_first']} {c['patient_last']} {c['claim_number']} {c['member_id']}".lower())]
    if not filtered:
        st.warning("No matching cases.")
        return
    view = pd.DataFrame(filtered)[["id", "patient_last", "patient_first", "payer", "dos", "cpt", "carc",
                                   "billed", "status", "deadline"]]
    st.dataframe(view, hide_index=True)
    lookup = {c["id"]: c for c in filtered}
    cid = st.selectbox("Open case", list(lookup), format_func=lambda i: case_label(lookup[i]))
    case_workspace(lookup[cid])


def case_workspace(case):
    practice = load_practice()
    payer = get_payer(case["payer"])
    desc, cat = CARC.get(case["carc"], ("Unknown code", "verify"))
    st.markdown(f"### Case #{case['id']} - {case['patient_first']} {case['patient_last']}")
    st.caption(f"{case['payer']} · Claim {case['claim_number']} · {case['group_code']}-{case['carc']}: {desc} · "
               f"Billed {fmt_money(case['billed'])} · Deadline {case['deadline']}")
    kind, msg = CATEGORY_INFO[cat]
    getattr(st, kind)(msg)

    t1, t2, t3, t4 = st.tabs(["Details & status", "Appeal letter", "Call script", "Corrected claim (837P)"])

    with t1:
        with st.form(f"upd_{case['id']}"):
            c1, c2 = st.columns(2)
            status = c1.selectbox("Status", STATUSES,
                                  index=STATUSES.index(case["status"]) if case["status"] in STATUSES else 0)
            level = c2.selectbox("Appeal level", LEVELS,
                                 index=LEVELS.index(case["appeal_level"]) if case["appeal_level"] in LEVELS else 0)
            deadline = c1.date_input("Appeal deadline", value=date.fromisoformat(case["deadline"]))
            recovered = c2.number_input("Recovered amount ($)", min_value=0.0, step=1.0, format="%.2f",
                                        value=float(case["recovered"] or 0))
            rationale = st.text_area("Clinical rationale (used in the letter)", value=case["rationale"] or "")
            notes = st.text_area("Notes / call log", value=case["notes"] or "")
            if st.form_submit_button("Save changes"):
                x("UPDATE claims SET status=?, appeal_level=?, deadline=?, recovered=?, rationale=?, notes=? WHERE id=?",
                  (status, level, deadline.isoformat(), recovered, rationale, notes, case["id"]))
                audit("case_updated", f"case {case['id']} -> {status}")
                st.toast("Saved")
                st.rerun()
        if st.session_state["user"]["role"] == "admin":
            with st.expander("Danger zone"):
                sure = st.checkbox("I understand this permanently deletes the case", key=f"del_{case['id']}")
                if st.button("Delete case", disabled=not sure):
                    x("DELETE FROM claims WHERE id=?", (case["id"],))
                    audit("case_deleted", f"case {case['id']}")
                    st.rerun()

    with t2:
        enclosures = st.multiselect("Enclosures", ENCLOSURE_OPTIONS, default=ENCLOSURE_OPTIONS[:2],
                                    key=f"enc_{case['id']}")
        if not practice:
            st.warning("Practice profile is empty. Fill it in under **Practice Profile** for a complete letter.")
        letter_text = build_appeal_letter(case, payer, practice, enclosures)
        st.code(letter_text, language="text")
        d1, d2 = st.columns(2)
        d1.download_button("Download TXT", letter_text, f"appeal_{case['id']}.txt",
                           on_click=audit, args=("download_appeal_txt", f"case {case['id']}"))
        if HAS_PDF:
            d2.download_button("Download PDF", text_to_pdf(letter_text), f"appeal_{case['id']}.pdf",
                               mime="application/pdf",
                               on_click=audit, args=("download_appeal_pdf", f"case {case['id']}"))
        else:
            d2.caption("Install `reportlab` to enable PDF export.")
        st.caption("Appeals normally go by the payer's portal, fax or mail, not by 837. "
                   "Review the letter and attach the enclosures before sending.")

    with t3:
        script = build_call_script(case, payer, practice)
        st.code(script, language="text")
        st.download_button("Download script", script, f"call_script_{case['id']}.txt")

    with t4:
        st.write("Generates a **corrected claim** file for your clearinghouse (e.g. Office Ally batch upload).")
        missing = [k for k in REQUIRED_EDI_PRACTICE if not practice.get(k)]
        if not payer.get("payer_id"):
            missing.append("payer ID (set in Payers)")
        for k in ["patient_street", "patient_city", "patient_state", "patient_zip"]:
            if not case.get(k):
                missing.append(k)
        if missing:
            st.error("Cannot generate yet. Missing: " + ", ".join(missing))
        else:
            c1, c2 = st.columns(2)
            freq = c1.radio("Claim frequency", ["7", "1"], horizontal=True,
                            format_func=lambda v: "7 - Replacement (corrected claim)" if v == "7" else "1 - Original claim")
            usage = c2.radio("Mode", ["T", "P"], horizontal=True,
                             format_func=lambda v: "Test" if v == "T" else "Production")
            edi = build_837p(case, payer, practice, freq, usage)
            st.code(edi, language="text")
            st.download_button("Download 837P", edi, f"claim_{case['id']}.837",
                               on_click=audit, args=("download_837p", f"case {case['id']}"))
            st.caption("Assumes the patient is the subscriber. Always run a TEST file through your "
                       "clearinghouse first and check their companion guide.")


def page_payers():
    st.title("Payers")
    st.caption("Enter verified payer IDs (from your clearinghouse's payer list) and appeal addresses "
               "(from the payer's provider manual or denial letter). Nothing here is guessed.")
    cols = ["name", "payer_id", "claim_filing", "appeal_days", "appeal_address", "appeal_fax", "portal_url"]
    df = pd.DataFrame(q(f"SELECT {','.join(cols)} FROM payers ORDER BY name"), columns=cols)
    edited = st.data_editor(
        df, num_rows="dynamic",
        column_config={
            "claim_filing": st.column_config.SelectboxColumn("Filing indicator", options=CLAIM_FILING),
            "appeal_days": st.column_config.NumberColumn("Appeal window (days)", min_value=1, default=180),
        },
    )
    if st.button("Save payers", type="primary"):
        edited = edited.fillna("")
        edited = edited[edited["name"].astype(str).str.strip() != ""]
        if edited["name"].duplicated().any():
            st.error("Payer names must be unique.")
            return
        with closing(get_conn()) as c:
            c.execute("DELETE FROM payers")
            for _, r in edited.iterrows():
                c.execute("INSERT INTO payers (name, payer_id, claim_filing, appeal_days, appeal_address, "
                          "appeal_fax, portal_url) VALUES (?,?,?,?,?,?,?)",
                          (str(r["name"]).strip(), str(r["payer_id"]).strip(), r["claim_filing"] or "CI",
                           int(r["appeal_days"] or 180), r["appeal_address"], r["appeal_fax"], r["portal_url"]))
            c.commit()
        audit("payers_saved")
        st.success("Saved.")


def page_practice():
    st.title("Practice Profile")
    st.caption("Used on letters and claim files. Leave blank what you don't have; nothing is pre-filled.")
    p = load_practice()
    if st.session_state["user"]["role"] != "admin":
        st.info("Only administrators can edit the practice profile.")
        st.json({k: v for k, v in p.items()})
        return
    with st.form("practice"):
        st.subheader("Billing provider")
        c1, c2, c3 = st.columns(3)
        billing_name = c1.text_input("Practice / entity name", p.get("billing_name", ""))
        billing_npi = c2.text_input("Billing NPI (10 digits)", p.get("billing_npi", ""))
        tax_id = c3.text_input("Tax ID (9 digits)", p.get("tax_id", ""))
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        billing_street = c1.text_input("Street address", p.get("billing_street", ""))
        billing_city = c2.text_input("City", p.get("billing_city", ""))
        billing_state = c3.text_input("State", p.get("billing_state", ""), max_chars=2)
        billing_zip = c4.text_input("ZIP", p.get("billing_zip", ""))
        phone = st.text_input("Phone (10 digits)", p.get("phone", ""))

        st.subheader("Rendering provider")
        c1, c2, c3 = st.columns(3)
        rendering_first = c1.text_input("First name", p.get("rendering_first", ""))
        rendering_last = c2.text_input("Last name", p.get("rendering_last", ""))
        rendering_creds = c3.text_input("Credentials", p.get("rendering_creds", ""), placeholder="LCSW")
        c1, c2 = st.columns(2)
        rendering_npi = c1.text_input("Rendering NPI", p.get("rendering_npi", ""))
        taxonomy = c2.text_input("Taxonomy code", p.get("taxonomy", ""))

        st.subheader("Clearinghouse (from your clearinghouse enrollment)")
        c1, c2 = st.columns(2)
        submitter_id = c1.text_input("Submitter ID (ISA06 / ETIN)", p.get("submitter_id", ""))
        receiver_id = c2.text_input("Receiver ID (ISA08)", p.get("receiver_id", ""))

        if st.form_submit_button("Save profile"):
            errors = []
            for label, npi in [("Billing NPI", billing_npi), ("Rendering NPI", rendering_npi)]:
                if npi and not valid_npi(npi.strip()):
                    errors.append(f"{label} is not a valid NPI.")
            if tax_id and len(re.sub(r"\D", "", tax_id)) != 9:
                errors.append("Tax ID must be 9 digits.")
            if phone and len(re.sub(r"\D", "", phone)) != 10:
                errors.append("Phone must be 10 digits.")
            if billing_state and not re.fullmatch(r"[A-Za-z]{2}", billing_state):
                errors.append("State must be 2 letters.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                save_practice({
                    "billing_name": billing_name.strip(), "billing_npi": billing_npi.strip(),
                    "tax_id": tax_id.strip(), "billing_street": billing_street.strip(),
                    "billing_city": billing_city.strip(), "billing_state": billing_state.strip().upper(),
                    "billing_zip": billing_zip.strip(), "phone": phone.strip(),
                    "rendering_first": rendering_first.strip(), "rendering_last": rendering_last.strip(),
                    "rendering_creds": rendering_creds.strip(), "rendering_npi": rendering_npi.strip(),
                    "taxonomy": taxonomy.strip(), "submitter_id": submitter_id.strip(),
                    "receiver_id": receiver_id.strip(),
                })
                audit("practice_saved")
                st.success("Profile saved.")


def page_users():
    st.title("Users")
    users = q("SELECT id, username, full_name, role, active, locked_until, created_at FROM users ORDER BY username")
    st.dataframe(pd.DataFrame(users), hide_index=True)

    st.subheader("Add user")
    with st.form("add_user", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        username = c2.text_input("Username")
        c1, c2 = st.columns(2)
        pw = c1.text_input("Temporary password", type="password", help=PW_HELP)
        role = c2.selectbox("Role", ["biller", "admin"])
        if st.form_submit_button("Create user"):
            err = "Fill in all fields." if not (name.strip() and username.strip() and pw) else password_error(pw)
            if err:
                st.error(err)
            else:
                try:
                    create_user(username, name, pw, role)
                    audit("user_created", f"{username.strip().lower()} ({role})")
                    st.success("User created.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That username already exists.")

    st.subheader("Manage user")
    me = st.session_state["user"]["id"]
    target = st.selectbox("User", users, format_func=lambda u: f"{u['username']} ({u['role']})")
    c1, c2 = st.columns(2)
    with c1:
        new_pw = st.text_input("New password", type="password", key="reset_pw")
        if st.button("Reset password"):
            err = password_error(new_pw)
            if err:
                st.error(err)
            else:
                set_password(target["id"], new_pw)
                audit("password_reset", target["username"])
                st.success("Password reset.")
    with c2:
        if target["id"] == me:
            st.caption("You cannot disable your own account.")
        else:
            label = "Disable account" if target["active"] else "Enable account"
            if st.button(label):
                x("UPDATE users SET active=? WHERE id=?", (0 if target["active"] else 1, target["id"]))
                audit("user_toggled", target["username"])
                st.rerun()


def page_audit():
    st.title("Audit Log")
    df = pd.DataFrame(q("SELECT ts, username, action, detail FROM audit ORDER BY id DESC LIMIT 1000"))
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "audit_log.csv")


# ----------------------------------------------------------------------------
# APP ENTRY
# ----------------------------------------------------------------------------
init_db()

if not enforce_session():
    login_screen()
    st.stop()

user = st.session_state["user"]
PAGES = {
    "Dashboard": page_dashboard,
    "Denial Cases": page_cases,
    "New Case": page_new_case,
    "Payers": page_payers,
    "Practice Profile": page_practice,
}
if user["role"] == "admin":
    PAGES["Users"] = page_users
    PAGES["Audit Log"] = page_audit

with st.sidebar:
    st.markdown("## 🧠 MindBill Pro")
    st.write(f"**{user['full_name']}**")
    st.caption(f"{user['role'].title()} · auto-logout after {SESSION_TIMEOUT_MIN} min")
    choice = st.radio("Navigate", list(PAGES), label_visibility="collapsed")
    st.markdown("---")
    with st.expander("Change my password"):
        with st.form("chpw", clear_on_submit=True):
            cur = st.text_input("Current password", type="password")
            new = st.text_input("New password", type="password")
            if st.form_submit_button("Update"):
                row = q("SELECT * FROM users WHERE id=?", (user["id"],))[0]
                if not hmac.compare_digest(hash_pw(cur, row["salt"]), row["pw_hash"]):
                    st.error("Current password is wrong.")
                elif password_error(new):
                    st.error(password_error(new))
                else:
                    set_password(user["id"], new)
                    audit("password_changed")
                    st.success("Password updated.")
    if st.button("Log out"):
        audit("logout")
        st.session_state.clear()
        st.rerun()

PAGES[choice]()
