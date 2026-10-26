"""
Tender Compliance Assistant — Cloud Version
Streamlit Community Cloud deployment

Differences from local version:
    - No Ollama dependency
    - Uses sentence-transformers for embeddings (free, runs on CPU)
    - Uses Groq API (free tier) for LLM generation
      OR falls back to showing retrieved chunks directly
    - All data pre-indexed and included in repo

Author: Prateek Gaur
Project: tender-compliance-rag
"""

import json
import sys
import os
from pathlib import Path

import numpy as np
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Tender Compliance Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .source-box {
        background: #1e3a5f; border-left: 3px solid #2563eb;
        padding: 8px 12px; border-radius: 4px; margin: 4px 0;
        font-size: 13px; color: #e2e8f0;
    }
    .answer-box {
        background: #1e293b; border: 1px solid #334155;
        padding: 16px; border-radius: 8px; margin: 8px 0;
        font-size: 14px; line-height: 1.6; color: #f1f5f9;
    }
    .verdict-pass    { color:#4ade80; font-weight:bold; font-size:18px; }
    .verdict-fail    { color:#f87171; font-weight:bold; font-size:18px; }
    .verdict-partial { color:#fbbf24; font-weight:bold; font-size:18px; }
</style>
""", unsafe_allow_html=True)

# ── Document store (inline for cloud deployment) ───────────────────────────────

DOCUMENTS = {
    "JdVVNL_BESS_Tender_2024": {
        "type": "tender",
        "content": """
JODHPUR VIDYUT VITRAN NIGAM LIMITED (JdVVNL) — BESS Tender 2024
Tender No: JdVVNL/BESS/2024/001

TECHNICAL SPECIFICATIONS:
- Rated Power: 100 MW AC | Rated Energy: 200 MWh usable
- Minimum C-rate: 0.5C (2-hour discharge)
- Round Trip Efficiency (RTE): >= 85% at AC terminals
- Depth of Discharge (DoD): >= 80%
- Calendar Life: >= 15 years | Cycle Life: >= 6000 cycles at 80% DoD
- Battery Technology: LFP preferred, NMC acceptable with enhanced safety
- Cells must comply with IEC 62619:2022 safety standard
- Grid-Forming (GFM) capability: MANDATORY for all units (Corrigendum 1)
- Grid-Following (GFL) mode: required as fallback
- Power Factor range: 0.95 leading to 0.95 lagging
- THD: <= 3% at rated power
- Frequency response: Primary Frequency Response (PFR) within 30 seconds
- Synthetic inertia: H >= 2 seconds
- BMS communication: IEC 61850 / Modbus TCP
- Cybersecurity: IEC 62443 compliance required (Corrigendum 3)
- IP rating: IP54 minimum for outdoor enclosures
- Operating temperature: -5 to +50 degrees C ambient

FINANCIAL:
- EMD: INR 5 Crore (Bank Guarantee, 180 days validity)
- Performance Bank Guarantee: 10% of contract value
- Payment: 10% on award, 30% delivery, 40% commissioning, 15% performance test, 5% retained
- Commissioning deadline: 18 months from LOA

CORRIGENDUM HISTORY:
- Corrigendum 1 (Feb 2024): Grid-Forming changed from preferred to MANDATORY
- Corrigendum 2 (Mar 2024): Cycle life increased from 5000 to 6000 cycles
- Corrigendum 3 (Apr 2024): Added IEC 62443 cybersecurity requirement for BMS

EVALUATION: Technical Pass/Fail (70% minimum), Financial L1 (lowest bid)
Make in India: 20% local content mandatory
Bid deadline: 31 May 2024
"""
    },
    "AVVNL_Solar_BESS_Tender_2024": {
        "type": "tender",
        "content": """
AJMER VIDYUT VITRAN NIGAM LIMITED (AVVNL) — 50 MW Solar + 25MW/50MWh BESS
Tender Ref: AVVNL/RE/2024/SOLAR-BESS/007

BESS SPECIFICATIONS:
- Power: 25 MW AC | Energy: 50 MWh usable (2-hour system)
- Chemistry: LFP preferred, NMC acceptable
- Round Trip Efficiency (RTE): >= 87% including transformer losses
- Warranty: 10 years, minimum 70% capacity retention

OPERATIONAL MODES REQUIRED:
- Mode 1: Peak shaving — charge during solar, discharge during evening peak
- Mode 2: Frequency regulation — respond within 200ms to grid frequency deviation
- Mode 3: Ramp rate control — limit solar ramp to 10% rated capacity per minute
- Mode 4: Black start — energize grid from islanded state

SOLAR SPECIFICATIONS:
- Technology: Mono-PERC or TOPCon bifacial, minimum 21% module efficiency
- Temperature coefficient (Pmax): better than -0.35%/degree C
- Certification: IEC 61215, IEC 61730, BIS IS 14286
- String or central inverters acceptable, MPPT efficiency >= 99%

FINANCIAL:
- Project tenure: 25 years Build-Own-Operate
- Tariff: Competitive bidding — lowest tariff in INR per kWh wins
- Deemed generation: applicable for grid unavailability > 4 hours

QUALIFICATION: Minimum 100 MW solar + 50 MWh BESS experience in India
Net worth >= INR 50 crore, turnover >= INR 100 crore
"""
    },
    "MSEDCL_BESS_Procurement_2024": {
        "type": "tender",
        "content": """
MAHARASHTRA STATE ELECTRICITY DISTRIBUTION CO. LTD (MSEDCL)
BESS Procurement — 500 MW / 1000 MWh

MANDATORY SAFETY STANDARDS (disqualification if not met):
- IEC 62619:2022 — Safety for secondary lithium cells
- UL 9540 — Energy Storage Systems standard
- NFPA 855 — Installation of Stationary Energy Storage Systems
- IS 16046 (Part 1) — BIS equivalent safety standard

PERFORMANCE GUARANTEES (tested during PAT):
- Round Trip Efficiency: >= 85% AC-AC per IEC 62933-2
- Capacity at BOL: >= 100% of rated
- Response time (frequency): <= 200 milliseconds per CEA Grid Code
- LVRT capability: 0% voltage for 150ms per CEA Regulations 2019
- Self-discharge rate: <= 2% per day
- SoC accuracy: +/- 3%

WARRANTY: Minimum 10 years, 80% rated capacity at end of warranty
Degradation: maximum 2.5% per year for first 5 years

GRID CODE COMPLIANCE:
- Primary Frequency Response (PFR): droop 4%, response within 30 seconds
- Frequency dead band: +/- 0.03 Hz per IEGC
- AGC participation: mandatory for units > 10 MW
- Reactive power: 0.95 leading to 0.95 lagging continuous

MAKE IN INDIA: Class I local content >= 40%, BIS certification mandatory from FY2026
"""
    },
    "CEA_Grid_Connectivity_Regulations_2019": {
        "type": "grid_code",
        "content": """
CEA TECHNICAL STANDARDS FOR CONNECTIVITY — 2019

FREQUENCY STANDARDS:
- Rated frequency: 50 Hz
- Normal operating range: 49.5 Hz to 50.5 Hz
- Emergency range: 47.5 Hz to 51.5 Hz (units must remain connected)

FAULT RIDE-THROUGH (LVRT) — all generating units > 10 MW must remain connected:
- 0% voltage: remain connected 150 milliseconds
- 20% voltage: remain connected 625 milliseconds
- 50% voltage: remain connected 1000 milliseconds
- 75% voltage: remain connected 2000 milliseconds
- 90% voltage: remain connected 3000 milliseconds

REACTIVE CURRENT INJECTION DURING FAULT:
- During voltage dips below 90% nominal: inject 2% rated current per 1% voltage dip
- Response time: within 20 milliseconds

POWER QUALITY:
- THD: <= 5% at Point of Interconnection
- DC injection: <= 0.5% of rated AC current

ANTI-ISLANDING: trip within 2 seconds, reconnect after 60 seconds stable grid

PROTECTION:
- Under voltage trip: < 0.8 pu for > 3 seconds
- Over voltage trip: > 1.15 pu for > 0.5 seconds
- Under frequency: < 47.5 Hz immediate trip
- Over frequency: > 51.5 Hz immediate trip

ABT METERING: Required for all generating stations > 1 MW, 15-minute blocks

BESS SPECIAL REQUIREMENTS:
- Minimum SoC during grid-connected operation: 10%
- Maximum SoC: 95%
- SoC reporting to SLDC: mandatory
- PFR participation: mandatory
- AGC: mandatory for units > 10 MW
"""
    },
    "IEC_62619_Safety_Requirements": {
        "type": "grid_code",
        "content": """
IEC 62619:2022 — SAFETY REQUIREMENTS FOR SECONDARY LITHIUM CELLS

CELL LEVEL REQUIREMENTS:
- Overcharge: withstand 2C for 2.5 hours without fire or explosion
- BMS must terminate charge at manufacturer cutoff voltage
- Redundant overcharge protection: primary BMS + secondary hardware cutoff
- Short circuit: no fire or explosion within 1 hour
- Nail penetration: 3mm steel nail at 80 mm/s — must not catch fire
- Thermal abuse: 130 degree C oven for 30 minutes — no thermal runaway
- Thermal runaway propagation: single cell TR must NOT propagate to adjacent cells

MODULE AND PACK REQUIREMENTS:
- BMS must monitor: voltage, current, temperature per cell or group
- BMS must provide: overcharge, over-discharge, overcurrent, overtemperature protection
- Isolation resistance: >= 100 ohm per volt between battery pack and enclosure
- Leakage current: <= 3.5 mA in normal operation
- IP rating: IP67 minimum for battery pack

SYSTEM REQUIREMENTS (BESS):
- Ventilation: forced ventilation to prevent gas accumulation
- Fire detection: smoke and heat detectors per NFPA 72
- Fire suppression: clean agent or water mist per NFPA 855
- Emergency disconnect: readily accessible main disconnect switch

TESTING: Factory Acceptance Test (FAT) and Site Acceptance Test (SAT) mandatory
Certification bodies: UL, TUV, BIS, SGS, Intertek
"""
    },
    "IEEE_1547_2018_Interconnection": {
        "type": "grid_code",
        "content": """
IEEE 1547-2018 — INTERCONNECTION OF DISTRIBUTED ENERGY RESOURCES

FREQUENCY REQUIREMENTS:
- Under frequency trip: 47.5 Hz (all categories)
- Over frequency trip: 51.5 Hz (all categories)
- Frequency ride-through: must remain connected 47.5 to 51.5 Hz

FREQUENCY-WATT RESPONSE (required for BESS):
- Active power reduction when f > 50.2 Hz
- Droop: default 5%, adjustable 1% to 10%
- Dead band: +/- 0.036 Hz default

REACTIVE POWER:
- Minimum: 0.85 leading to 0.85 lagging at Point of Connection
- Volt-VAR: automatic reactive power injection based on voltage

ANTI-ISLANDING:
- Trip within 2 seconds of island detection
- Reconnect: voltage stable for 60 seconds, frequency 47.5 to 51.5 Hz

COMMUNICATION:
- Must support IEEE 2030.5 or SunSpec Modbus
- Required signals: real power, reactive power, voltage, frequency, SoC for BESS
- Cybersecurity: TLS 1.2 or higher for all communications
- Authentication: required for all remote control interfaces

TESTING REQUIRED:
- Voltage regulation, frequency response, reactive power capability
- Anti-islanding test, ride-through demonstration
"""
    },
}

# ── Embedding and retrieval ─────────────────────────────────────────────────────────────────────

@st.cache_resource
def load_embedder():
    """Load sentence-transformers embedder (free, runs on CPU)."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model, True
    except Exception:
        return None, False

@st.cache_data
def build_index(_model, use_st: bool):
    """Build embedding index from document store."""
    chunks    = []
    texts     = []

    for doc_name, doc in DOCUMENTS.items():
        # Split into paragraphs
        paragraphs = [p.strip() for p in doc["content"].split("\n\n") if len(p.strip()) > 60]
        for i, para in enumerate(paragraphs):
            chunks.append({
                "doc_name": doc_name,
                "doc_type": doc["type"],
                "text":     para,
                "citation": f"{'Tender' if doc['type']=='tender' else 'Grid Code'}: {doc_name.replace('_',' ')}",
            })
            texts.append(para)

    if use_st and _model is not None:
        embeddings = _model.encode(texts, normalize_embeddings=True)
    else:
        # Fallback: simple TF-IDF style keyword embeddings
        embeddings = _keyword_embeddings(texts)

    return chunks, np.array(embeddings, dtype=np.float32)

def _keyword_embeddings(texts):
    """Simple keyword-based embeddings as fallback."""
    vocab = {}
    for text in texts:
        for word in text.lower().split():
            if word not in vocab:
                vocab[word] = len(vocab)

    dim = min(len(vocab), 300)
    embs = []
    for text in texts:
        vec = np.zeros(dim)
        for word in text.lower().split():
            idx = vocab.get(word, -1)
            if 0 <= idx < dim:
                vec[idx] += 1
        norm = np.linalg.norm(vec)
        embs.append(vec / (norm + 1e-8))
    return embs

def retrieve(query: str, chunks, embeddings, model, use_st: bool, k: int = 4):
    """Retrieve top-kchunks for a query."""
    if use_st and model is not None:
        q_emb = model.encode([query], normalize_embeddings=True)[0]
    else:
        q_emb = _keyword_embeddings([query])[0]
        if len(q_emb) < embeddings.shape[1]:
            q_emb = np.pad(q_emb, (0, embeddings.shape[1] - len(q_emb)))
        elif len(q_emb) > embeddings.shape[1]:
            q_emb = q_emb[:embeddings.shape[1]]

    scores   = embeddings @ q_emb
    top_idxs = np.argsort(scores)[::-1][:k]
    return [{"score": float(scores[i]), **chunks[i]} for i in top_idxs]

def generate_answer(question: str, results: list, mode: str) -> str:
    """Generate answer from retrieved chunks."""
    context = "\n\n".join([
        f"[{r['citation']}]\n{r['text']}" for r in results
    ])

    # Try Groq API if key is available
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            import requests
            prompt = f"""You are an expert in Indian power sector tenders and grid codes.
Answer the question based ONLY on the provided context. Cite sources in brackets.

Context:
{context}

Question: {question}
Mode: {mode}

Answer concisely with source citations:"""

            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}",
                         "Content-Type": "application/json"},
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 600,
                    "temperature": 0.1,
                },
                timeout=30,
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # Fallback: return best retrieved chunks
    best = results[0] if results else {}
    answer = f"**Most relevant information found:**\n\n"
    for r in results[:2]:
        answer += f"📄 **{r['citation']}** (relevance: {r['score']:.2f})\n\n"
        answer += f"{r['text'][:400]}...\n\n---\n\n"

    if mode == "compliance":
        text_lower = " ".join(r["text"] for r in results).lower()
        if any(term in question.lower() for term in ["85%", "87%", "83%", "80%"]):
            answer += "\n⚠️ *Compare the value in your question against the requirement shown above.*"

    return answer

# ── Load resources ────────────────────────────────────────────────────────────

model, use_st = load_embedder()
chunks, embeddings = build_index(model, use_st)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 📋 Tender Compliance Assistant")
    st.markdown("*AI-powered analysis for Indian DISCOM BESS tenders*")
    st.markdown("---")
    st.markdown("### 📚 Knowledge Base")
    st.metric("Chunks indexed", len(chunks))
    st.markdown(f"📄 Tenders: **3** (JdVVNL, AVVNL, MSEDCL)")
    st.markdown(f"⚡ Grid codes: **3** (CEA, IEC 62619, IEEE 1547)")
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        "Built by [Prateek Gaur](https://github.com/PRATdoppelEK). "
        "Demonstrates Solution C from the Inverter AI pitch deck — "
        "a RAG system for tender compliance."
    )
    if use_st:
        st.success("✅ sentence-transformers loaded")
    else:
        st.info("ℹ️ Using keyword matching (install sentence-transformers for better results)")

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("# 📋 Tender & Grid Compliance Assistant")
st.markdown(
    "Ask questions about **JdVVNL, AVVNL, MSEDCL** BESS tenders "
    "and **CEA, IEC 62619, IEEE 1547** grid codes. "
    "Every answer cites the source document."
)
st.markdown("---")

# ── Mode ─────────────────────────────────────────────────────────────────────

mode_map = {
    "💬 Answer Question":    "answer",
    "✅ Compliance Check":   "compliance",
    "📝 Corrigendum Tracker":"corrigendum",
    "🔀 Compare Tenders":    "compare",
}
selected = st.radio("Mode:", list(mode_map.keys()), horizontal=True)
mode     = mode_map[selected]
st.markdown("---")

# ── Examples ──────────────────────────────────────────────────────────────────

EXAMPLES = {
    "answer": [
        "What is the minimum round trip efficiency required?",
        "Is Grid-Forming capability mandatory or optional?",
        "What are the LVRT fault ride-through requirements?",
        "What is the EMD amount for JdVVNL?",
        "What battery chemistries are acceptable?",
        "What are the Make in India requirements?",
        "What is the IEC 62619 requirement for thermal runaway propagation?",
        "What communication protocols are required for BMS?",
    ],
    "compliance": [
        "Does 83% round trip efficiency meet MSEDCL requirements?",
        "Does NMC battery chemistry meet JdVVNL requirements?",
        "Does IP54 rating meet the environmental requirements?",
        "Does 5000 cycle life meet JdVVNL specifications?",
    ],
    "corrigendum": [
        "What changed in the JdVVNL corrigendum?",
        "List all amendments and changes in the tenders",
        "What was the original Grid-Forming requirement before corrigendum?",
    ],
    "compare": [
        "Compare round trip efficiency requirements across all tenders",
        "How does cycle life requirement differ between JdVVNL and MSEDCL?",
        "Which tender has the strictest safety certification requirements?",
    ],
}

st.markdown("**💡 Try these questions:**")
cols = st.columns(2)
examples = EXAMPLES.get(mode, EXAMPLES["answer"])
for i, ex in enumerate(examples[:6]):
    with cols[i % 2]:
        if st.button(f"📌 {ex[:55]}", key=f"ex_{i}"):
            st.session_state["q"] = ex

# ── Input ─────────────────────────────────────────────────────────────────────

st.markdown("---")
if mode == "compliance":
    c1, c2 = st.columns([2, 1])
    with c1: spec  = st.text_input("Specification", placeholder="e.g. Round Trip Efficiency")
    with c2: value = st.text_input("Your value",    placeholder="e.g. 83%")
    question = f"Does {spec} of {value} meet the requirements?" if spec and value else ""
else:
    question = st.text_area(
        "Your question:",
        value   = st.session_state.get("q", ""),
        height  = 80,
        placeholder="Ask anything about tenders or grid codes..."
    )

k = st.slider("Chunks to retrieve", 2, 6, 4, key="k_slider")

if st.button("🔍 Ask", type="primary", disabled=not question):
    with st.spinner("Retrieving and generating answer..."):
        results = retrieve(question, chunks, embeddings, model, use_st, k=k)
        answer  = generate_answer(question, results, mode)

    st.markdown("### 💬 Answer")
    st.markdown("**Answer:**")
    st.info(answer)

    if mode == "compliance":
        ans_upper = answer.upper()
        if "FAIL"    in ans_upper: st.markdown('<p class="verdict-fail">❌ LIKELY FAIL</p>', unsafe_allow_html=True)
        elif "PASS"  in ans_upper: st.markdown('<p class="verdict-pass">✅ LIKELY PASS</p>', unsafe_allow_html=True)

    st.markdown(f"### 📚 Sources ({len(results)})")
    for r in results:
        icon = "📄" if r["doc_type"] == "tender" else "⚡"
        st.markdown(f"{icon} **{r['citation']}** | Relevance: {r['score']:.3f}")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#9ca3af;font-size:12px;'>"
    "tender-compliance-rag · Built by Prateek Gaur · "
    "<a href='https://github.com/PRATdoppelEK/tender-compliance-rag'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
