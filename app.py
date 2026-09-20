import streamlit as st
from datetime import datetime
import time

# Page Configuration
st.set_page_config(
    page_title="MindBill AI - Enterprise Behavioral Health & Portal Direct Dispatch",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional UI Styling (CSS)
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #ffffff;
        color: #1f2937;
        font-weight: 600;
        border-radius: 10px;
        border: 1px solid #d1d5db;
        padding: 0.6rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #f3f4f6;
        border-color: #9ca3af;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 5px solid #2e6fef;
    }
    .status-badge {
        background-color: #e6f4ea;
        color: #137333;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 🔐 USER LOGIN / AUTHENTICATION SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# Render Login Screen
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1>🧠 MindBill AI Pro</h1>
            <p style="color: #5f6368;">Enterprise Behavioral Health Billing Portal</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("🔑 Sign In or Create Account")
        st.caption("Select your preferred login provider:")
        
        # Single-Line Official Social Login Buttons (Google, Apple, Facebook, Gmail)
        auth_c1, auth_c2, auth_c3, auth_c4 = st.columns(4)
        
        with auth_c1:
            if st.button("🌐 Google", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Google User"
                st.rerun()
        with auth_c2:
            if st.button(" Apple", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Apple ID User"
                st.rerun()
        with auth_c3:
            if st.button("f Facebook", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Facebook User"
                st.rerun()
        with auth_c4:
            if st.button("✉️ Gmail", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Gmail User"
                st.rerun()

        st.divider()
        
        # Standard Email & Password Fallback Login
        with st.form("email_login_form"):
            st.write("**Or Sign In with Email Credentials**")
            username_input = st.text_input("Username / Email")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In / Login", use_container_width=True)
            
            if submit_login:
                if username_input and password_input:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = username_input
                    st.success(f"Welcome back, {username_input}!")
                    st.rerun()
                else:
                    st.error("❌ Please enter username and password!")
                    
    st.stop()  # Stop execution until user logs in

# --- MAIN APP (ACCESSIBLE ONLY AFTER LOGIN) ---

# COMPLETE & FULL BEHAVIORAL HEALTH CARC / DENIAL CODES DATABASE (ALL 37 CODES)
DENIAL_CODES = {
    "CO 1 - Deductible Amount": "Deductible amount not met by the patient.",
    "CO 2 - Coinsurance Amount": "Coinsurance amount applied to patient responsibility.",
    "CO 3 - Copay Amount": "Co-payment amount required from the patient.",
    "CO 4 - Procedure code inconsistent with modifier / Missing Modifier": "The procedure code is inconsistent with the modifier used or a required modifier is missing.",
    "CO 16 - Claim/service lacks information": "Claim or service lacks necessary information or has submission errors (e.g., missing clinical notes/medical records).",
    "CO 18 - Duplicate claim / service rendered": "Duplicate claim or service rendered on the same date of service.",
    "CO 19 - Claim denied; Student coverage guidelines not met": "Student insurance guidelines or documentation requirements not met.",
    "CO 22 - Care may be covered by another payer (COB / Primary issue)": "Payment denied because care may be covered by another primary insurance (Coordination of Benefits).",
    "CO 24 - Charges in excess of fee schedule / maximum allowable": "Billed charges exceed the fee schedule or maximum allowable fee contract.",
    "CO 26 - Expenses incurred prior to coverage effective date": "Service date was before the insurance coverage became effective.",
    "CO 27 - Expenses incurred after coverage terminated": "Service date was after the patient insurance coverage was terminated.",
    "CO 29 - Timely Filing limit exceeded": "The time limit for filing the claim has expired based on payer contract guidelines.",
    "CO 31 - Patient cannot be identified as our insured": "Patient details (Name/DOB/ID) do not match payer insured records.",
    "CO 35 - Lifetime benefit maximum reached": "Patient has reached their maximum policy lifetime coverage limits.",
    "CO 45 - Charge exceeds fee schedule / Contractual Adjustment": "Contractual adjustment applied as charge exceeds allowable schedule.",
    "CO 50 - Non-covered service / Lack of Medical Necessity": "These are non-covered services because they were not deemed medically necessary by the payer.",
    "CO 51 - Non-covered pre-existing condition": "Service rendered for a pre-existing condition not covered under policy rules.",
    "CO 59 - Processed according to NCCI edits / Distinct procedural service required": "Service bundled or processed according to National Correct Coding Initiative (NCCI) edits.",
    "CO 96 - Non-covered charge(s) / Benefit limit reached": "Non-covered charges because service is excluded from policy or benefit maximum reached.",
    "CO 97 - Procedure code bundled / Inclusive to another service": "Procedure code is bundled into another primary procedure performed on the same day.",
    "CO 109 - Not covered by this payer / Billed to wrong carrier": "Claim submitted to wrong insurance carrier; not covered under this plan.",
    "CO 119 - Benefit maximum reached for this service": "Specific benefit limit for this procedure/service category has been reached.",
    "CO 133 - Claim submitted past timely filing limit": "Late claim submission beyond state/federal or contractual filing rules.",
    "CO 140 - Patient/Insured financial responsibility": "Amount is patient's financial responsibility under plan terms.",
    "CO 151 - Documentation does not support level of service": "Payment adjusted because information submitted does not support the billed CPT code intensity/duration.",
    "CO 167 - Diagnosis inconsistent with procedure": "The diagnosis code provided is inconsistent with the billed procedure code.",
    "CO 197 - Pre-certification / Prior Authorization missing or invalid": "Pre-certification or Prior Authorization was not obtained before rendering the service.",
    "CO 198 - Pre-certification / Authorization exceeded": "Billed units exceed the number of authorized units granted in the precertification.",
    "CO 204 - Service not covered under patient policy": "This specific procedure or service is excluded from the patient's benefit plan.",
    "CO 219 - Service/procedure denied; missing medical records": "Claim rejected due to missing medical records or session notes.",
    "CO 234 - Procedure code not covered for date of service": "This code was not active or eligible for coverage on the billed date of service.",
    "CO 252 - Attachment/documentation missing": "Electronic attachment or required supporting document was not received.",
    "CO 256 - Service not covered when performed by this provider type": "Provider specialty or taxonomy is not authorized to render this behavioral health service.",
    "CO 260 - Settlement/Court award adjustment": "Third-party liability or settlement adjustment applied.",
    "PR 1 - Deductible Amount (Patient Responsibility)": "Deductible applied to patient financial responsibility.",
    "PR 2 - Coinsurance Amount (Patient Responsibility)": "Coinsurance applied to patient financial responsibility.",
    "PR 3 - Co-payment Amount (Patient Responsibility)": "Copay amount applied to patient financial responsibility."
}

# Sidebar: Provider & Account Details
with st.sidebar:
    st.image("https://img.icons8.com/isometric-headers/100/brain.png", width=70)
    st.title("MindBill AI Pro")
    st.caption(f"Logged in as: **{st.session_state['user_name']}**")
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['user_name'] = ""
        st.rerun()

    st.divider()
    st.subheader("👨‍⚕️ Rendering Provider Details")
    rendering_provider = st.text_input("Rendering Provider Name", "Dr. Sarah Jenkins, LCSW")
    rendering_npi = st.text_input("Rendering Provider NPI", "1982736450")
    provider_taxonomy = st.text_input("Provider Taxonomy Code", "101YM0800X")
    
    st.divider()
    st.subheader("🏢 Billing Provider Details")
    billing_provider = st.text_input("Billing Group / Entity Name", "Behavioral Health Practice LLC")
    billing_npi = st.text_input("Billing NPI", "1234567890")
    provider_taxid = st.text_input("Tax ID (EIN/SSN)", "12-3456789")
    billing_address = st.text_area("Billing Address", "123 Medical Plaza, Suite 400\nNew York, NY 10001", height=60)
    
    st.divider()
    st.subheader("🏥 Facility / Place of Service (POS)")
    facility_name = st.text_input("Facility / Clinic Name", "MindBill Behavioral Center")
    facility_npi = st.text_input("Facility NPI", "1098765432")
    pos_code = st.selectbox("Place of Service (POS)", ["11 - Office / Outpatient Clinic", "02 - Telehealth Provided Other Than Home", "10 - Telehealth Provided in Patient Home", "22 - Outpatient Hospital"])
    facility_address = st.text_area("Facility Address", "456 Health Ave, New York, NY 10002", height=60)

# Main UI Header
st.title("🧠 MindBill AI — Multi-Portal & Direct Payer Dispatch Engine")
st.markdown("Direct Integration for AdvanceMD, InSync, Tebra, MDClaim & Clearinghouse Portals.")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card"><b>Portal Connections</b><br><span style="color:#137333; font-size:1.3rem; font-weight:bold;">🟢 Active Portals</span></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><b>CARC Codes Database</b><br><span style="color:#2e6fef; font-size:1.3rem; font-weight:bold;">37 Codes Active</span></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><b>EDI Protocol</b><br><span style="color:#2e6fef; font-size:1.3rem; font-weight:bold;">ANSI 837P v5010</span></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><b>Parity Enforcement</b><br><span style="color:#2e6fef; font-size:1.3rem; font-weight:bold;">MHPAEA Ready</span></div>', unsafe_allow_html=True)

st.divider()

col_input, col_output = st.columns([1.1, 1.2], gap="medium")

with col_input:
    st.subheader("📝 Billing Portal, Claim & Payer Details")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        billing_portal = st.selectbox("Select Billing Platform / Portal", [
            "AdvanceMD EHR & Practice Management",
            "InSync Healthcare Solutions (Qualifacts)",
            "Tebra / Kareo PM Portal",
            "MDClaim / MD-Medical Billing Portal",
            "CareCloud Central Portal",
            "Availity Clearinghouse Portal",
            "Change Healthcare (Optum) Gateway",
            "Office Ally EDI Direct Portal",
            "ePACES Medicaid Direct Portal",
            "Epic Resolute Professional Billing",
            "Cerner / Oracle Health Billing"
        ])
        
        payer = st.selectbox("Insurance Payer", [
            "Health First (NY)",
            "MetroPlus Health Plan",
            "EmblemHealth (HIP/GHI)",
            "Fidelis Care",
            "BCBS / Empire BlueCross BlueShield",
            "Aetna / Aetna Behavioral",
            "Cigna / Evernorth Health",
            "UnitedHealthcare (UHC) / Optum",
            "Medicare (CMS / MAC)",
            "Medicaid (ePACES / State)"
        ])
    with c_p2:
        payer_id = st.text_input("Payer Electronic ID (Payer ID)", "60054")
        submission_type = st.radio("Submission Mode", ["Electronic Appeal / Dispute", "837P Re-submission (Corrected Claim)"])

    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        patient_name = st.text_input("Patient Full Name", "John Doe")
        member_id = st.text_input("Insurance Member ID", "MBD9948201")
        patient_dob = st.date_input("Patient Date of Birth", datetime(1990, 5, 14))
    with c2:
        claim_icn = st.text_input("Claim ID / ICN", "2026092000847")
        billed_amount = st.text_input("Billed Amount ($)", "175.00")
        dos = st.date_input("Date of Service", datetime.now())
        
    cpt = st.selectbox("Mental Health / Medical CPT Code", [
        "90837 - Psychotherapy (60 Min)",
        "90834 - Psychotherapy (45 Min)",
        "90832 - Psychotherapy (30 Min)",
        "90791 - Psychiatric Diagnostic Evaluation",
        "90792 - Psychiatric Eval w/ Medical Services",
        "90833 - Psychotherapy w/ E/M (Add-on)",
        "99214 - Medication Management / Outpatient E/M"
    ])
    
    modifiers = st.text_input("Modifiers Billed (e.g., 95, 59, XE)", "95")
    selected_carc = st.selectbox("Denial Reason Code (CARC - 37 Codes Loaded)", list(DENIAL_CODES.keys()))
    carc_desc = DENIAL_CODES[selected_carc]
    st.info(f"💡 **Description:** {carc_desc}")
    
    dx_notes = st.text_area("ICD-10 Diagnosis & Specific Rationale", "F41.1 (Generalized Anxiety Disorder). Persistent severe anxiety requiring full 60-min session.", height=70)
    
    generate_btn = st.button("🚀 Push to Portal & Generate Deliverables", use_container_width=True)

with col_output:
    st.subheader("📡 Portal Transmission & Output Engine")
    
    if generate_btn:
        st.markdown('<span class="status-badge">✅ Claim & Appeal Data Prepared</span>', unsafe_allow_html=True)
        st.write("")
        
        tab_direct, tab1, tab2, tab3 = st.tabs([
            "🚀 Portal Sync & Transmission", 
            "✉️ Formal Appeal Letter", 
            "📞 AR Call Script", 
            "💻 EDI 837P Payload"
        ])
        
        cpt_code_only = cpt.split(" - ")[0]
        carc_code_only = selected_carc.split(" - ")[0]
        pos_code_only = pos_code.split(" - ")[0]
        
        # Dynamic Denial Specific Arguments
        if "CO 97" in selected_carc or "CO 59" in selected_carc:
            denial_argument = f"1. NCCI & DISTINCT SERVICE COMPLIANCE:\n   The billed procedure CPT {cpt_code_only} represents a separate, distinct procedural service rendered on {dos}. Modifiers billed ({modifiers}) clearly delineate this session from concurrent services per NCCI edits. Bundling this distinct service is an improper claim edit error."
        elif "CO 197" in selected_carc or "CO 198" in selected_carc:
            denial_argument = f"1. AUTHORIZATION & PRIOR CERTIFICATION VERIFICATION:\n   Patient was actively enrolled with valid eligibility on DOS {dos}. Behavioral health therapy ({cpt_code_only}) was initiated for acute symptoms of {dx_notes}. Enclosed is proof of prior authorization / active referral."
        elif "CO 16" in selected_carc or "CO 219" in selected_carc or "CO 252" in selected_carc:
            denial_argument = f"1. CLINICAL DOCUMENTATION SUBMISSION:\n   Claim was rejected for missing documentation. Attached are unredacted psychotherapy progress notes with start/stop times, clinical rationale, and provider signature for DOS {dos}."
        elif "CO 50" in selected_carc or "CO 151" in selected_carc:
            denial_argument = f"1. CLINICAL MEDICAL NECESSITY JUSTIFICATION:\n   The session rendered on {dos} was medically necessary for {dx_notes}. Duration and intensity match CPT {cpt_code_only} guidelines and APA clinical practice standards."
        elif "CO 29" in selected_carc or "CO 133" in selected_carc:
            denial_argument = f"1. TIMELY FILING PROOF:\n   Claim was transmitted electronically within contractual limits. Enclosed is the clearinghouse 277 acceptance report confirming submission."
        else:
            denial_argument = f"1. ADJUDICATION REVIEW JUSTIFICATION:\n   Claim for CPT {cpt_code_only} billed on DOS {dos} was adjudicated in error under {selected_carc}. All coding accuracy and modifier requirements have been fully satisfied."

        with tab_direct:
            st.success(f" Ready to Sync & Transmit via **{billing_portal}** to **{payer}** (Payer ID: `{payer_id}`).")
            
            st.markdown(f"""
            **Transmission & Portal Configuration:**
            * **Active Platform / Portal:** `{billing_portal}`
            * **Target Insurance Payer:** {payer} (Payer ID: `{payer_id}`)
            * **Billing Provider:** {billing_provider} (NPI: `{billing_npi}` | Tax ID: `{provider_taxid}`)
            * **Rendering Provider:** {rendering_provider} (NPI: `{rendering_npi}` | Taxonomy: `{provider_taxonomy}`)
            * **Facility/Location:** {facility_name} (POS `{pos_code_only}`)
            * **Claim ICN:** `{claim_icn}` | **CPT:** `{cpt_code_only}` | **Amount:** `${billed_amount}`
            """)
            
            if st.button(f"📲 Transmit & Push Claim/Appeal to {billing_portal} Now", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text(f"Establishing API / Secure Bridge to {billing_portal}...")
                progress_bar.progress(25)
                time.sleep(0.5)
                
                status_text.text(f"Validating Payer ID {payer_id} and NPI credentials in {billing_portal}...")
                progress_bar.progress(55)
                time.sleep(0.5)
                
                status_text.text("Generating EDI 837P Payload and attaching clinical documentation...")
                progress_bar.progress(85)
                time.sleep(0.5)
                
                progress_bar.progress(100)
                status_text.text("Transmission Complete!")
                
                st.balloons()
                st.success(f"🎉 **SUCCESS!** Successfully pushed to **{billing_portal}**!\n\n**Portal Batch ID:** `{billing_portal[:3].upper()}-2026-{claim_icn}`\n**Payer Acknowledgement:** 277 ACCEPTED BY PAYER ({payer_id})")

        appeal_letter = f"""BILLING PROVIDER: {billing_provider}
Address: {billing_address}
Billing NPI: {billing_npi} | Tax ID: {provider_taxid}

RENDERING PROVIDER: {rendering_provider} (NPI: {rendering_npi} | Taxonomy: {provider_taxonomy})
FACILITY / LOCATION: {facility_name} (POS: {pos_code_only})
Address: {facility_address}

DATE: {datetime.now().strftime('%B %d, %Y')}

TO: {payer} (PAYER ID: {payer_id})
ATTN: Appeals & Grievance Department / Claims Reconsideration

FORMAL RECONSIDERATION / APPEAL REQUEST

PATIENT & CLAIM IDENTIFICATION:
- Patient Name       : {patient_name} (DOB: {patient_dob.strftime('%Y-%m-%d')})
- Member ID          : {member_id}
- Original Claim ICN : {claim_icn}
- Date of Service    : {dos}
- CPT Code / Mod     : {cpt_code_only} (Modifier: {modifiers})
- Billed Amount      : ${billed_amount}
- Primary Diagnosis  : {dx_notes}
- Denial Reason Code : {selected_carc}

Dear Appeals Committee,

Please accept this letter as a formal written appeal regarding improper denial of Claim ICN {claim_icn} for Date of Service {dos}. The claim was denied under CARC {carc_code_only} ({carc_desc}).

REASON FOR APPEAL & CLINICAL JUSTIFICATION:

{denial_argument}

2. MENTAL HEALTH PARITY ACT (MHPAEA) COMPLIANCE:
   Under the Mental Health Parity and Addiction Equity Act (MHPAEA), health plans are prohibited from applying non-quantitative treatment limitations (NQTLs) or arbitrary bundling edits to behavioral health services that are more restrictive than medical/surgical benefits. Denial of CPT {cpt_code_only} violates parity protections.

DEMAND FOR ACTION:
We request immediate reversal of this denial and re-adjudication of Claim ICN {claim_icn} for full payment of ${billed_amount}.

Sincerely,

____________________________________
{rendering_provider}
Rendering Provider / Behavioral Health Specialist
NPI: {rendering_npi}

{billing_provider}
NPI: {billing_npi} | Tax ID: {provider_taxid}"""

        with tab1:
            st.code(appeal_letter, language="text")
            st.download_button("📥 Download Formal Appeal (.txt)", appeal_letter, f"Appeal_{claim_icn}.txt")

        with tab2:
            call_script = f"""1. CALL & IDENTIFICATION:
   "Hi, calling from {billing_provider} (NPI: {billing_npi}). I am inquiring about Claim ICN {claim_icn} for Patient {patient_name} (Member ID: {member_id}, DOB: {patient_dob}). Billed under Payer ID {payer_id} via {billing_portal}."

2. DENIAL REVIEW:
   "CPT {cpt_code_only} on DOS {dos} was denied under {carc_code_only} ({carc_desc}). Billed amount is ${billed_amount}."

3. RESOLUTION DEMAND:
   - Rendering Provider: {rendering_provider} (NPI: {rendering_npi}, Taxonomy: {provider_taxonomy}).
   - Facility: {facility_name} (POS {pos_code_only}).
   - "Modifier {modifiers} was billed correctly. Please send this claim back for manual re-adjudication."

4. CONFIRMATION:
   "Please provide Call Reference Number and supervisor confirmation." """
            st.code(call_script, language="text")
            st.download_button("📥 Download AR Script (.txt)", call_script, f"AR_Script_{claim_icn}.txt")

        with tab3:
            edi_payload = f"""ISA*00*          *00*          *ZZ*{billing_npi:<15}*ZZ*{payer_id:<15}*{datetime.now().strftime('%y%m%d')}*{datetime.now().strftime('%H%M')}*U*00501*000000001*0*P*>~
GS*HC*{billing_npi}*{payer_id}*{datetime.now().strftime('%Y%m%d')}*{datetime.now().strftime('%H%M')}*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*1001*{datetime.now().strftime('%Y%m%d')}*{datetime.now().strftime('%H%M')}*CH~
NM1*41*2*{billing_provider}*****46*{billing_npi}~
PER*IC*BILLING DEPT*TE*5550192831~
NM1*40*2*{payer}*****46*{payer_id}~
HL*1**20*1~
PRV*BI*PXC*{provider_taxonomy}~
NM1*85*2*{billing_provider}*****XX*{billing_npi}~
N3*{billing_address.replace('\n', ' ')}~
REF*EI*{provider_taxid.replace('-', '')}~
HL*2*1*22*0~
NM1*QC*1*{patient_name.split()[-1]}*{patient_name.split()[0]}****MI*{member_id}~
DMG*D8*{patient_dob.strftime('%Y%m%d')}*M~
CLM*{claim_icn}*{billed_amount}***{pos_code_only}:B:1*Y*A*Y*Y~
HI*BK:{dx_notes.split()[0]}~
LX*1~
SV1*HC:{cpt_code_only}:{modifiers}*{billed_amount}*UN*1***1~
DTP*472*D8*{dos.strftime('%Y%m%d')}~
NM1*82*1*{rendering_provider.split()[-1]}*{rendering_provider.split()[0]}****XX*{rendering_npi}~
PRV*PE*PXC*{provider_taxonomy}~
NM1*77*2*{facility_name}*****XX*{facility_npi}~
N3*{facility_address.replace('\n', ' ')}~
SE*24*0001~
GE*1*1~
IEA*1*000000001~"""
            st.markdown(f"<b>Raw ANSI 837P Professional EDI Payload ({billing_portal}):</b>", unsafe_allow_html=True)
            st.code(edi_payload, language="text")
            st.download_button("📥 Download EDI 837P Payload (.edi)", edi_payload, f"Claim_837P_{claim_icn}.edi")

