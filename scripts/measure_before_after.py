import time
import json
import urllib.request
import statistics
import psutil

OLLAMA_API = "http://127.0.0.1:11434"
PROMPT = "What is 12 multiplied by 8? Answer with the number only."

def benchmark_config(model, ctx, threads, keep_alive="30m", trials=4):
    payload = {
        "model": model,
        "prompt": PROMPT,
        "stream": True,
        "keep_alive": keep_alive,
        "options": {
            "num_predict": 20,
            "temperature": 0.1,
            "num_ctx": ctx,
            "num_thread": threads
        }
    }
    data = json.dumps(payload).encode("utf-8")
    
    # 1 warmup
    req_warm = urllib.request.Request(f"{OLLAMA_API}/api/generate", data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req_warm, timeout=60).read()

    latencies = []
    ttfts = []
    tpss = []
    
    for _ in range(trials):
        time.sleep(0.2)
        req = urllib.request.Request(f"{OLLAMA_API}/api/generate", data=data, headers={"Content-Type": "application/json"})
        start_time = time.perf_counter()
        first_token_time = None
        eval_count = 0
        eval_duration_ns = 0

        with urllib.request.urlopen(req, timeout=60) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str: continue
                item = json.loads(line_str)
                if not first_token_time and item.get("response"):
                    first_token_time = time.perf_counter()
                if item.get("done"):
                    eval_count = item.get("eval_count", 0)
                    eval_duration_ns = item.get("eval_duration", 0)

        tot = time.perf_counter() - start_time
        ttft = (first_token_time - start_time) if first_token_time else tot
        tps = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns > 0 else 0
        latencies.append(tot)
        ttfts.append(ttft)
        tpss.append(tps)

    # Check RAM usage of ollama processes
    ollama_ram_mb = 0
    for p in psutil.process_iter(['name', 'memory_info']):
        if 'ollama' in (p.info['name'] or '').lower():
            ollama_ram_mb += p.info['memory_info'].rss / (1024 * 1024)

    return {
        "model": model,
        "ctx": ctx,
        "threads": threads,
        "median_latency": statistics.median(latencies),
        "min_latency": min(latencies),
        "max_latency": max(latencies),
        "median_ttft": statistics.median(ttfts),
        "median_tps": statistics.median(tpss),
        "ollama_ram_mb": round(ollama_ram_mb, 1)
    }

print("Running Before vs After Measurements...")

# Before: 7B model or 3B with 4096 ctx and default unoptimized parameters
before_res = benchmark_config(model="qwen2.5:7b", ctx=4096, threads=4, keep_alive="5m")
print("Before (7B baseline):", before_res)

# After: Optimized llama3.2:3b, ctx=2048, threads=4, keep_alive="30m"
after_res = benchmark_config(model="llama3.2:3b", ctx=2048, threads=4, keep_alive="30m")
print("After (Optimized 3B):", after_res)

# Also test qwen2.5:3b for multi-model reference
qwen_res = benchmark_config(model="qwen2.5:3b", ctx=2048, threads=4, keep_alive="30m")
print("After (Optimized Qwen 3B):", qwen_res)

comparison = {
    "before": before_res,
    "after_llama": after_res,
    "after_qwen": qwen_res
}

with open("scratch/before_after_comparison.json", "w", encoding="utf-8") as f:
    json.dump(comparison, f, indent=2)

print("Comparison written to scratch/before_after_comparison.json")
