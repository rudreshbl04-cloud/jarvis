import time
import json
import urllib.request
import statistics

OLLAMA_API = "http://127.0.0.1:11434"
PROMPT = "What is 12 multiplied by 8? Answer with the number only."
CANDIDATES = ["qwen2.5:3b", "llama3.2:3b", "phi3:mini"]

def query_ollama(model, prompt, options=None, keep_alive="30m"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "keep_alive": keep_alive,
        "options": options or {}
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
    prompt_eval_count = 0
    prompt_eval_duration_ns = 0

    with urllib.request.urlopen(req, timeout=120) as resp:
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
                prompt_eval_count = item.get("prompt_eval_count", 0)
                prompt_eval_duration_ns = item.get("prompt_eval_duration", 0)

    end_time = time.perf_counter()
    total_latency = end_time - start_time
    ttft = (first_token_time - start_time) if first_token_time else total_latency
    full_response = "".join(chunks).strip()
    
    # Calculate tokens/sec from Ollama reported eval_duration if available, else wall clock
    if eval_duration_ns > 0:
        tok_per_sec = eval_count / (eval_duration_ns / 1e9)
    else:
        tok_per_sec = eval_count / max(0.001, (total_latency - ttft))

    return {
        "response": full_response,
        "total_latency": total_latency,
        "ttft": ttft,
        "eval_count": eval_count,
        "tok_per_sec": tok_per_sec,
        "correct": ("96" in full_response)
    }

print("=" * 70)
print("BENCHMARKING LOCAL SMALL MODELS ON INTEL i7 CPU (CPU-ONLY INFERENCE)")
print(f"Prompt: '{PROMPT}'")
print("=" * 70)

results = {}

for model in CANDIDATES:
    print(f"\n---> Benchmarking {model}...")
    default_opts = {
        "num_predict": 20,
        "temperature": 0.1,
        "num_ctx": 2048,
        "num_thread": 4
    }
    
    # 1. Cold start trial
    print("  Running trial 1 (cold start / initial load)...", flush=True)
    cold_res = query_ollama(model, PROMPT, default_opts)
    print(f"  Cold latency: {cold_res['total_latency']:.2f}s | Response: '{cold_res['response']}' | Correct: {cold_res['correct']}")
    
    # 2. Warm trials
    warm_latencies = []
    warm_ttfts = []
    warm_tps = []
    responses = []
    correct_count = 0

    for i in range(3):
        time.sleep(0.5)
        print(f"  Running warm trial {i+1}...", flush=True)
        w_res = query_ollama(model, PROMPT, default_opts)
        warm_latencies.append(w_res["total_latency"])
        warm_ttfts.append(w_res["ttft"])
        warm_tps.append(w_res["tok_per_sec"])
        responses.append(w_res["response"])
        if w_res["correct"]:
            correct_count += 1
        print(f"    Total: {w_res['total_latency']:.2f}s | TTFT: {w_res['ttft']:.2f}s | Speed: {w_res['tok_per_sec']:.1f} t/s | Output: '{w_res['response']}'")

    results[model] = {
        "cold_latency": cold_res["total_latency"],
        "warm_latencies": warm_latencies,
        "median_warm_latency": statistics.median(warm_latencies),
        "mean_warm_latency": statistics.mean(warm_latencies),
        "median_ttft": statistics.median(warm_ttfts),
        "median_tps": statistics.median(warm_tps),
        "correct_rate": f"{correct_count}/3",
        "sample_output": responses[-1]
    }

print("\n" + "=" * 70)
print("BENCHMARK COMPARISON TABLE (4 Threads, Context: 2048)")
print("=" * 70)
print(f"{'Model':<14} | {'Cold (s)':<9} | {'Median Warm (s)':<15} | {'TTFT (s)':<9} | {'Tokens/s':<9} | {'Correct':<8}")
print("-" * 70)
for m, r in results.items():
    print(f"{m:<14} | {r['cold_latency']:<9.2f} | {r['median_warm_latency']:<15.2f} | {r['median_ttft']:<9.2f} | {r['median_tps']:<9.1f} | {r['correct_rate']:<8}")

with open("scratch/benchmark_models_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("\nSaved benchmark results to scratch/benchmark_models_result.json")
