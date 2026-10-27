import os
import subprocess
import sys
import time
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "services" / "shared") not in sys.path:
    sys.path.insert(0, str(root_dir / "services" / "shared"))

# 1. Seed data first
try:
    from simulator.seed_data import seed_database
    seed_database()
except Exception as e:
    print(f"Warning seeding database: {e}")

# 2. Load root .env into env dict
env = os.environ.copy()
env_file = root_dir / ".env"
if env_file.exists():
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k and v:
                env[k] = v  # .env always wins over os.environ


# 3. Launch each microservice with cwd set to its directory
services = [
    ("listing-service", 8001),
    ("matching-service", 8002),
    ("notification-service", 8003),
    ("logistics-service", 8004),
    ("analytics-service", 8005),
    ("expiry-job", 8006),
]

processes = []

print("==================================================================")
print("      FOODBRIDGE CLOUD-NATIVE BACKEND DEV SERVER MESH             ")
print("==================================================================")

for name, port in services:
    service_path = root_dir / "services" / name
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    svc_env = env.copy()
    svc_env["PYTHONPATH"] = f"{service_path};{root_dir / 'services' / 'shared'}"
    p = subprocess.Popen(cmd, cwd=str(service_path), env=svc_env)
    processes.append((name, p))
    print(f"  [RUNNING] {name} on http://127.0.0.1:{port}")

gemini_status = "[OK]" if env.get("GEMINI_API_KEY") else "[MISSING] -- set GEMINI_API_KEY in .env"
print("==================================================================")
print(f"  Gemini AI key loaded: {gemini_status}")
print("==================================================================")
print("Press Ctrl+C to terminate all services.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down dev servers...")
    for name, p in processes:
        p.terminate()
