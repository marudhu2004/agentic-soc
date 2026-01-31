import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

app = Flask(__name__)

# --- Gemini API Configuration ---
# Securely configure the API using an environment variable
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        model = None
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        print("Gemini API configured successfully.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

@app.route('/mitigate', methods=['POST'])
def mitigate_alert():
    """
    Receives a Wazuh alert and uses Gemini to suggest a mitigation plan.
    """
    if not model:
        return jsonify({"error": "Gemini API is not configured on the server."}), 500

    request_data = request.get_json()
    if not request_data or 'alert_description' not in request_data:
        return jsonify({"error": "Request body must contain 'alert_description'"}), 400

    alert_description = request_data['alert_description']

    prompt = f"""You are a senior security operations center (SOC) analyst.
    Your task is to provide a concise, actionable, step-by-step mitigation plan for the following Wazuh alert.
    Focus on immediate containment and long-term prevention.

    Wazuh Alert:
    ---
    {alert_description}
    ---
    """

    try:
        response = model.generate_content(prompt)
        mitigation_plan = response.text
        return jsonify({"suggested_mitigation": mitigation_plan})
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": f"Failed to generate mitigation plan from Gemini: {str(e)}"}), 500

if __name__ == '__main__':
    # Using 0.0.0.0 makes the app accessible from outside the Docker container
    app.run(host='0.0.0.0', port=5001, debug=True)
