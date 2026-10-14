import sys
import urllib.request
import json

def check_jarvis_health(url="http://127.0.0.1:5000/manifest.json"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JarvisHealthChecker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get("name") == "Jarvis":
                    print("[HEALTH] JARVIS Server is healthy and responding.")
                    return True
    except Exception as e:
        print(f"[HEALTH] JARVIS Server check failed: {e}")
        return False
    return False

def check_ollama_health(url="http://127.0.0.1:11434/api/tags"):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JarvisHealthChecker/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                models = [m.get("name") for m in data.get("models", [])]
                print(f"[HEALTH] Ollama is healthy with {len(models)} models available: {models}")
                return True
    except Exception as e:
        print(f"[HEALTH] Ollama check failed: {e}")
        return False
    return False

if __name__ == "__main__":
    j_ok = check_jarvis_health()
    o_ok = check_ollama_health()
    if j_ok and o_ok:
        print("[HEALTH] All core services HEALTHY (PASS)")
        sys.exit(0)
    else:
        print("[HEALTH] Service check FAILED")
        sys.exit(1)
