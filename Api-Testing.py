# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 19:09:12 2025

@author: root
"""

import json
import requests
from fpdf import FPDF

# Global Variables
Indigo_api_host_url = "http://your-api-host:port"  # <-- Replace this with your actual API base URL
Indigo_Api_json_file = "Flight-search.json"
Indigo_contract_test_report_file = "Flight-search-test-report.pdf"


# Function To Run the Actual Test
def contract_api_test(method, url, headers, body, expected_status, expected_errors=None):
    full_url = Indigo_api_host_url + url
    try:
        response = requests.request(method, full_url, headers=headers, json=body if body else None)
        result = {
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "passed": response.status_code == expected_status,
            "errors": []
        }

        try:
            resp_json = response.json()
            if "errors" in resp_json and resp_json["errors"]:
                result["errors"].append("Non-empty 'errors' found in response")
                result["passed"] = False
            if expected_errors and resp_json.get("errors") != expected_errors.get("errors"):
                result["errors"].append("Error mismatch in response body")
                result["passed"] = False
        except Exception as e:
            result["errors"].append(f"Response JSON parse error: {str(e)}")
            result["passed"] = False

        return result

    except Exception as e:
        return {
            "method": method,
            "url": url,
            "status_code": "N/A",
            "passed": False,
            "errors": [str(e)]
        }


# Function To Process Test And Send Request To Test
def api_tests(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    results = []

    for case in test_cases:
        method = case["sampleRequest"]["method"]
        if method not in ["GET", "PATCH"]:
            continue

        happy = case["sampleRequest"]
        result = contract_api_test(
            method=happy["method"],
            url=happy["url"],
            headers=happy.get("headers", {}),
            body=happy.get("body", {}),
            expected_status=case["happyPathTest"]["expectedStatusCode"]
        )
        result["scenario"] = "Happy Path"
        results.append(result)

        for sad in case.get("sadPathTests", []):
            sad_req = sad["sampleRequest"]
            result = contract_api_test(
                method=sad_req["method"],
                url=sad_req["url"],
                headers=sad_req.get("headers", {}),
                body=sad_req.get("body", {}),
                expected_status=sad["expectedErrorResponse"]["statusCode"],
                expected_errors=sad.get("expectedErrorResponse")
            )
            result["scenario"] = sad["scenario"]
            results.append(result)

    return results


def generate_pdf_report(results, Indigo_contract_test_report_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="API Contract Test Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)

    for res in results:
        pdf.multi_cell(0, 10, f"""
Scenario      : {res["scenario"]}
Method        : {res["method"]}
URL           : {res["url"]}
Status Code   : {res["status_code"]}
Passed        : {res["passed"]}
Errors        : {", ".join(res["errors"]) if res["errors"] else "None"}
        """, border=1)

    pdf.output(Indigo_contract_test_report_file)
    print(f"✅ Test report saved to {Indigo_contract_test_report_file}")


# Main Function
def main():
       
    results = api_tests(Indigo_Api_json_file)
    generate_pdf_report(results, Indigo_contract_test_report_file)

# Main execution
if __name__ == "__main__":
    main()