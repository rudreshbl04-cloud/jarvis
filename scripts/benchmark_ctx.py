import time
import json
import urllib.request
import statistics

OLLAMA_API = "http://127.0.0.1:11434"
PROMPT = "What is 12 multiplied by 8? Answer with the number only."
CTX_SIZES = [1024, 1536, 2048, 4096]
MODEL = "llama3.2:3b"

def query_ctx(ctx_size):
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": True,
        "keep_alive": "30m",
        "options": {
            "num_predict": 20,
            "temperature": 0.1,
            "num_ctx": ctx_size,
            "num_thread": 4
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
    prompt_eval_duration_ns = 0

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
                prompt_eval_duration_ns = item.get("prompt_eval_duration", 0)

    end_time = time.perf_counter()
    total_latency = end_time - start_time
    ttft = (first_token_time - start_time) if first_token_time else total_latency
    prompt_eval_ms = (prompt_eval_duration_ns / 1e6)
    return total_latency, ttft, prompt_eval_ms

print("=" * 65)
print(f"BENCHMARKING CONTEXT SIZE (num_ctx) ON {MODEL}")
print("=" * 65)

results = {}

for ctx in CTX_SIZES:
    print(f"\nTesting num_ctx = {ctx}...")
    latencies = []
    ttfts = []
    pe_times = []
    # 1 warmup
    query_ctx(ctx)
    for trial in range(3):
        time.sleep(0.3)
        lat, ttft, pe_ms = query_ctx(ctx)
        latencies.append(lat)
        ttfts.append(ttft)
        pe_times.append(pe_ms)
        print(f"  Trial {trial+1}: latency={lat:.3f}s | TTFT={ttft:.3f}s | PromptEval={pe_ms:.1f}ms")

    results[ctx] = {
        "median_latency": statistics.median(latencies),
        "median_ttft": statistics.median(ttfts),
        "median_prompt_eval_ms": statistics.median(pe_times)
    }

print("\n" + "=" * 65)
print("CONTEXT SIZE RESULTS SUMMARY")
print("=" * 65)
print(f"{'num_ctx':<10} | {'Median Latency (s)':<20} | {'TTFT (s)':<12} | {'PromptEval (ms)':<16}")
print("-" * 65)
for ctx, r in results.items():
    print(f"{ctx:<10} | {r['median_latency']:<20.3f} | {r['median_ttft']:<12.3f} | {r['median_prompt_eval_ms']:<16.1f}")

with open("scratch/benchmark_ctx_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
