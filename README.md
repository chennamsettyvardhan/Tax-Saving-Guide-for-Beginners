# TaxWise AI - Tax Saving Guide for Beginners 🇮🇳

An AI-powered, beginner-friendly Indian Income Tax web application that calculates tax liability, compares the **Old vs. New Tax Regime** (FY 2024-25 / FY 2025-26), visualizes deductions, and provides educational tax guidance powered by **Google Gemini** and a grounded tax knowledge base.

---

## 🚀 Key Features

1. **Interactive Income Tax Calculator**:
   - Computes tax for salaried individuals and professionals.
   - Handles standard deduction (₹75,000 for New Regime / ₹50,000 for Old Regime).
   - Accurately computes Section 87A rebate (zero tax up to ₹12.75 Lakhs under New Regime for salaried) and marginal relief.
   - Surcharge and 4% Health & Education cess.

2. **Old vs. New Tax Regime Comparison**:
   - Side-by-side comparison table.
   - Direct savings indicator showing which regime saves more money and the exact amount saved.
   - Slab-by-slab tax breakdown.

3. **Smart Tax Breakdown Donut Chart**:
   - Visual distribution of Take-Home Salary, Total Tax Payable, and Deductions/Exemptions rendered via Chart.js.

4. **Tax-Saving Recommendations Engine**:
   - Analyzes unutilized limits in Section 80C (up to ₹1.5L), Section 80D (Health Insurance up to ₹25k/₹50k), and Section 80CCD(1B) (NPS extra ₹50k).
   - Shows potential tax savings if unused headroom is invested.

5. **AI Tax Assistant ("Ask TaxWise AI")**:
   - Powered by Google Gemini (`google-genai` SDK) with domain guardrails.
   - Grounded Indian Tax Knowledge Base for instant responses to common questions (80C, 80D, HRA, 87A, NPS, ELSS vs PPF, etc.).
   - Pre-configured quick prompt chips for common beginner queries.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ / 3.14, Flask, python-dotenv
- **AI Integration**: Google GenAI SDK (`google-genai`), Gemini 2.5 Flash
- **Frontend**: HTML5, Vanilla CSS3 (Custom design system), Vanilla JavaScript
- **Data Visualization**: Chart.js

---

## 📦 Project Structure

```text
TaxWise AI/
├── app.py                 # Flask server & REST API endpoints
├── tax_engine.py          # Deterministic Indian income tax calculation engine
├── ai_assistant.py        # Gemini AI assistant & verified knowledge base
├── requirements.txt       # Python dependencies (Flask, google-genai, python-dotenv)
├── .env.example           # Environment template
├── .env                   # Local environment configuration
├── .gitignore             # Standard git exclusions
├── README.md              # Project documentation
├── templates/
│   └── index.html         # Modern finance dashboard single-page interface
└── static/
    ├── css/
    │   └── style.css      # Cohesive design system & responsive styling
    └── js/
        └── app.js         # Real-time reactivity, Chart.js updates, chat controller
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher installed ([Download Python](https://www.python.org/downloads/)).
- (Optional) Free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 2. Setup Virtual Environment & Install Dependencies
Open a terminal in the project directory:

```bash
# Create virtual environment (optional but recommended)
python -m venv .venv

# Activate on Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Or on Windows Command Prompt:
.\.venv\Scripts\activate.bat

# Install dependencies:
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
PORT=5000
```
> *Note: If you don't have an API key yet, the app runs smoothly with the built-in verified Indian tax knowledge base!*

### 4. Run the Application
```bash
python app.py
```

Open your browser at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## ⚖️ Disclaimer

TaxWise AI is designed for educational and informational purposes only. Income tax liability may vary based on individual circumstances, special rate income, and updates from the Central Board of Direct Taxes (CBDT). Users should verify specific calculations with official government portals ([incometax.gov.in](https://www.incometax.gov.in)) or a certified Chartered Accountant.
