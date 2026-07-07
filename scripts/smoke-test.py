#!/usr/bin/env python3
"""
Synaptix E2E Backend Smoke Test Script.

Validates health checks, login, admin dashboard counts, and student attendance
percentages against running local docker services.
"""

import sys
import urllib.request
import urllib.error
import json

SERVICES = {
    "Auth Service": "http://localhost:8001/health",
    "Academic Service": "http://localhost:8002/health",
    "Logbook Service": "http://localhost:8006/health",
    "Institution Service": "http://localhost:8007/health",
    "Workflow Service": "http://localhost:8010/health",
}

def api_call(url, data=None, token=None, method="GET"):
    headers = {
        "Content-Type": "application/json",
        "X-Tenant-ID": "00000000-0000-0000-0000-000000000001"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(
        url,
        data=req_data,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            body = e.reason
        return e.code, body
    except Exception as e:
        return 999, str(e)

def run_smoke_test():
    print("====================================================")
    print("           SYNAPTIX SYSTEM SMOKE TEST               ")
    print("====================================================")
    
    # 1. Verify Health Checks
    print("\n[1/4] Checking Backend Services Health...")
    all_healthy = True
    for name, url in SERVICES.items():
        try:
            with urllib.request.urlopen(url, timeout=3) as res:
                if res.status == 200:
                    print(f"  [OK] {name}: Healthy")
                else:
                    print(f"  [FAIL] {name}: Unhealthy (Status {res.status})")
                    all_healthy = False
        except Exception as e:
            print(f"  [FAIL] {name}: Down ({e})")
            all_healthy = False
            
    if not all_healthy:
        print("\n[ERROR] One or more backend services are down. Please run run-all.bat first.")
        sys.exit(1)
        
    # 2. Verify Admin Login & Dashboard Stats
    print("\n[2/4] Authenticating as Admin & Fetching Stats...")
    status, resp = api_call(
        "http://localhost:8001/api/v1/auth/login",
        data={"email": "admin@jmn.edu.in", "password": "Synaptix@2026", "tenant_id": "00000000-0000-0000-0000-000000000001"},
        method="POST"
    )
    if status != 200:
        print(f"  [FAIL] Admin Login Failed (Status {status}): {resp}")
        sys.exit(1)
    print("  [OK] Admin Login: Success")
    admin_token = resp["access_token"]
    
    status, stats = api_call(
        "http://localhost:8002/api/v1/dashboard/stats",
        token=admin_token
    )
    if status != 200:
        print(f"  [FAIL] Fetching Admin Dashboard Stats Failed: {stats}")
        sys.exit(1)
    print("  [OK] Dashboard Stats Loaded:")
    print(f"    - Total Students: {stats['total_students']}")
    print(f"    - Today's Attendance Rate: {stats['todays_attendance_rate']}%")
    print(f"    - Pending Logbook Reviews: {stats['pending_logbook_reviews']}")
    print(f"    - At-Risk Students: {stats['at_risk_students']}")
    
    # 3. Verify Student Login & Summaries
    print("\n[3/4] Authenticating as Student & Fetching Attendance...")
    status, resp = api_call(
        "http://localhost:8001/api/v1/auth/login",
        data={"email": "student1@jmn.edu.in", "password": "Synaptix@2026", "tenant_id": "00000000-0000-0000-0000-000000000001"},
        method="POST"
    )
    if status != 200:
        print(f"  [FAIL] Student Login Failed (Status {status}): {resp}")
        sys.exit(1)
    print("  [OK] Student Login: Success")
    student_token = resp["access_token"]
    student_id = resp["user_id"]
    
    status, summaries = api_call(
        f"http://localhost:8002/api/v1/attendance/student/{student_id}/summary",
        token=student_token
    )
    if status != 200:
        print(f"  [FAIL] Fetching Student Summaries Failed: {summaries}")
        sys.exit(1)
    print("  [OK] Attendance Summaries Loaded:")
    for item in summaries:
        eligibility = "ELIGIBLE" if item["is_eligible"] else "NOT ELIGIBLE (Shortfall)"
        print(f"    - {item['course_name']} ({item['subject_code']} - {item['attendance_category']}): "
              f"{item['attendance_pct']}% (Threshold: {item['threshold']}%) -> {eligibility}")
        
    print("\n[4/4] E2E Verification Complete! All checks passed successfully.")
    print("====================================================")

if __name__ == "__main__":
    run_smoke_test()
