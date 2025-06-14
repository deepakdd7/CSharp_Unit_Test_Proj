# -*- coding: utf-8 -*-
"""
Created on Sun Jun  8 19:09:12 2025
Refactored for GET, PATCH, POST including Indigo FlightSearch format
"""

import json
import argparse
import requests
from fpdf import FPDF
from typing import Optional

# Global Variables
Indigo_api_host_url = "https://api-6epartner-qa.goindigo.in/flightsearch"
Indigo_Api_json_files = ["Indigo-FlightSearch.json"]
Indigo_contract_test_report_file = "Flight-search-test-report.pdf"


# Function To Parse Command Line Arguments
def parse_argements(arg: Optional[str] = None) -> argparse.Namespace:
    
    parser = argparse.ArgumentParser(
        description="Indigo Microservice API Contract Testing"
    )
        
    parser.add_argument(
        "--add-response-body-on-success",
        action="store_true",
        help="Add Request And Response Body On Success (ErrorCode: 200) (default: False)"
    )
           
    args = parser.parse_args()
    
    return args

# Function To Run the Actual Test
def contract_api_test(method, url, headers, body, expected_status, expected_errors=None, query=None):
    full_url = Indigo_api_host_url + url
    if query:
        full_url += "?" + "&".join(f"{k}={v}" for k, v in query.items() if v)

    try:
        response = requests.request(method, full_url, headers=headers, json=body if body else None)
        try:
            resp_json = response.json()
            resp_body = json.dumps(resp_json, indent=2)
        except ValueError:
            resp_body = response.text or "Empty/Invalid JSON"
            resp_json = {}

        result = {
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "passed": response.status_code == expected_status,
            "errors": [],
            "request_body": json.dumps(body or {}, indent=2),
            "response_body": resp_body
        }

        if "errors" in resp_json and resp_json["errors"]:
            result["errors"].append("Non-empty 'errors' found in response")
            result["passed"] = False
        if expected_errors and resp_json.get("errors") != expected_errors.get("errors"):
            result["errors"].append("Error mismatch in response body")
            result["passed"] = False

        return result

    except Exception as e:
        return {
            "method": method,
            "url": url,
            "status_code": "N/A",
            "passed": False,
            "errors": [str(e)],
            "request_body": json.dumps(body or {}, indent=2),
            "response_body": "No response received"
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
def generate_pdf_report(args, results, report_file):
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
        req_body = res.get("request_body", "N/A")
        res_body = res.get("response_body", "N/A")

        if not args.add_response_body_on_success and status_code == 200:
            pdf.multi_cell(0, 10, f"Scenario      : {scenario}\n"
                                  f"Method        : {method}\n"
                                  f"URL           : {url}\n"
                                  f"Status Code   : {status_code}\n"
                                  f"Passed        : {passed}\n"
                                  f"Errors        : {errors}\n", border=1)
        else:
            pdf.multi_cell(0, 10, f"Scenario      : {scenario}\n"
                                  f"Method        : {method}\n"
                                  f"URL           : {url}\n"
                                  f"Status Code   : {status_code}\n"
                                  f"Passed        : {passed}\n"
                                  f"Errors        : {errors}\n"
                                  f"Request Body  : {req_body}\n"
                                  f"Response Body : {res_body}\n", border=1)

    pdf.output(report_file)
    print(f"✅ Test report saved to {report_file}")


# Main Function
def main():
    args = parse_argements()
    results = api_tests(Indigo_Api_json_files)
    generate_pdf_report(args, results, Indigo_contract_test_report_file)

# Main execution
if __name__ == "__main__":
    main()