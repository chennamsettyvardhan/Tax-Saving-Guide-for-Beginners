"""
TaxWise AI - Tax Calculation Engine
Accurate, deterministic Indian Income Tax computation engine for:
- Financial Year 2024-25 & 2025-26 (Assessment Year 2025-26 & 2026-27)
- Supports Old Tax Regime vs New Tax Regime (Section 115BAC)
- Verified slabs, standard deductions, 87A rebate & marginal relief, cess (4%), and tax-saving optimization
"""

from typing import Dict, List, Any


def calculate_surcharge(tax: float, taxable_income: float, is_new_regime: bool = True) -> float:
    """
    Computes surcharge based on income brackets.
    New regime caps surcharge at 25%, Old regime goes up to 37%.
    """
    if taxable_income <= 5_000_000:
        return 0.0
    elif taxable_income <= 10_000_000:
        return tax * 0.10
    elif taxable_income <= 20_000_000:
        return tax * 0.15
    elif taxable_income <= 50_000_000:
        return tax * 0.25
    else:
        # > 5 Crore
        return tax * (0.25 if is_new_regime else 0.37)


def calculate_new_regime(
    gross_income: float,
    is_salaried: bool = True,
    nps_employer_80ccd2: float = 0.0
) -> Dict[str, Any]:
    """
    Computes Indian Income Tax under the New Tax Regime (Section 115BAC)
    Updated as per Union Budget 2024-25 / 2025-26:
    - Standard deduction for salaried: ₹75,000
    - Slabs:
        0 - 3,00,000        : 0%
        3,00,001 - 7,00,000 : 5%
        7,00,001 - 10,00,000: 10%
        10,00,001 - 12,00,000: 15%
        12,00,001 - 15,00,000: 20%
        Above 15,00,000     : 30%
    - Section 87A Rebate: Full rebate up to ₹25,000 if taxable income <= ₹7,00,000 (tax = ₹0)
    - Marginal relief under Section 87A: Tax before cess cannot exceed (Taxable Income - ₹7,00,000)
    """
    gross = max(0.0, float(gross_income))
    std_deduction = 75000.0 if is_salaried else 0.0
    allowed_employer_nps = max(0.0, float(nps_employer_80ccd2))

    total_deductions = min(gross, std_deduction + allowed_employer_nps)
    taxable_income = max(0.0, gross - total_deductions)

    slabs = [
        (0, 300000, 0.00, "Up to ₹3,00,000"),
        (300000, 700000, 0.05, "₹3,00,001 to ₹7,00,000"),
        (700000, 1000000, 0.10, "₹7,00,001 to ₹10,00,000"),
        (1000000, 1200000, 0.15, "₹10,00,001 to ₹12,00,000"),
        (1200000, 1500000, 0.20, "₹12,00,001 to ₹15,00,000"),
        (1500000, float("inf"), 0.30, "Above ₹15,00,000"),
    ]

    breakdown: List[Dict[str, Any]] = []
    base_tax = 0.0

    for lower, upper, rate, label in slabs:
        if taxable_income > lower:
            taxable_in_slab = min(taxable_income, upper) - lower
            slab_tax = taxable_in_slab * rate
            base_tax += slab_tax
            breakdown.append({
                "slab": label,
                "rate": f"{int(rate * 100)}%",
                "taxable_amount": round(taxable_in_slab, 2),
                "tax": round(slab_tax, 2)
            })
        else:
            breakdown.append({
                "slab": label,
                "rate": f"{int(rate * 100)}%",
                "taxable_amount": 0.0,
                "tax": 0.0
            })

    # Section 87A Rebate & Marginal Relief
    rebate_87a = 0.0
    marginal_relief = 0.0
    tax_after_rebate = base_tax

    if taxable_income <= 700000.0:
        # Full rebate under 87A
        rebate_87a = base_tax
        tax_after_rebate = 0.0
    elif taxable_income > 700000.0:
        # Marginal relief: Tax before cess cannot exceed income over ₹7,00,000
        excess_income = taxable_income - 700000.0
        if base_tax > excess_income:
            marginal_relief = base_tax - excess_income
            tax_after_rebate = excess_income

    surcharge = calculate_surcharge(tax_after_rebate, taxable_income, is_new_regime=True)
    cess = (tax_after_rebate + surcharge) * 0.04
    total_tax = tax_after_rebate + surcharge + cess
    take_home = max(0.0, gross - total_tax)
    effective_rate = (total_tax / gross * 100.0) if gross > 0 else 0.0

    return {
        "regime": "new",
        "regime_name": "New Tax Regime (FY 2025-26)",
        "gross_income": round(gross, 2),
        "standard_deduction": round(std_deduction, 2),
        "other_deductions": round(allowed_employer_nps, 2),
        "total_deductions": round(total_deductions, 2),
        "taxable_income": round(taxable_income, 2),
        "base_tax": round(base_tax, 2),
        "rebate_87a": round(rebate_87a, 2),
        "marginal_relief": round(marginal_relief, 2),
        "tax_after_rebate": round(tax_after_rebate, 2),
        "surcharge": round(surcharge, 2),
        "cess": round(cess, 2),
        "total_tax": round(total_tax, 2),
        "take_home": round(take_home, 2),
        "effective_rate": round(effective_rate, 2),
        "slab_breakdown": breakdown,
        "features": [
            "Increased Standard Deduction of ₹75,000 for salaried individuals",
            "Zero tax up to ₹7.75 Lakhs for salaried individuals (due to ₹75k std deduction + ₹7L rebate)",
            "Concessional tax slabs with lower tax rates across all brackets",
            "No paperwork or proof of investments required"
        ]
    }


def calculate_old_regime(
    gross_income: float,
    is_salaried: bool = True,
    sec_80c: float = 0.0,
    sec_80d: float = 0.0,
    hra_exemption: float = 0.0,
    sec_80ccd_1b: float = 0.0,
    home_loan_interest_24b: float = 0.0,
    other_deductions: float = 0.0
) -> Dict[str, Any]:
    """
    Computes Indian Income Tax under the Old Tax Regime:
    - Standard deduction for salaried: ₹50,000
    - Section 80C (PPF, EPF, ELSS, Life Insurance, Tuition fee): Max ₹1,50,000
    - Section 80D (Health Insurance): Up to ₹25,000 (self/family) / ₹50,000 (parents)
    - Section 10(13A) HRA Exemption
    - Section 80CCD(1B) NPS: Max ₹50,000
    - Section 24(b) Home loan interest: Max ₹2,00,000
    - Slabs (General Individual < 60 yrs):
        0 - 2,50,000        : 0%
        2,50,001 - 5,00,000 : 5%
        5,00,001 - 10,00,000: 20%
        Above 10,00,000     : 30%
    - Section 87A Rebate: Full rebate up to ₹12,500 if taxable income <= ₹5,00,000 (tax = ₹0)
    """
    gross = max(0.0, float(gross_income))
    std_deduction = 50000.0 if is_salaried else 0.0

    # Capped deductions
    c_ded = min(150000.0, max(0.0, float(sec_80c)))
    d_ded = min(100000.0, max(0.0, float(sec_80d)))  # Self (up to 50k) + Parents (up to 50k)
    hra_ded = max(0.0, float(hra_exemption))
    nps_ded = min(50000.0, max(0.0, float(sec_80ccd_1b)))
    home_loan_ded = min(200000.0, max(0.0, float(home_loan_interest_24b)))
    other_ded = max(0.0, float(other_deductions))

    itemized_deductions = c_ded + d_ded + hra_ded + nps_ded + home_loan_ded + other_ded
    total_deductions = min(gross, std_deduction + itemized_deductions)
    taxable_income = max(0.0, gross - total_deductions)

    slabs = [
        (0, 250000, 0.00, "Up to ₹2,50,000"),
        (250000, 500000, 0.05, "₹2,50,001 to ₹5,00,000"),
        (500000, 1000000, 0.20, "₹5,00,001 to ₹10,00,000"),
        (1000000, float("inf"), 0.30, "Above ₹10,00,000"),
    ]

    breakdown: List[Dict[str, Any]] = []
    base_tax = 0.0

    for lower, upper, rate, label in slabs:
        if taxable_income > lower:
            taxable_in_slab = min(taxable_income, upper) - lower
            slab_tax = taxable_in_slab * rate
            base_tax += slab_tax
            breakdown.append({
                "slab": label,
                "rate": f"{int(rate * 100)}%",
                "taxable_amount": round(taxable_in_slab, 2),
                "tax": round(slab_tax, 2)
            })
        else:
            breakdown.append({
                "slab": label,
                "rate": f"{int(rate * 100)}%",
                "taxable_amount": 0.0,
                "tax": 0.0
            })

    # Section 87A Rebate for Old Regime (Threshold: ₹5,00,000)
    rebate_87a = 0.0
    tax_after_rebate = base_tax

    if taxable_income <= 500000.0:
        rebate_87a = min(12500.0, base_tax)
        tax_after_rebate = max(0.0, base_tax - rebate_87a)

    surcharge = calculate_surcharge(tax_after_rebate, taxable_income, is_new_regime=False)
    cess = (tax_after_rebate + surcharge) * 0.04
    total_tax = tax_after_rebate + surcharge + cess
    take_home = max(0.0, gross - total_tax)
    effective_rate = (total_tax / gross * 100.0) if gross > 0 else 0.0

    return {
        "regime": "old",
        "regime_name": "Old Tax Regime",
        "gross_income": round(gross, 2),
        "standard_deduction": round(std_deduction, 2),
        "deductions_detail": {
            "sec_80c": round(c_ded, 2),
            "sec_80d": round(d_ded, 2),
            "hra_exemption": round(hra_ded, 2),
            "sec_80ccd_1b": round(nps_ded, 2),
            "home_loan_24b": round(home_loan_ded, 2),
            "other_deductions": round(other_ded, 2),
        },
        "itemized_deductions": round(itemized_deductions, 2),
        "total_deductions": round(total_deductions, 2),
        "taxable_income": round(taxable_income, 2),
        "base_tax": round(base_tax, 2),
        "rebate_87a": round(rebate_87a, 2),
        "marginal_relief": 0.0,
        "tax_after_rebate": round(tax_after_rebate, 2),
        "surcharge": round(surcharge, 2),
        "cess": round(cess, 2),
        "total_tax": round(total_tax, 2),
        "take_home": round(take_home, 2),
        "effective_rate": round(effective_rate, 2),
        "slab_breakdown": breakdown,
        "features": [
            "Allows major Chapter VI-A deductions (80C, 80D, NPS 80CCD, HRA, Home Loan Interest)",
            "Standard Deduction of ₹50,000 for salaried individuals",
            "Zero tax up to ₹5.5 Lakhs for salaried individuals with basic standard deduction",
            "Beneficial for individuals with heavy investments, rent payments, and home loans"
        ]
    }


def compare_regimes(
    gross_income: float,
    is_salaried: bool = True,
    sec_80c: float = 0.0,
    sec_80d: float = 0.0,
    hra_exemption: float = 0.0,
    sec_80ccd_1b: float = 0.0,
    home_loan_interest_24b: float = 0.0,
    other_deductions: float = 0.0
) -> Dict[str, Any]:
    """
    Compares Old and New regimes side-by-side, determining the optimal choice and tax savings.
    """
    new_res = calculate_new_regime(
        gross_income=gross_income,
        is_salaried=is_salaried
    )
    old_res = calculate_old_regime(
        gross_income=gross_income,
        is_salaried=is_salaried,
        sec_80c=sec_80c,
        sec_80d=sec_80d,
        hra_exemption=hra_exemption,
        sec_80ccd_1b=sec_80ccd_1b,
        home_loan_interest_24b=home_loan_interest_24b,
        other_deductions=other_deductions
    )

    old_tax = old_res["total_tax"]
    new_tax = new_res["total_tax"]
    diff = abs(old_tax - new_tax)

    if new_tax < old_tax:
        recommendation = "new"
        savings = round(old_tax - new_tax, 2)
        headline = f"New Tax Regime saves you ₹{savings:,.0f}"
        advice = (
            f"You will pay ₹{new_tax:,.0f} under the New Regime compared to ₹{old_tax:,.0f} "
            f"under the Old Regime, saving ₹{savings:,.0f}. The New Regime offers lower tax rates "
            f"and a higher ₹75,000 standard deduction."
        )
    elif old_tax < new_tax:
        recommendation = "old"
        savings = round(new_tax - old_tax, 2)
        headline = f"Old Tax Regime saves you ₹{savings:,.0f}"
        advice = (
            f"You will pay ₹{old_tax:,.0f} under the Old Regime compared to ₹{new_tax:,.0f} "
            f"under the New Regime, saving ₹{savings:,.0f}. Your total deductions of "
            f"₹{old_res['total_deductions']:,.0f} effectively reduced your taxable income."
        )
    else:
        recommendation = "equal"
        savings = 0.0
        headline = "Both regimes result in identical tax"
        advice = "Tax liability is equal under both regimes. The New Regime is typically simpler with zero documentation."

    # Compute break-even deduction needed for Old Regime to match New Regime
    # General rule of thumb: break-even point for deduction
    return {
        "gross_income": gross_income,
        "is_salaried": is_salaried,
        "recommended_regime": recommendation,
        "tax_saved": savings,
        "headline": headline,
        "advice": advice,
        "new_regime": new_res,
        "old_regime": old_res
    }


def get_tax_saving_recommendations(
    gross_income: float,
    sec_80c: float = 0.0,
    sec_80d: float = 0.0,
    sec_80ccd_1b: float = 0.0,
    current_regime: str = "new"
) -> List[Dict[str, Any]]:
    """
    Analyzes unutilized deduction headroom and suggests high-impact tax-saving avenues.
    """
    tips = []

    # 1. Section 80C analysis (Cap: 1.5 Lakhs)
    c_used = min(150000.0, max(0.0, float(sec_80c)))
    c_gap = 150000.0 - c_used
    if c_gap > 0:
        # Approximate tax bracket based on income
        marginal_tax_rate = 0.30 if gross_income > 1000000 else (0.20 if gross_income > 500000 else 0.05)
        potential_saving = c_gap * marginal_tax_rate * 1.04
        tips.append({
            "section": "Section 80C",
            "title": "Maximize Section 80C Deductions",
            "gap": round(c_gap, 2),
            "potential_saving": round(potential_saving, 2),
            "description": f"You have ₹{c_gap:,.0f} unutilized limit out of ₹1,50,000.",
            "options": ["ELSS Mutual Funds (3-year lock-in)", "Public Provident Fund (PPF)", "Employees' Provident Fund (EPF)", "Term Life Insurance Premium"],
            "applicability": "Old Tax Regime only"
        })

    # 2. Section 80CCD(1B) NPS analysis (Extra ₹50,000)
    nps_used = min(50000.0, max(0.0, float(sec_80ccd_1b)))
    nps_gap = 50000.0 - nps_used
    if nps_gap > 0:
        marginal_tax_rate = 0.30 if gross_income > 1000000 else 0.20
        potential_saving = nps_gap * marginal_tax_rate * 1.04
        tips.append({
            "section": "Section 80CCD(1B)",
            "title": "Invest in National Pension System (NPS)",
            "gap": round(nps_gap, 2),
            "potential_saving": round(potential_saving, 2),
            "description": f"Additional ₹50,000 deduction exclusively for Tier-1 NPS over and above Section 80C.",
            "options": ["NPS Tier-1 Account for retirement planning with market-linked equity/debt growth"],
            "applicability": "Old Tax Regime only"
        })

    # 3. Section 80D Health Insurance (₹25,000 self + ₹25,000/₹50,000 parents)
    d_used = min(25000.0, max(0.0, float(sec_80d)))
    d_gap = 25000.0 - d_used
    if d_gap > 0:
        marginal_tax_rate = 0.30 if gross_income > 1000000 else 0.20
        potential_saving = d_gap * marginal_tax_rate * 1.04
        tips.append({
            "section": "Section 80D",
            "title": "Health Insurance for Self & Family",
            "gap": round(d_gap, 2),
            "potential_saving": round(potential_saving, 2),
            "description": f"Deduction of up to ₹25,000 for self/family + up to ₹50,000 for senior citizen parents.",
            "options": ["Comprehensive Health Insurance cover", "Preventive Health Check-up (up to ₹5,000 within the limit)"],
            "applicability": "Old Tax Regime only"
        })

    # 4. New Regime Benefit
    tips.append({
        "section": "New Regime Benefit",
        "title": "Switch to New Tax Regime (Section 115BAC)",
        "gap": 0.0,
        "potential_saving": 0.0,
        "description": "If your total deductions (80C, 80D, HRA) are less than ~₹3.75 - 4 Lakhs, the New Regime provides lower tax slabs and an automatic ₹75,000 standard deduction without needing any investment proofs.",
        "options": ["Zero investment lock-in", "Immediate higher monthly take-home pay", "Streamlined tax filing"],
        "applicability": "New Tax Regime"
    })

    return tips
