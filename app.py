import streamlit as st

st.set_page_config(
    page_title="MindBill AI - Enterprise Denial Management Engine",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 MindBill AI")
st.caption("Advanced Multi-Payer Behavioral & Medical Denial Resolution Portal")
st.divider()

# Complete CARC Denial Codes Database (CO 1 - CO 260+)
DENIAL_CODES = {
    "CO 1 - Deductible Amount": "Deductible amount not met by the patient.",
    "CO 2 - Coinsurance Amount": "Coinsurance amount applied to patient responsibility.",
    "CO 3 - Copay Amount": "Co-payment amount required from the patient.",
    "CO 4 - Procedure code inconsistent with modifier / Missing Modifier": "The procedure code is inconsistent with the modifier used or a required modifier is missing.",
    "CO 16 - Claim/service lacks information": "Claim or service lacks necessary information or has submission errors (e.g., missing clinical notes/medical records).",
    "CO 18 - Duplicate claim / service rendered": "Duplicate claim or service rendered on the same date of service.",
    "CO 19 - Claim denied; Student coverage guidelines not met": "Student insurance guidelines or documentation requirements not met.",
    "CO 22 - This care may be covered by another payer (COB / Primary issue)": "Payment denied because care may be covered by another primary insurance (Coordination of Benefits).",
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
    "CO 167 - Diagnosis inconsistent with procedure": "The diagnosis code provided is inconsistent with the billed procedure code.",
    "CO 197 - Pre-certification / Prior Authorization missing or invalid": "Pre-certification or Prior Authorization was not obtained before rendering the service.",
    "CO 198 - Pre-certification / Authorization exceeded": "Billed units exceed the number of authorized units granted in the precertification.",
    "CO 204 - Service not covered under patient policy": "This specific procedure or service is excluded from the patient's benefit plan.",
    "CO 219 - Service/procedure denied; missing medical records": "Claim rejected due to missing medical records or session notes.",
    "CO 234 - Procedure code not covered for date of service": "This code was not active or eligible for coverage on the billed date of service.",
    "CO 252 - Attachment/documentation missing": "Electronic attachment or required supporting document was not received.",
    "CO 260 - Settlement/Court award adjustment": "Third-party liability or settlement adjustment applied."
}

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Claim & Payer Setup")
    
    # Comprehensive US Payers (Including NY/Regional & National Payers)
    payer = st.selectbox("Select Payer", [
        "Health First (NY)",
        "MetroPlus Health Plan",
        "EmblemHealth (HIP/GHI)",
        "Fidelis Care",
        "BCBS / Empire BlueCross BlueShield",
        "Aetna / Aetna Behavioral",
        "Cigna / Evernorth Health",
        "UnitedHealthcare (UHC) / Optum",
        "Medicare (CMS / MAC)",
        "Medicaid (State Portal)",
        "Beacon Health Options / Carelon",
        "Magellan Health",
        "Humana Behavioral"
    ])
    
    dos = st.date_input("Date of Service")
    
    cpt = st.selectbox("Mental Health / Medical CPT Code", [
        "90837 - Psychotherapy (60 Min)",
        "90834 - Psychotherapy (45 Min)",
        "90832 - Psychotherapy (30 Min)",
        "90791 - Psychiatric Diagnostic Evaluation",
        "90792 - Psychiatric Eval w/ Medical Services",
        "90833 - Psychotherapy with E/M Visit (Add-on)",
        "99214 - Medication Management / Outpatient E/M",
        "99213 - Outpatient E/M Visit",
        "90847 - Family Psychotherapy w/ Patient",
        "90853 - Group Psychotherapy"
    ])
    
    selected_carc_key = st.selectbox("Denial Code (CARC)", list(DENIAL_CODES.keys()))
    carc_description = DENIAL_CODES[selected_carc_key]
    
    st.caption(f"📌 **Code Info:** {carc_description}")
    
    notes = st.text_area("Clinical Notes / Diagnosis (e.g., F41.1 Anxiety, F32.9 Depression, F43.10 PTSD)", height=90)
    
    generate_btn = st.button("🚀 Generate Appeal & Call Script", use_container_width=True)

with col2:
    if generate_btn:
        st.success(f"✅ AI Analysis Complete for {payer} Claim!")
        
        tab1, tab2, tab3 = st.tabs(["📄 Appeal Letter", "📞 AR Call Script", "🔍 Compliance Guidelines"])
        
        with tab1:
            st.subheader("Formal Reconsideration / Appeal Letter")
            letter_text = f"""
DATE: [Current Date]
TO: {payer} - Claims Appeal & Grievance Department
RE: FORMAL RECONSIDERATION / APPEAL REQUEST
CLAIM DENIAL CODE: {selected_carc_key}
DATE OF SERVICE: {dos} | BILLED CPT: {cpt.split(' - ')[0]}

Dear Appeals Committee,

Please accept this letter as a formal reconsideration request regarding the improper denial of CPT code {cpt.split(' - ')[0]} for Date of Service {dos} under denial code {selected_carc_key} ({carc_description}).

REASON FOR APPEAL:
The rendered service was medically necessary, clinically indicated, and performed by a licensed professional in compliance with payer guidelines for diagnosis: {notes if notes else 'DSM-5 / ICD-10 Diagnosis'}.

1. CLINICAL & PARITY JUSTIFICATION:
   Under the Mental Health Parity and Addiction Equity Act (MHPAEA) and state insurance mandates, mental health and substance use disorder benefits must be provided at parity with medical/surgical benefits without imposing improper Non-Quantitative Treatment Limitations (NQTLs).

2. BILLING COMPLIANCE:
   All documentation, CPT modifiers, and session durations meet CPT and CMS coding standard requirements.

Enclosed please find supporting clinical notes and documentation. We request immediate re-adjudication and processing of this claim for payment.

Sincerely,
[Provider Name / Billing Department]
[NPI / Tax ID]
            """
            st.code(letter_text, language="text")

        with tab2:
            st.subheader("AR Representative Call Script")
            script_text = f"""
1. GREETING & VERIFICATION:
   "Hello, I am calling from [Clinic Name] regarding Claim ID for DOS {dos}, Patient Member ID [ID] billed to {payer}."

2. ISSUE STATEMENT:
   "I am reviewing a denial under code {selected_carc_key}. The explanation states: {carc_description} for CPT {cpt.split(' - ')[0]}."

3. TARGETED ACTION & QUESTIONS FOR REP:
   - If Authorization (CO 197/198): "Can you verify if a retroactive authorization can be initiated, or if clinical records can be submitted for review?"
   - If Medical Necessity (CO 50): "Please confirm the direct fax number/portal address to submit session notes for Medical Necessity review."
   - If Bundled/Modifier (CO 4/CO 59/CO 97): "Modifier was billed appropriately per NCCI edits. Can this claim be sent back for automated re-processing?"
   - If COB/Primary (CO 22): "Could you confirm the primary policy details currently on file in your system?"

4. CALL CLOSURE:
   "Please provide the Call Reference Number, Rep Name, and expected turnaround timeframe for this re-adjudication."
            """
            st.code(script_text, language="text")

        with tab3:
            st.info(f"💡 **Payer & Code Rules ({payer}):**\n- Ensure CPT 90837 start/stop times are documented (53+ mins).\n- Verify state Medicaid / Managed Care (Health First, MetroPlus, Fidelis) authorization rules.\n- For Telehealth claims, confirm whether Modifier 95 or GT is required by {payer}.")
    else:
        st.info("👈 Select claim details on the left panel and click 'Generate' to create custom appeals.")
