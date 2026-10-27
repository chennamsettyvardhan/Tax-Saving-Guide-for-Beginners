"""
TaxWise AI - AI Tax Assistant & Grounded Knowledge Base
Integrates Google Gemini API using google-genai SDK with safety guardrails
and a comprehensive built-in offline tax knowledge base for instant responses.
"""

import os
import re
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# Verified Built-in Indian Tax Knowledge Base for instant beginner explanations
BUILTIN_TAX_KNOWLEDGE = {
    "80c": {
        "title": "Section 80C - Tax Deductions up to ₹1,50,000",
        "answer": """### What is Section 80C?
**Section 80C** of the Income Tax Act allows individual taxpayers under the **Old Tax Regime** to reduce their taxable income by up to **₹1,50,000** per financial year.

#### Popular Eligible Investments & Expenses:
1. **Employees' Provident Fund (EPF)**: Automatic monthly employee contribution.
2. **Public Provident Fund (PPF)**: 15-year government-backed scheme with tax-free interest (EEE status).
3. **ELSS (Equity Linked Savings Scheme)**: Tax-saving mutual fund with the shortest lock-in period (3 years) and inflation-beating equity returns.
4. **Life Insurance Premium (Term/ULIP)**: Premiums paid for self, spouse, and children.
5. **National Savings Certificate (NSC)** & 5-Year Tax Saver Fixed Deposits.
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
        "title": "Old vs New Tax Regime: Which is Better for You?",
        "answer": """### Old Regime vs New Regime: How to Choose?

#### Key Differences:
| Feature | New Tax Regime (Default) | Old Tax Regime (Optional) |
| :--- | :--- | :--- |
| **Standard Deduction** | **₹75,000** (Salaried) | **₹50,000** (Salaried) |
| **Tax Free Income Limit** | Up to **₹12.75 Lakhs** (after std ded & 87A rebate) | Up to **₹5.5 Lakhs** (after std ded & 87A rebate) |
| **Deductions Allowed** | None (except employer NPS 80CCD(2)) | 80C, 80D, HRA, Home Loan Interest, etc. |
| **Tax Slabs** | Lower rates (0%, 5%, 10%, 15%, 20%, 25%, 30%) | Higher rates (0%, 5%, 20%, 30%) |
| **Paperwork** | Zero investment proofs needed | Investment proofs & receipts required |

#### Rule of Thumb:
- **Choose the New Regime** if your gross salary is up to **₹12.75 Lakhs** (as you pay **₹0 tax** with ₹75k standard deduction + ₹12L Section 87A rebate) or if your deductions under the Old Regime do not significantly exceed the new lower tax rates.
- **Choose the Old Regime** only if you have massive deductions (high HRA rent, ₹2L home loan interest, full ₹1.5L 80C, ₹50k 80CCD NPS, and 80D health insurance)."""
    },
    "87a": {
        "title": "Section 87A Rebate Explained (FY 2025-26)",
        "answer": """### What is Section 87A Tax Rebate?
**Section 87A** provides tax relief to resident individual taxpayers so they pay **zero tax** up to specified income thresholds.

#### In the New Tax Regime (FY 2025-26 / AY 2026-27):
- If your net taxable income does not exceed **₹12,00,000**, you receive full Section 87A rebate, making your **tax liability ₹0**!
- Salaried individuals also get a **₹75,000 Standard Deduction**, meaning an annual gross salary of up to **₹12,75,000 pays ZERO income tax**!
- **Marginal Relief**: If taxable income slightly crosses ₹12 Lakhs, tax before cess cannot exceed the amount by which income exceeds ₹12 Lakhs.

#### In the Old Tax Regime:
- Available only if taxable income is up to **₹5,00,000** (rebate up to **₹12,500**). Salaried pay zero tax up to ₹5.5 Lakhs."""
    },
    "nps": {
        "title": "Section 80CCD - National Pension System (NPS) Tax Benefits",
        "answer": """### National Pension System (NPS) Tax Benefits:
NPS offers three distinct tax benefits under the Income Tax Act:

1. **Section 80CCD(1)**: Employee contribution up to 10% of salary (included within the ₹1.5L limit of Section 80C).
2. **Section 80CCD(1B)**: **Exclusive additional deduction of up to ₹50,000** over and above the ₹1.5 Lakh limit of 80C (Old Regime only). This allows total deduction of **₹2,00,000**!
3. **Section 80CCD(2)**: **Employer's contribution** up to 14% of Basic+DA. This benefit is allowed in **BOTH Old and New Tax Regimes**!

#### Why consider NPS?
- Ideal for long-term retirement corpus with low fund management charges.
- At age 60, 60% of the corpus can be withdrawn completely tax-free; 40% is converted into a monthly pension (annuity)."""
    },
    "12 lakh": {
        "title": "Tax Planning for ₹12 Lakh - ₹15 Lakh Annual Salary (FY 2025-26)",
        "answer": """### Tax Planning Guide for FY 2025-26 (AY 2026-27)

#### For ₹12,00,000 Annual Salary under New Regime:
- Gross Salary: ₹12,00,000
- Standard Deduction: -₹75,000
- Net Taxable Income: ₹11,25,000
- Tax Computed before rebate: ₹52,500 (0-4L @ 0%, 4-8L @ 5%, 8-11.25L @ 10%)
- **Section 87A Rebate**: -₹52,500 (Since taxable income is under ₹12,00,000)
- **Total Tax Payable = ₹0 (ZERO TAX!)** 🎉

#### For ₹15,00,000 Annual Salary under New Regime:
- Gross Salary: ₹15,00,000
- Standard Deduction: -₹75,000
- Net Taxable Income: ₹14,25,000
- Slab Breakdown:
  - ₹0 - ₹4L: ₹0
  - ₹4L - ₹8L (5%): ₹20,000
  - ₹8L - ₹12L (10%): ₹40,000
  - ₹12L - ₹14.25L (15%): ₹33,750
- Tax before cess: **₹93,750**
- Health & Education Cess (4%): **₹3,750**
- **Total Tax = ₹97,500** (Take-home salary: ₹14,02,500)!"""
    }
}


def get_offline_tax_answer(query: str) -> Optional[Dict[str, str]]:
    """
    Matches user queries against verified Indian tax knowledge base for instant responses.
    """
    q = query.lower()

    if any(k in q for k in ["80c", "ppf", "elss", "epf", "tuition"]):
        return BUILTIN_TAX_KNOWLEDGE["80c"]
    elif any(k in q for k in ["80d", "health insurance", "mediclaim", "medical insurance"]):
        return BUILTIN_TAX_KNOWLEDGE["80d"]
    elif any(k in q for k in ["hra", "rent", "house rent"]):
        return BUILTIN_TAX_KNOWLEDGE["hra"]
    elif any(k in q for k in ["old vs new", "regime", "difference", "which is better", "which regime"]):
        return BUILTIN_TAX_KNOWLEDGE["old vs new"]
    elif any(k in q for k in ["87a", "rebate", "zero tax", "12 lakh", "12.75", "marginal relief"]):
        return BUILTIN_TAX_KNOWLEDGE["87a"]
    elif any(k in q for k in ["nps", "80ccd", "pension"]):
        return BUILTIN_TAX_KNOWLEDGE["nps"]
    elif any(k in q for k in ["15 lakh", "15l", "save tax on 12", "12l"]):
        return BUILTIN_TAX_KNOWLEDGE["12 lakh"]

    return None


def ask_taxwise_ai(question: str) -> Dict[str, Any]:
    """
    Answers tax questions using Gemini LLM if configured, or uses grounded knowledge base.
    """
    clean_question = question.strip()
    if not clean_question:
        return {"error": "Please enter a valid tax question."}

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"

    # Check offline knowledge base first for standard keywords
    offline_match = get_offline_tax_answer(clean_question)

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
                "I am your Indian Income Tax Learning Assistant for **FY 2025-26 (AY 2026-27)**. "
                "Here are some popular topics you can ask me about:\n\n"
                "- **New Regime Slabs**: 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-16L (15%), 16-20L (20%), 20-24L (25%), >24L (30%)\n"
                "- **Section 87A Rebate**: Pay ₹0 tax up to ₹12 Lakhs taxable income (up to ₹12.75 Lakhs for salaried!)\n"
                "- **Section 80C**: Investments, EPF, ELSS, PPF (up to ₹1.5 Lakh in Old Regime)\n"
                "- **Section 80D**: Health insurance deductions for self and parents\n"
                "- **HRA Exemption**: How rent allowance exemption is calculated\n"
                "- **Old vs New Regime**: Which regime is better for your salary bracket\n\n"
                "💡 *Tip: To enable live Gemini AI explanations for custom queries, add your free `GEMINI_API_KEY` to the `.env` file.*"
            ),
            "source": "TaxWise Guide",
            "ai_live": False
        }

    # Live Gemini Request
    system_instruction = """
You are TaxWise AI, an expert, friendly educational assistant specializing in Indian Income Tax for beginners, salaried professionals, and students.

Core Principles:
1. Ground answers strictly in verified Indian Income Tax rules for Financial Year 2025-26 (Assessment Year 2026-27).
2. Under the New Tax Regime (Section 115BAC) for FY 2025-26:
   - Slabs: 0-4L (0%), 4-8L (5%), 8-12L (10%), 12-16L (15%), 16-20L (20%), 20-24L (25%), Above 24L (30%).
   - Standard Deduction for salaried is ₹75,000.
   - Section 87A rebate provides full tax relief (zero tax) for taxable income up to ₹12,00,000 (meaning salaried employees pay ₹0 tax on gross income up to ₹12,75,000).
   - Marginal relief applies if taxable income slightly exceeds ₹12 Lakhs.
3. Under the Old Tax Regime:
   - Slabs: 0-2.5L (0%), 2.5-5L (5%), 5-10L (20%), Above 10L (30%).
   - Standard Deduction: ₹50,000.
   - Section 87A rebate up to ₹5,00,000 taxable income.
   - Deductions allowed: 80C (₹1.5L), 80D (₹25k-₹50k), HRA, 80CCD(1B) NPS (₹50k), Home loan interest (₹2L).
4. Keep answers beginner-friendly, structured, and easy to read using markdown headings, bullet points, and tables when helpful.
5. Always clarify that this is educational guidance and not certified chartered accountant advice.
6. Never request personal identifying information (PAN, Aadhaar, bank credentials, passwords).
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=clean_question,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1000
            )
        )

        answer_text = response.text or "I could not generate an explanation at this time. Please try again."
        return {
            "answer": answer_text,
            "source": f"Google Gemini ({model_name}) + Indian Tax Rules",
            "ai_live": True
        }

    except Exception as e:
        # If API quota is exceeded or network fails, fall back to offline knowledge base smoothly
        if offline_match:
            return {
                "answer": offline_match["answer"],
                "source": "Verified Indian Tax Knowledge Base (Fallback)",
                "ai_live": False,
                "note": "Offline knowledge base used due to API connectivity."
            }
        return {
            "answer": (
                f"### Tax Guidance\n\n"
                f"Regarding your query on: **\"{clean_question}\"**\n\n"
                f"Under Indian Income Tax rules (FY 2025-26), taxpayers can choose between the **New Regime** "
                f"(simplified, lower tax rates, ₹75,000 standard deduction, zero tax up to ₹12.75 Lakhs) or the **Old Regime** "
                f"(higher slabs, but allows deductions like 80C up to ₹1.5L, 80D up to ₹25k-₹50k, and HRA).\n\n"
                f"*Note: Live Gemini API request encountered: {str(e)[:120]}. Please check your API key in .env.*"
            ),
            "source": "TaxWise Tax Engine",
            "ai_live": False
        }
