import requests
import time
import statistics

BASE_URL = "http://localhost:5000"
TEST_DURATION = 600  # seconds
IMAGE_PATH = "test.jpg"

upload_latencies = []
download_latencies = []

start_time = time.perf_counter()

total_requests = 0
cycle_attempts = 0
successful_cycles = 0

upload_failures = 0
download_failures = 0


while time.perf_counter() - start_time < TEST_DURATION:

    cycle_attempts += 1

    # ---- Upload ----
    try:
        with open(IMAGE_PATH, "rb") as f:
            files = {"file": f}

            t1 = time.perf_counter()

            total_requests += 1

            r = requests.post(
                BASE_URL + "/upload",
                files=files,
                timeout=10
            )

            upload_time = time.perf_counter() - t1

    except Exception:
        upload_failures += 1
        continue

    if r.status_code != 201:
        upload_failures += 1
        continue

    upload_latencies.append(upload_time)

    try:
        image_id = r.json()["image_id"]
    except Exception:
        upload_failures += 1
        continue

    # ---- Download ----
    try:
        t2 = time.perf_counter()

        total_requests += 1

        d = requests.get(
            BASE_URL + f"/images/{image_id}",
            timeout=10
        )

        download_time = time.perf_counter() - t2

    except Exception:
        download_failures += 1
        continue

    if d.status_code == 200:
        download_latencies.append(download_time)
        successful_cycles += 1
    else:
        download_failures += 1


# =============================
# Metrics Calculation
# =============================

success_rate = (successful_cycles / cycle_attempts) if cycle_attempts else 0


def percentile(data, p):
    if not data:
        return 0
    data = sorted(data)
    k = int((len(data) - 1) * p / 100)
    return data[k]


print("\n==== RESULTS ====")
print(f"Cycle Attempts: {cycle_attempts}")
print(f"Successful Upload+Download Cycles: {successful_cycles}")
print(f"Total Requests: {total_requests}")
print(f"Test Duration: {TEST_DURATION} seconds")

print("\nFAILURES:")
print(f"Upload Failures: {upload_failures}")
print(f"Download Failures: {download_failures}")

print(f"\nSuccess Rate: {success_rate*100:.2f}%")

# Upload metrics
if upload_latencies:
    print("\nUPLOAD LATENCY:")
    print(f"Avg: {statistics.mean(upload_latencies):.4f}s")

    if len(upload_latencies) > 1:
        print(f"Std Dev: {statistics.stdev(upload_latencies):.4f}s")

    print(f"P95: {percentile(upload_latencies, 95):.4f}s")
    print(f"P99: {percentile(upload_latencies, 99):.4f}s")


# Download metrics
if download_latencies:
    print("\nDOWNLOAD LATENCY:")
    print(f"Avg: {statistics.mean(download_latencies):.4f}s")

    if len(download_latencies) > 1:
        print(f"Std Dev: {statistics.stdev(download_latencies):.4f}s")

    print(f"P95: {percentile(download_latencies, 95):.4f}s")
    print(f"P99: {percentile(download_latencies, 99):.4f}s")


throughput = total_requests / TEST_DURATION if TEST_DURATION else 0
print(f"\nThroughput: {throughput:.2f} requests/sec")
print(f"Successful Uploads: {len(upload_latencies)}")
print(f"Successful Downloads: {len(download_latencies)}")