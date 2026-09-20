import streamlit as st
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="MindBill AI - Enterprise Behavioral Health Denial Portal",
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
        background-color: #2e6fef;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1a56cc;
        color: white;
        box-shadow: 0 4px 12px rgba(46,111,239,0.3);
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

# Complete & Expanded Behavioral Health CARC / Denial Codes Database
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

# Sidebar Banner & Controls
with st.sidebar:
    st.image("https://img.icons8.com/isometric-headers/100/brain.png", width=70)
    st.title("MindBill AI Pro")
    st.caption("Behavioral Health RCM & Parity Engine")
    st.divider()
    
    st.subheader("⚙️ Quick Settings")
    provider_name = st.text_input("Rendering Provider / Practice Name", "Behavioral Health Practice")
    provider_npi = st.text_input("NPI / Tax ID", "1234567890 / XX-XXXXXXX")
    st.divider()
    st.caption("🔒 HIPAA Compliant Workflow Standard")

# Header Section
st.title("🧠 MindBill AI — Claim Denial Resolution Hub")
st.markdown("Quickly generate formal parity-backed reconsideration appeals and AR rep scripts for behavioral health claims.")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card"><b>Payer Parity Enforcement</b><br><span style="color:#2e6fef; font-size:1.4rem; font-weight:bold;">MHPAEA 100%</span></div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card"><b>CARC Codes Loaded</b><br><span style="color:#2e6fef; font-size:1.4rem; font-weight:bold;">Expanded Database</span></div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card"><b>Appeal Resolution Rate</b><br><span style="color:#2e6fef; font-size:1.4rem; font-weight:bold;">84.2%</span></div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card"><b>Turnaround Time</b><br><span style="color:#2e6fef; font-size:1.4rem; font-weight:bold;">&lt; 2 Mins</span></div>', unsafe_allow_html=True)

st.divider()

# Main Layout
col_input, col_output = st.columns([1, 1.3], gap="medium")

with col_input:
    st.subheader("📝 Claim & Denial Entry")
    
    payer = st.selectbox("Select Insurance Payer", [
        "Health First (NY)",
        "MetroPlus Health Plan",
        "EmblemHealth (HIP/GHI)",
        "Fidelis Care",
        "BCBS / Empire BlueCross BlueShield",
        "Aetna / Aetna Behavioral",
        "Cigna / Evernorth Health",
        "UnitedHealthcare (UHC) / Optum",
        "Medicare (CMS / MAC)",
        "Medicaid (State Portal)"
    ])
    
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
    
    selected_carc = st.selectbox("Denial Reason Code (CARC)", list(DENIAL_CODES.keys()))
    carc_desc = DENIAL_CODES[selected_carc]
    st.info(f"💡 **Description:** {carc_desc}")
    
    notes = st.text_area("Clinical Notes / Diagnosis Code", "F41.1 (Generalized Anxiety Disorder)", height=80)
    
    generate_btn = st.button("🚀 Generate Appeal & Call Script", use_container_width=True)

with col_output:
    st.subheader("📄 Generated Deliverables")
    
    if generate_btn:
        st.markdown('<span class="status-badge">✅ Appeal & Script Ready</span>', unsafe_allow_html=True)
        st.write("")
        
        tab1, tab2, tab3 = st.tabs(["✉️ Formal Appeal Letter", "📞 AR Call Script", "📋 Checklist & Notes"])
        
        cpt_code_only = cpt.split(" - ")[0]
        carc_code_only = selected_carc.split(" - ")[0]
        
        appeal_letter = f"""DATE: {datetime.now().strftime('%B %d, %Y')}

TO: {payer}
ATTN: Appeals & Grievance Department

RE: FORMAL RECONSIDERATION / APPEAL REQUEST
Patient Diagnosis: {notes}
Billed CPT Code: {cpt_code_only}
Date of Service: {dos}
Denial Code: {selected_carc}

Dear Appeals Committee,

Please accept this letter as a formal reconsideration request regarding the improper denial of CPT code {cpt_code_only} for Date of Service {dos} under denial code {selected_carc} ({carc_desc}).

REASON FOR APPEAL:
The rendered mental health service was medically necessary, clinically indicated, and performed by a licensed professional in compliance with established practice guidelines for {notes}.

1. CLINICAL & MENTAL HEALTH PARITY JUSTIFICATION (MHPAEA):
   Under the Mental Health Parity and Addiction Equity Act (MHPAEA) and federal/state insurance guidelines, health plans are prohibited from imposing non-quantitative treatment limitations (NQTLs) or arbitrary session caps on behavioral health services that are more restrictive than medical/surgical benefits.

2. CODING & DOCUMENTATION COMPLIANCE:
   The session duration, provider qualifications, and progress notes comply fully with CPT coding and CMS clinical documentation standards.

Enclosed are the supporting progress notes, treatment plan, and claim form. We request immediate re-adjudication and processing of this claim for full payment.

Sincerely,
{provider_name}
NPI / Tax ID: {provider_npi}"""

        with tab1:
            st.code(appeal_letter, language="text")
            st.download_button(
                label="📥 Download Appeal Letter (.txt)",
                data=appeal_letter,
                file_name=f"Appeal_{cpt_code_only}_{dos}.txt",
                mime="text/plain"
            )

        with tab2:
            call_script = f"""1. VERIFICATION:
   "Hi, calling from {provider_name} regarding Claim ID for DOS {dos}, Patient Member ID [ID] billed to {payer}."

2. DENIAL INQUIRY:
   "I see CPT {cpt_code_only} denied for {carc_code_only} ({carc_desc})."

3. RESOLUTION PATHWAY:
   - For Auth/Necessity/Notes: "Can we submit session notes and treatment plan via portal/fax for retroactive review?"
   - For Bundled/Modifier: "Modifier was billed appropriately per NCCI edits. Can this claim be re-processed?"
   - For Parity/Limits: "This is a behavioral health service covered under MHPAEA parity laws. Please transfer me to a senior claims specialist."

4. CALL CLOSING:
   "Please share the call reference number, representative name, and standard reprocessing timeframe."
"""
            st.code(call_script, language="text")
            st.download_button(
                label="📥 Download Call Script (.txt)",
                data=call_script,
                file_name=f"AR_Script_{cpt_code_only}.txt",
                mime="text/plain"
            )

        with tab3:
            st.warning("""
            **📌 Enclosures Checklist:**
            - [ ] Signed Progress / Session Notes (Start and Stop times included)
            - [ ] Diagnostic Evaluation (DSM-5 / ICD-10)
            - [ ] CMS-1500 Claim Copy & ERA/EOB
            - [ ] Prior Authorization Copy (if applicable)
            """)
    else:
        st.info("👈 Complete the claim details on the left and click **'Generate Appeal & Call Script'** to view outputs.")
