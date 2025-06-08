
# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 19:09:12 2025
Refactored for GET, PATCH, POST including Indigo FlightSearch format
"""

import json
import requests
from fpdf import FPDF

# Global Variables
Indigo_api_host_url = "http://your-api-host:port"  # <-- Replace this with your actual API base URL
Indigo_Api_json_files = ["test_data.json", "Indigo-FlighSearch.json"]
Indigo_contract_test_report_file = "Flight-search-test-report.pdf"


# Function To Run the Actual Test
def contract_api_test(method, url, headers, body, expected_status, expected_errors=None, query=None):
    full_url = Indigo_api_host_url + url
    if query:
        full_url += "?" + "&".join(f"{k}={v}" for k, v in query.items() if v)

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
def api_tests(file_list):
    results = []

    for input_file in file_list:
        with open(input_file, "r", encoding="utf-8") as f:
            test_cases = json.load(f)

        for case in test_cases:
            method = case.get("httpVerb") or case.get("sampleRequest", {}).get("method")
            if method not in ["GET", "PATCH", "POST", "PUT", "DELETE"]:
                continue

            url = case.get("route") or case["sampleRequest"].get("url")

            # Happy Path
            if "sampleRequest" in case and "happyPathTest" in case:
                req = case["sampleRequest"]
                result = contract_api_test(
                    method=method,
                    url=url,
                    headers=req.get("headers", {}),
                    body=req.get("body", {}),
                    query=req.get("query", {}),
                    expected_status=case["happyPathTest"]["expectedStatusCode"]
                )
                result["scenario"] = "Happy Path"
                results.append(result)

            elif "sampleRequest" in case and "happyPathTests" in case:
                for happy in case["happyPathTests"]:
                    req = case["sampleRequest"]
                    result = contract_api_test(
                        method=method,
                        url=url,
                        headers=req.get("headers", {}),
                        body=req.get("body", {}),
                        query=req.get("query", {}),
                        expected_status=happy["expectedStatusCode"]
                    )
                    result["scenario"] = happy.get("summary", "Happy Path")
                    results.append(result)

            # Sad Path
            for sad in case.get("sadPathTests", []):
                bad = sad.get("badRequest") or sad.get("sampleRequest", {})
                expected = sad.get("expectedErrorResponse", {})
                result = contract_api_test(
                    method=method,
                    url=url,
                    headers=bad.get("headers", {}),
                    body=bad.get("body", {}),
                    query=bad.get("query", {}),
                    expected_status=expected.get("statusCode"),
                    expected_errors=expected
                )
                result["scenario"] = sad.get("scenario", "Sad Path")
                results.append(result)

    return results


# Generate PDF Report
def generate_pdf_report(results, report_file):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="API Contract Test Report", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(5)

    for res in results:
        scenario = res["scenario"]
        method = res["method"]
        url = res["url"]
        status_code = res["status_code"]
        passed = res["passed"]
        errors = ", ".join(res["errors"]) if res["errors"] else "None"

        pdf.multi_cell(0, 10, f"Scenario      : {scenario}\n"
                              f"Method        : {method}\n"
                              f"URL           : {url}\n"
                              f"Status Code   : {status_code}\n"
                              f"Passed        : {passed}\n"
                              f"Errors        : {errors}\n", border=1)

    pdf.output(report_file)
    print(f"✅ Test report saved to {report_file}")


# Main Function
def main():
    results = api_tests(Indigo_Api_json_files)
    generate_pdf_report(results, Indigo_contract_test_report_file)

# Main execution
if __name__ == "__main__":
    main()
