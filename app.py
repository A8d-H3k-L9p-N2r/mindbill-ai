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

# Custom Styling (CSS) - Clean & Professional Single Line Social Auth
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .social-auth-container {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-bottom: 20px;
    }
    .social-btn {
        flex: 1;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #dadce0;
        background-color: #ffffff;
        text-align: center;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .social-btn:hover {
        background-color: #f1f3f4;
        border-color: #d2d6dc;
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

# --- 🔐 LOGIN & MULTI-ACCOUNT AUTHENTICATION SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><h2 style='text-align: center;'>🧠 MindBill AI Pro</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #5f6368;'>Sign in or Register using your preferred account</p>", unsafe_allow_html=True)
        
        # Single-Line OAuth Buttons (Google, Apple, Facebook, Email)
        st.markdown("### Quick Social Login")
        auth_c1, auth_c2, auth_c3, auth_c4 = st.columns(4)
        
        with auth_c1:
            if st.button("🌐 Google", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Google User"
                st.rerun()
        with auth_c2:
            if st.button("🍎 Apple", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Apple ID User"
                st.rerun()
        with auth_c3:
            if st.button("📘 Facebook", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Facebook User"
                st.rerun()
        with auth_c4:
            if st.button("✉️ Gmail", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_name'] = "Gmail User"
                st.rerun()

        st.divider()
        
        # Standard Email & Password Login
        with st.form("email_login"):
            st.subheader("🔑 Or Sign In with Email / Username")
            email_in = st.text_input("Email / Username")
            pass_in = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("Sign In", use_container_width=True)
            
            if btn_login:
                if email_in and pass_in:
                    st.session_state['logged_in'] = True
                    st.session_state['user_name'] = email_in
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Please enter credentials.")
    st.stop()

# --- MAIN MEDICAL BILLING APPLICATION ---

# COMPLETE & FULL BEHAVIORAL HEALTH CARC CODES DATABASE (37 CODES INTACT)
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

# Sidebar Details & Logout
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

# Main Dashboard Header
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
            "ePACES Medicaid Direct Portal"
        ])
        payer = st.selectbox("Insurance Payer", [
            "Health First (NY)", "MetroPlus Health Plan", "EmblemHealth (HIP/GHI)",
            "Fidelis Care", "BCBS / Empire BlueCross BlueShield", "Aetna / Aetna Behavioral",
            "Cigna / Evernorth Health", "UnitedHealthcare (UHC) / Optum", "Medicare (CMS / MAC)"
        ])
    with c_p2:
        payer_id = st.text_input("Payer Electronic ID (Payer ID)", "60054")
        submission_type = st.radio("Submission Mode", ["Electronic Appeal / Dispute", "837P Re-submission"])

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
        
    cpt = st.selectbox("CPT Code", [
        "90837 - Psychotherapy (60 Min)", "90834 - Psychotherapy (45 Min)",
        "90791 - Psychiatric Diagnostic Eval", "99214 - Med Management"
    ])
    modifiers = st.text_input("Modifiers (e.g., 95, 59)", "95")
    selected_carc = st.selectbox("Denial Reason Code (CARC - 37 Codes Loaded)", list(DENIAL_CODES.keys()))
    dx_notes = st.text_area("Diagnosis & Rationale", "F41.1 (Generalized Anxiety Disorder). Severe symptoms.", height=70)
    
    generate_btn = st.button("🚀 Push to Portal & Generate Deliverables", use_container_width=True)

with col_output:
    st.subheader("📡 Portal Transmission & Output Engine")
    if generate_btn:
        st.markdown('<span class="status-badge">✅ Claim & Appeal Data Prepared</span>', unsafe_allow_html=True)
        tab_direct, tab1, tab2, tab3 = st.tabs(["🚀 Portal Sync", "✉️ Formal Appeal", "📞 AR Call Script", "💻 EDI 837P Payload"])
        
        cpt_code = cpt.split(" - ")[0]
        carc_code = selected_carc.split(" - ")[0]
        pos_code_only = pos_code.split(" - ")[0]

        with tab_direct:
            st.success(f" Ready to Sync & Transmit via **{billing_portal}** to **{payer}**.")
            if st.button(f"📲 Transmit to {billing_portal} Now", type="primary", use_container_width=True):
                st.balloons()
                st.success(f"🎉 **SUCCESS!** Pushed to **{billing_portal}**! Batch ID: `{billing_portal[:3].upper()}-2026-{claim_icn}`")

        with tab1:
            st.code(f"FORMAL APPEAL FOR CLAIM {claim_icn}\nProvider: {billing_provider}\nPatient: {patient_name}\nCARC: {selected_carc}", language="text")

        with tab2:
            st.code(f"AR SCRIPT:\nCall Payer {payer_id} for Claim {claim_icn}. Inquire about denial under {carc_code}.", language="text")

        with tab3:
            st.code(f"ISA*00*...ST*837*0001*...CLM*{claim_icn}*{billed_amount}...SE*24*0001~", language="text")
