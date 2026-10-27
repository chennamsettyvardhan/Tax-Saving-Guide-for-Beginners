"""
TaxWise AI - Flask Web Application
Web server exposing the tax calculation engine, regime comparison,
tax-saving recommendations, and Gemini AI assistant.
"""

import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

import tax_engine
import ai_assistant

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "taxwise-ai-hackathon-2026")


@app.route("/")
def index():
    """Renders the main TaxWise AI interactive dashboard."""
    return render_template("index.html")


@app.route("/api/calculate", methods=["POST"])
def calculate():
    """
    Calculates tax under chosen regime and generates side-by-side comparison.
    """
    try:
        data = request.get_json(silent=True) or {}
        gross_income = float(data.get("gross_income", 0.0))

        if gross_income < 0:
            return jsonify({"error": "Gross income must be a positive number."}), 400

        is_salaried = bool(data.get("is_salaried", True))
        regime = str(data.get("regime", "new")).lower()

        sec_80c = float(data.get("sec_80c", 0.0))
        sec_80d = float(data.get("sec_80d", 0.0))
        hra = float(data.get("hra_exemption", 0.0))
        nps = float(data.get("sec_80ccd_1b", 0.0))
        home_loan = float(data.get("home_loan_24b", 0.0))
        other_ded = float(data.get("other_deductions", 0.0))

        # Perform comprehensive comparison
        comparison = tax_engine.compare_regimes(
            gross_income=gross_income,
            is_salaried=is_salaried,
            sec_80c=sec_80c,
            sec_80d=sec_80d,
            hra_exemption=hra,
            sec_80ccd_1b=nps,
            home_loan_interest_24b=home_loan,
            other_deductions=other_ded
        )

        active_result = comparison["new_regime"] if regime == "new" else comparison["old_regime"]
        other_result = comparison["old_regime"] if regime == "new" else comparison["new_regime"]

        # Calculate savings compared to alternative regime
        tax_saved_vs_other = max(0.0, other_result["total_tax"] - active_result["total_tax"])

        # Smart recommendations
        tips = tax_engine.get_tax_saving_recommendations(
            gross_income=gross_income,
            sec_80c=sec_80c,
            sec_80d=sec_80d,
            sec_80ccd_1b=nps,
            current_regime=regime
        )

        return jsonify({
            "status": "success",
            "active_regime": regime,
            "active_result": active_result,
            "comparison": comparison,
            "tax_saved_vs_other": round(tax_saved_vs_other, 2),
            "recommendations": tips,
            "meta": {
                "assessment_year": "AY 2025-26 / 2026-27",
                "financial_year": "FY 2024-25 / 2025-26",
                "cess_rate": "4% Health & Education Cess"
            }
        })

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input format: {str(e)}"}), 400
    except Exception as e:
        app.logger.exception("Calculation error")
        return jsonify({"error": "An error occurred during calculation."}), 500


@app.route("/api/recommendations", methods=["POST"])
def recommendations():
    """Returns tailored tax optimization tips based on user's current numbers."""
    try:
        data = request.get_json(silent=True) or {}
        gross_income = float(data.get("gross_income", 0.0))
        sec_80c = float(data.get("sec_80c", 0.0))
        sec_80d = float(data.get("sec_80d", 0.0))
        nps = float(data.get("sec_80ccd_1b", 0.0))
        regime = str(data.get("regime", "new")).lower()

        tips = tax_engine.get_tax_saving_recommendations(
            gross_income=gross_income,
            sec_80c=sec_80c,
            sec_80d=sec_80d,
            sec_80ccd_1b=nps,
            current_regime=regime
        )
        return jsonify({"recommendations": tips})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/chat", methods=["POST"])
def chat():
    """Handles conversational questions with AI assistant."""
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()
    user_context = data.get("user_context", None)

    if not question:
        return jsonify({"error": "Please enter a question to ask TaxWise AI."}), 400

    if len(question) > 2000:
        return jsonify({"error": "Please keep your question under 2,000 characters."}), 400

    response = ai_assistant.ask_taxwise_ai(question, user_context=user_context)
    return jsonify(response)


@app.route("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "TaxWise AI", "version": "1.0.0"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
