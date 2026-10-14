import time
import json
import urllib.request
import statistics

OLLAMA_API = "http://127.0.0.1:11434"
PROMPT = "What is 12 multiplied by 8? Answer with the number only."
THREAD_CANDIDATES = [2, 4, 6, 8]
TEST_MODEL = "llama3.2:3b"

def query_ollama_thread(threads):
    payload = {
        "model": TEST_MODEL,
        "prompt": PROMPT,
        "stream": True,
        "keep_alive": "30m",
        "options": {
            "num_predict": 20,
            "temperature": 0.1,
            "num_ctx": 2048,
            "num_thread": threads
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_API}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    start_time = time.perf_counter()
    first_token_time = None
    chunks = []
    eval_count = 0
    eval_duration_ns = 0

    with urllib.request.urlopen(req, timeout=60) as resp:
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            item = json.loads(line_str)
            if not first_token_time and item.get("response"):
                first_token_time = time.perf_counter()
            if item.get("response"):
                chunks.append(item["response"])
            if item.get("done"):
                eval_count = item.get("eval_count", len(chunks))
                eval_duration_ns = item.get("eval_duration", 0)

    end_time = time.perf_counter()
    total_latency = end_time - start_time
    ttft = (first_token_time - start_time) if first_token_time else total_latency
    tps = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns > 0 else 0
    return total_latency, ttft, tps

print("=" * 65)
print(f"BENCHMARKING CPU THREAD TUNING ON {TEST_MODEL}")
print("=" * 65)

results = {}

for t in THREAD_CANDIDATES:
    print(f"\nTesting num_thread = {t}...")
    latencies = []
    ttfts = []
    tpss = []
    # 1 warmup
    query_ollama_thread(t)
    for trial in range(4):
        time.sleep(0.3)
        lat, ttft, tps = query_ollama_thread(t)
        latencies.append(lat)
        ttfts.append(ttft)
        tpss.append(tps)
        print(f"  Trial {trial+1}: latency={lat:.3f}s | TTFT={ttft:.3f}s | speed={tps:.1f} t/s")

    med_lat = statistics.median(latencies)
    med_ttft = statistics.median(ttfts)
    med_tps = statistics.median(tpss)
    results[t] = {
        "median_latency": med_lat,
        "median_ttft": med_ttft,
        "median_tps": med_tps
    }

print("\n" + "=" * 65)
print("THREAD TUNING RESULTS SUMMARY")
print("=" * 65)
print(f"{'num_thread':<12} | {'Median Latency (s)':<20} | {'TTFT (s)':<12} | {'Tokens/s':<10}")
print("-" * 65)
for t, r in results.items():
    print(f"{t:<12} | {r['median_latency']:<20.3f} | {r['median_ttft']:<12.3f} | {r['median_tps']:<10.1f}")

with open("scratch/benchmark_threads_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
