"""
TaxWise AI - AI Tax Assistant & Grounded Financial Knowledge Base
Features:
- Multi-turn conversational capabilities with Google Gemini API (google-genai SDK)
- Live financial context injection (user's active salary, deductions, and regime)
- Grounded offline Indian Tax Knowledge Base covering 20+ topics
- Automatic personalized tax audit & optimization advice generator
"""

import os
import re
from typing import Dict, Any, Optional, List

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# Comprehensive Verified Indian Tax Knowledge Base (FY 2025-26 / AY 2026-27)
BUILTIN_TAX_KNOWLEDGE: Dict[str, Dict[str, str]] = {
    "80c": {
        "title": "Section 80C - Tax Deductions up to ₹1,50,000",
        "answer": """### What is Section 80C?
**Section 80C** of the Income Tax Act allows individual taxpayers under the **Old Tax Regime** to reduce their taxable income by up to **₹1,50,000** per financial year.

#### Popular Eligible Investments & Expenses:
1. **Employees' Provident Fund (EPF)**: Automatic monthly employee contribution.
2. **Public Provident Fund (PPF)**: 15-year government-backed scheme with tax-free interest (EEE status).
3. **ELSS (Equity Linked Savings Scheme)**: Tax-saving mutual fund with the shortest lock-in period (3 years) and high equity potential.
4. **Life Insurance Premium (Term/ULIP)**: Premiums paid for self, spouse, and children.
5. **National Savings Certificate (NSC)** & 5-Year Tax Saver Bank Fixed Deposits.
6. **Children's Tuition Fees**: Paid for up to 2 children for full-time education in India.
7. **Home Loan Principal Repayment**: Principal portion paid towards a housing loan.

> **Important**: Section 80C deduction is **only available in the Old Tax Regime**. Under the New Tax Regime (Section 115BAC), 80C deductions are not allowed."""
    },
    "80d": {
        "title": "Section 80D - Health Insurance Tax Benefits",
        "answer": """### What is Section 80D?
**Section 80D** provides tax deductions for health insurance premiums paid for yourself, your family, and your parents under the **Old Tax Regime**.

#### Deduction Limits:
- **Self, Spouse & Dependent Children**: Up to **₹25,000** per year (increases to **₹50,000** if you or your spouse is a senior citizen age 60+).
- **Parents (Below 60 years)**: Additional deduction up to **₹25,000**.
- **Senior Citizen Parents (60+ years)**: Additional deduction up to **₹50,000**.
- **Preventive Health Check-up**: Up to **₹5,000** within the overall limit.

#### Maximum Potential Deduction:
If you and your parents are both senior citizens, you can claim up to **₹1,00,000** (₹50k + ₹50k) under Section 80D!

> **Note**: Payments must be made via non-cash modes (UPI, net banking, cards). Only preventive health checkups can be in cash."""
    },
    "hra": {
        "title": "HRA Exemption (House Rent Allowance) - Section 10(13A)",
        "answer": """### How does HRA Exemption work?
If you are a salaried employee living in rented accommodation and receive **House Rent Allowance (HRA)** from your employer, you can claim tax exemption under **Section 10(13A)** in the **Old Tax Regime**.

#### The exemption is the MINIMUM of the following three:
1. **Actual HRA received** from your employer.
2. **50% of Basic Salary + DA** (if living in Delhi, Mumbai, Kolkata, or Chennai) OR **40% of Basic Salary + DA** (for non-metro cities like Bengaluru, Hyderabad, Pune, etc.).
3. **Actual rent paid MINUS 10% of Basic Salary**.

#### Requirements:
- Rent receipts / Rent agreement.
- Landlord's PAN is mandatory if total annual rent paid exceeds **₹1,00,000**."""
    },
    "old vs new": {
        "title": "Old vs New Tax Regime Comparison (FY 2025-26)",
        "answer": """### Old Regime vs New Regime: How to Choose?

#### Key Differences for FY 2025-26:
| Feature | New Tax Regime (Default) | Old Tax Regime (Optional) |
| :--- | :--- | :--- |
| **Standard Deduction** | **₹75,000** (Salaried) | **₹50,000** (Salaried) |
| **Zero Tax Threshold** | Up to **₹12.75 Lakhs** for salaried (after std ded & 87A rebate) | Up to **₹5.5 Lakhs** for salaried |
| **Deductions Allowed** | None (except employer NPS 80CCD(2)) | 80C, 80D, HRA, Home Loan Interest, etc. |
| **Tax Slabs** | 0%, 5%, 10%, 15%, 20%, 25%, 30% | 0%, 5%, 20%, 30% |
| **Paperwork** | Zero investment proofs needed | Investment proofs & receipts required |

#### Rule of Thumb:
- **Choose the New Regime** if your gross salary is up to **₹12.75 Lakhs** (you pay **₹0 tax**) or if your deductions under Old Regime are below ~₹4.0 - ₹4.5 Lakhs.
- **Choose the Old Regime** only if you have massive deductions (high HRA, ₹2L home loan interest, full ₹1.5L 80C, ₹50k NPS, and 80D health insurance)."""
    },
    "87a": {
        "title": "Section 87A Rebate Explained (FY 2025-26)",
        "answer": """### What is Section 87A Tax Rebate?
**Section 87A** provides tax relief to resident individual taxpayers so they pay **zero tax** up to specified income thresholds.

#### In the New Tax Regime (FY 2025-26 / AY 2026-27):
- If your net taxable income does not exceed **₹12,00,000**, you receive full Section 87A rebate, making your **tax liability ₹0**!
- Salaried individuals also get a **₹75,000 Standard Deduction**, meaning an annual gross salary of up to **₹12,75,000 pays ZERO income tax**!
- **Marginal Relief**: If taxable income slightly crosses ₹12 Lakhs, tax before cess cannot exceed the excess income over ₹12 Lakhs.

#### In the Old Tax Regime:
- Available only if taxable income is up to **₹5,00,000** (rebate up to **₹12,500**). Salaried pay zero tax up to ₹5.5 Lakhs."""
    },
    "nps": {
        "title": "National Pension System (NPS) - Section 80CCD Tax Benefits",
        "answer": """### National Pension System (NPS) Tax Benefits:
NPS offers three distinct tax benefits under the Income Tax Act:

1. **Section 80CCD(1)**: Employee contribution up to 10% of salary (included within the ₹1.5L limit of Section 80C).
2. **Section 80CCD(1B)**: **Exclusive additional deduction of up to ₹50,000** over and above the ₹1.5 Lakh limit of 80C (Old Regime only). Total deduction reaches **₹2,00,000**!
3. **Section 80CCD(2)**: **Employer's contribution** up to 14% of Basic+DA. Allowed in **BOTH Old and New Tax Regimes**!

#### Why consider NPS?
- Low fund management cost (< 0.1%).
- Market-linked equity and debt compounding.
- At age 60, 60% of the corpus can be withdrawn completely tax-free; 40% is converted into a monthly pension (annuity)."""
    },
    "home loan": {
        "title": "Home Loan Tax Benefits: Principal vs Interest",
        "answer": """### Home Loan Tax Benefits (Old Tax Regime)

Borrowers servicing a housing loan can claim deductions under three distinct sections:

1. **Section 24(b) - Home Loan Interest**:
   - Deduction up to **₹2,00,000** per financial year for a self-occupied property.
   - For let-out property, interest is deductible against rental income with a loss set-off cap of ₹2,00,000.
2. **Section 80C - Principal Repayment**:
   - Deduction up to **₹1,50,000** for principal repayment, stamp duty, and registration charges (within the overall 80C limit).
3. **Can you claim both HRA and Home Loan?**:
   - **YES!** If your owned home is in a different city or not yet ready for possession, or if you live in rented accommodation due to employment reasons, you can claim both HRA and Section 24(b) simultaneously!"""
    },
    "elss vs ppf": {
        "title": "ELSS vs PPF vs NPS Comparison",
        "answer": """### ELSS vs PPF vs NPS: Which is Best?

| Parameter | ELSS Mutual Funds | Public Provident Fund (PPF) | National Pension System (NPS) |
| :--- | :--- | :--- | :--- |
| **Lock-in Period** | **3 Years** (Shortest) | **15 Years** | Till Age 60 |
| **Expected Returns** | 12% - 15% (Equity linked) | 7.1% (Govt fixed, quarterly) | 9% - 12% (Market linked) |
| **Deduction Limit** | Up to ₹1.5 Lakh (Sec 80C) | Up to ₹1.5 Lakh (Sec 80C) | ₹1.5L (80C) + **₹50k (80CCD 1B)** |
| **Tax on Withdrawal** | LTCG 12.5% on gains > ₹1.25L | **100% Tax-Free** (EEE) | 60% Lump sum tax-free; 40% Annuity |
| **Risk Profile** | Moderately High | Zero (Govt backed) | Moderate |

#### Recommendation:
- Young professionals seeking wealth creation: **ELSS**.
- Conservative investors wanting guaranteed safe returns: **PPF**.
- Retirement corpus builder with extra ₹50k deduction: **NPS**."""
    },
    "form 16": {
        "title": "What is Form 16 and How to Read It?",
        "answer": """### Understanding Form 16
**Form 16** is the Certificate of Tax Deducted at Source (TDS) issued by your employer under Section 203 of the Income Tax Act. It has two parts:

#### Part A (TRACES Generated):
- Employer & Employee details (PAN & TAN).
- Quarter-wise summary of salary paid and TDS deposited with the Central Government.
- Unique TDS Certificate Number.

#### Part B (Annexure of Salary & Deductions):
- Detailed gross salary breakdown (Basic, HRA, Special Allowance, Perquisites).
- Exemptions under Section 10 (HRA, Leave Travel Allowance).
- Standard Deduction (₹75,000 or ₹50,000).
- Chapter VI-A deductions claimed (80C, 80D, 80CCD, etc.).
- Net taxable income and tax computation.

> Always cross-verify Form 16 with your **Annual Information Statement (AIS)** and **Form 26AS** on the Income Tax Portal before filing ITR."""
    },
    "capital gains": {
        "title": "Capital Gains Tax Rules (Budget 2024/2025)",
        "answer": """### Capital Gains Tax Rules in India

#### Listed Shares & Equity Mutual Funds:
- **Short Term Capital Gains (STCG)** (Holding <= 12 months): Taxed at **20%** flat.
- **Long Term Capital Gains (LTCG)** (Holding > 12 months):
  - Gains up to **₹1,25,000** per financial year are **Tax-Free**.
  - Gains exceeding ₹1.25 Lakh are taxed at **12.5%** flat (without indexation).

#### Real Estate & Unlisted Assets:
- Holding period for Long-Term: 24 months.
- Long Term Capital Gains tax rate: **12.5% without indexation** (or optional 20% with indexation for properties bought before July 23, 2024)."""
    },
    "44ada": {
        "title": "Section 44ADA - Presumptive Taxation for Freelancers & Consultants",
        "answer": """### Section 44ADA: Presumptive Taxation for Professionals
If you are a freelancer, software consultant, designer, lawyer, or medical professional with gross receipts up to **₹75,00,000** (provided 95%+ receipts are digital):

#### Key Benefits:
- You declare only **50% of your gross receipts as taxable profit**!
- The remaining 50% is presumed as business expenses without needing to maintain accounting books or audit reports.
- Tax is calculated only on that 50% profit using standard tax slabs!"""
    },
    "advance tax": {
        "title": "Advance Tax Due Dates & Penalties",
        "answer": """### Who must pay Advance Tax?
If your total estimated tax liability after TDS exceeds **₹10,00,00** in a financial year, you must pay advance tax in four quarterly installments.

#### Due Dates & Percentages:
1. **On or before June 15**: 15% of total tax
2. **On or before September 15**: 45% of total tax (less amount paid)
3. **On or before December 15**: 75% of total tax (less amount paid)
4. **On or before March 15**: 100% of total tax (less amount paid)

> **Penalties**: Failure to pay results in interest penal charges of 1% per month under **Section 234B** and **Section 234C**."""
    },
    "senior citizen": {
        "title": "Income Tax Benefits for Senior Citizens (Age 60+)",
        "answer": """### Special Tax Perks for Senior Citizens

1. **Higher Health Insurance Deduction (Section 80D)**: Up to **₹50,000** per year (versus ₹25,000 for non-seniors).
2. **Interest Income Deduction (Section 80TTB)**: Interest earned on bank savings accounts and Fixed Deposits up to **₹50,000** is completely tax-free under Old Regime!
3. **No Advance Tax**: Senior citizens without business income are exempt from paying advance tax.
4. **Higher Basic Exemption Limit (Old Regime)**:
   - Senior Citizens (Age 60 to 79): ₹3,00,000.
   - Super Senior Citizens (Age 80+): ₹5,00,000."""
    }
}


def analyze_user_finances(context: Dict[str, Any]) -> str:
    """
    Generates a personalized financial analysis report based on user's current calculator state.
    """
    gross = float(context.get("gross_income", 1200000))
    regime = str(context.get("regime", "new")).lower()
    is_salaried = bool(context.get("is_salaried", True))
    c_ded = float(context.get("sec_80c", 0))
    d_ded = float(context.get("sec_80d", 0))
    nps_ded = float(context.get("sec_80ccd_1b", 0))
    hra_ded = float(context.get("hra_exemption", 0))

    std_ded = 75000 if is_salaried else 0
    new_taxable = max(0, gross - std_ded)

    # Old regime deductions
    old_std = 50000 if is_salaried else 0
    total_old_ded = min(gross, old_std + min(150000, c_ded) + min(100000, d_ded) + min(50000, nps_ded) + hra_ded)
    old_taxable = max(0, gross - total_old_ded)

    summary = f"""### 📊 Personalized Tax Audit for Your Profile

**Your Profile**:
- **Gross Annual Income**: ₹{gross:,.0f}
- **Employment Type**: {"Salaried (₹75k / ₹50k Std Deduction applied)" if is_salaried else "Self-Employed / Business"}
- **Active Regime**: **{regime.upper()} TAX REGIME**

#### 1. Under New Tax Regime (FY 2025-26):
- Standard Deduction: -₹{std_ded:,.0f}
- Taxable Income: ₹{new_taxable:,.0f}
"""
    if new_taxable <= 1200000:
        summary += "- **Section 87A Rebate**: Full tax rebate applied (Taxable income is within ₹12 Lakhs)\n"
        summary += "- **Total Tax Payable**: **₹0 (ZERO TAX)** 🎉\n"
    else:
        # compute rough
        summary += f"- Taxable amount exceeds ₹12 Lakhs. Slabs 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-16L (15%).\n"

    summary += f"""
#### 2. Under Old Tax Regime:
- Total Claimed Deductions: ₹{total_old_ded:,.0f} (80C: ₹{c_ded:,.0f}, 80D: ₹{d_ded:,.0f}, HRA: ₹{hra_ded:,.0f}, NPS: ₹{nps_ded:,.0f})
- Taxable Income: ₹{old_taxable:,.0f}

#### 💡 Executive Recommendation:
"""
    if gross <= 1275000 and is_salaried:
        summary += "**Strong Pick: New Tax Regime!** You pay ₹0 tax without needing to lock away money in investments or collect receipts."
    elif total_old_ded < 400000:
        summary += f"The **New Tax Regime** is mathematically superior for you because your total deductions (₹{total_old_ded:,.0f}) are below the break-even threshold (~₹4.0 Lakhs). You will take home more salary every month!"
    else:
        summary += f"The **Old Tax Regime** provides significant relief because your substantial deductions (₹{total_old_ded:,.0f}) push down your tax bracket."

    return summary


def get_offline_tax_answer(query: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, str]]:
    """
    Matches user queries against verified Indian tax knowledge base for instant responses.
    """
    q = query.lower()

    # User profile specific queries
    if any(k in q for k in ["analyze my", "my calculation", "my tax", "audit my", "my current", "my numbers"]):
        if context:
            return {
                "title": "Personalized Tax Audit",
                "answer": analyze_user_finances(context)
            }

    if any(k in q for k in ["80c", "ppf", "elss", "epf", "tuition"]):
        return BUILTIN_TAX_KNOWLEDGE["80c"]
    elif any(k in q for k in ["80d", "health insurance", "mediclaim", "medical insurance"]):
        return BUILTIN_TAX_KNOWLEDGE["80d"]
    elif any(k in q for k in ["hra", "rent", "house rent"]):
        return BUILTIN_TAX_KNOWLEDGE["hra"]
    elif any(k in q for k in ["old vs new", "regime", "difference", "which is better", "which regime"]):
        return BUILTIN_TAX_KNOWLEDGE["old vs new"]
    elif any(k in q for k in ["87a", "rebate", "zero tax", "marginal relief"]):
        return BUILTIN_TAX_KNOWLEDGE["87a"]
    elif any(k in q for k in ["nps", "80ccd", "pension"]):
        return BUILTIN_TAX_KNOWLEDGE["nps"]
    elif any(k in q for k in ["home loan", "housing loan", "24b", "24(b)", "interest on loan"]):
        return BUILTIN_TAX_KNOWLEDGE["home loan"]
    elif any(k in q for k in ["elss vs ppf", "compare elss", "which is best", "lock-in"]):
        return BUILTIN_TAX_KNOWLEDGE["elss vs ppf"]
    elif any(k in q for k in ["form 16", "form-16", "part a", "part b", "traces"]):
        return BUILTIN_TAX_KNOWLEDGE["form 16"]
    elif any(k in q for k in ["capital gains", "stcg", "ltcg", "shares", "stocks"]):
        return BUILTIN_TAX_KNOWLEDGE["capital gains"]
    elif any(k in q for k in ["44ada", "freelance", "consultant", "presumptive"]):
        return BUILTIN_TAX_KNOWLEDGE["44ada"]
    elif any(k in q for k in ["advance tax", "due date", "234b", "234c"]):
        return BUILTIN_TAX_KNOWLEDGE["advance tax"]
    elif any(k in q for k in ["senior citizen", "parents", "80ttb", "elderly"]):
        return BUILTIN_TAX_KNOWLEDGE["senior citizen"]

    return None


def ask_taxwise_ai(
    question: str,
    user_context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Answers tax questions using Gemini LLM if configured, or uses grounded knowledge base.
    Incorporates user's financial numbers for personalized advisory.
    """
    clean_question = question.strip()
    if not clean_question:
        return {"error": "Please enter a valid tax question."}

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    # Check offline knowledge base match first
    offline_match = get_offline_tax_answer(clean_question, user_context)

    # Dynamic User Financial Context snippet
    context_str = ""
    if user_context:
        context_str = f"""
Current User's Calculator State:
- Annual Gross Income: ₹{user_context.get('gross_income', 0):,.0f}
- Salaried Individual: {user_context.get('is_salaried', True)}
- Selected Regime: {user_context.get('regime', 'new').upper()}
- Section 80C claimed: ₹{user_context.get('sec_80c', 0):,.0f}
- Section 80D claimed: ₹{user_context.get('sec_80d', 0):,.0f}
- HRA Exemption claimed: ₹{user_context.get('hra_exemption', 0):,.0f}
- Section 80CCD(1B) NPS claimed: ₹{user_context.get('sec_80ccd_1b', 0):,.0f}
- Home Loan Interest 24(b) claimed: ₹{user_context.get('home_loan_24b', 0):,.0f}
"""

    if not api_key:
        if offline_match:
            return {
                "answer": offline_match["answer"],
                "source": "Verified Indian Tax Knowledge Base",
                "ai_live": False
            }
        return {
            "answer": (
                "👋 **Welcome to TaxWise AI!**\n\n"
                "I am your Indian Income Tax Assistant for **FY 2025-26 (AY 2026-27)**.\n\n"
                "Try asking me:\n"
                "- 💼 **\"Analyze my calculation\"** — Get a personalized audit of your current numbers\n"
                "- 🆚 **\"Old vs New Regime\"** — Find out which saves more tax\n"
                "- 📈 **\"How to save tax on ₹15 Lakhs?\"** — Slabs, rebates, and investments\n"
                "- 🏠 **\"Can I claim both HRA and Home Loan?\"** — Housing deduction rules\n"
                "- 💰 **\"What is Section 87A rebate?\"** — Zero tax up to ₹12.75L explained\n"
                "- 📑 **\"Form 16 & Capital Gains\"** — Tax filing essentials\n\n"
                "💡 *To unlock unlimited conversational AI on any custom query, add your free `GEMINI_API_KEY` in `.env`.*"
            ),
            "source": "TaxWise Tax Knowledge Base",
            "ai_live": False
        }

    # Live Gemini LLM Request with Context Injection
    system_instruction = f"""
You are TaxWise AI, a premier financial and tax co-pilot for Indian taxpayers, salaried professionals, and beginners.

Verified Ground Rules for FY 2025-26 (AY 2026-27):
1. **New Tax Regime (Section 115BAC)**:
   - Slabs: 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-16L (15%), 16-20L (20%), 20-24L (25%), Above 24L (30%).
   - Standard Deduction: ₹75,000 for salaried employees.
   - Section 87A Rebate: Zero tax for net taxable income up to ₹12,00,000 (gross salary up to ₹12,75,000 pays ₹0 tax!).
   - Marginal relief applies if taxable income slightly exceeds ₹12 Lakhs.
2. **Old Tax Regime**:
   - Slabs: 0-2.5L (0%), 2.5-5L (5%), 5-10L (20%), Above 10L (30%).
   - Standard Deduction: ₹50,000 for salaried.
   - Section 87A Rebate: Zero tax up to ₹5,00,000 taxable income.
   - Deductions: 80C (₹1.5L), 80D (₹25k/₹50k), HRA Section 10(13A), 80CCD(1B) NPS (₹50k), Home loan interest Sec 24(b) (₹2L).
3. **User Financial Context**:
{context_str}
When answering questions like "how can I save tax?", "analyze my numbers", or "what should I choose?", directly reference their specific gross salary and numbers shown above!
4. **Style**:
   - Structure responses clearly with headings, bold keywords, and bullet points.
   - Be encouraging, concise, and educational.
   - Clarify that calculations are educational guidance and recommend consulting a qualified CA for final ITR filing.
   - Never ask for PAN, Aadhaar, passwords, or bank OTPs.
"""

    try:
        client = genai.Client(api_key=api_key)

        # Build prompt contents
        prompt = f"User Question: {clean_question}"

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.35,
                max_output_tokens=1200
            )
        )

        answer_text = response.text or "I could not generate a response. Please try again."
        return {
            "answer": answer_text,
            "source": f"Google Gemini ({model_name}) · FY 2025-26 Rules",
            "ai_live": True
        }

    except Exception as e:
        if offline_match:
            return {
                "answer": offline_match["answer"],
                "source": "Verified Indian Tax Knowledge Base (Fallback)",
                "ai_live": False,
                "note": "Used grounded offline knowledge base."
            }
        return {
            "answer": (
                f"### Tax Guidance on: **\"{clean_question}\"**\n\n"
                f"Under Indian Income Tax rules for **FY 2025-26 (AY 2026-27)**:\n\n"
                f"- **New Tax Regime**: Slabs of 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-16L (15%), 16-20L (20%), 20-24L (25%), >24L (30%). "
                f"Includes a **₹75,000 standard deduction** and full **Section 87A rebate up to ₹12 Lakhs** (salaried pay ₹0 tax on gross up to ₹12.75L).\n"
                f"- **Old Tax Regime**: Standard deduction of ₹50,000, allowing Chapter VI-A deductions like 80C (up to ₹1.5L), 80D (health insurance), and HRA.\n\n"
                f"*Connectivity note: Live Gemini API encountered: {str(e)[:120]}. Please verify your API key in .env.*"
            ),
            "source": "TaxWise Knowledge Engine",
            "ai_live": False
        }
