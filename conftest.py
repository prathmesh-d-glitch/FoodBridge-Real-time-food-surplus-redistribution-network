import sys
from pathlib import Path


def pytest_runtest_setup(item):
    """Dynamically scopes `app` imports to each respective microservice directory
    so that multi-service test suites run cleanly in a single pytest invocation.
    """
    for key in list(sys.modules.keys()):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]

    fspath_str = str(item.fspath)
    services = [
        "listing-service",
        "matching-service",
        "notification-service",
        "logistics-service",
        "analytics-service",
        "expiry-job",
    ]

    for service in services:
        if service in fspath_str:
            service_root = str(Path(__file__).parent / "services" / service)
            if service_root in sys.path:
                sys.path.remove(service_root)
            sys.path.insert(0, service_root)
            break
