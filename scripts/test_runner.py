import subprocess
import sys
from pathlib import Path

# Service test directories
SERVICES = [
    "services/shared/tests",
    "services/listing-service/tests",
    "services/matching-service/tests",
    "services/notification-service/tests",
    "services/logistics-service/tests",
    "services/analytics-service/tests",
    "services/expiry-job/tests",
]

def main():
    root_dir = Path(__file__).resolve().parent.parent
    total_passed = 0
    total_failed = 0
    failures = []

    print("==================================================================")
    print("      FOODBRIDGE CLOUD-NATIVE PLATFORM - FULL TEST SUITE          ")
    print("==================================================================")

    for svc in SERVICES:
        svc_path = root_dir / svc
        if not svc_path.exists():
            continue

        print(f"\n---> Running tests for: {svc}")
        cmd = [sys.executable, "-m", "pytest", str(svc_path), "-v", "--no-header"]
        result = subprocess.run(cmd, cwd=str(root_dir))

        if result.returncode == 0:
            print(f"  [PASS] {svc}")
        else:
            print(f"  [FAIL] {svc}")
            failures.append(svc)

    print("\n==================================================================")
    if not failures:
        print(" [SUCCESS] ALL MICROSERVICE UNIT & INTEGRATION TEST SUITES PASSED!")
        print("==================================================================")
        sys.exit(0)
    else:
        print(f" [FAILED] {len(failures)} test suite(s) failed: {failures}")
        print("==================================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
