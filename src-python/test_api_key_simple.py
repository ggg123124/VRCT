"""Simple test to verify Aliyun API key configuration"""
import subprocess
import json
import time
import sys

# Start backend
print("Starting backend process...")
process = subprocess.Popen(
    [sys.executable, 'mainloop.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

# Wait for initialization
print("Waiting for initialization...")
start_time = time.time()
while True:
    line = process.stdout.readline()
    if not line:
        if process.poll() is not None:
            print("Backend terminated")
            sys.exit(1)
        continue
    
    try:
        response = json.loads(line.strip())
        endpoint = response.get("endpoint", "")
        if endpoint == "/run/initialization_complete":
            print(f"Initialized in {time.time() - start_time:.1f}s")
            break
    except json.JSONDecodeError:
        pass

# Set API key
print("\nSetting Aliyun API key...")
request = {
    "endpoint": "/set/data/aliyun_auth_key",
    "data": "dGVzdF9rZXlfMTIzNDU2Nzg5MDEyMzQ1Njc4OTA="  # base64 encoded test key
}
process.stdin.write(json.dumps(request) + '\n')
process.stdin.flush()

# Wait for response
while True:
    line = process.stdout.readline()
    if not line:
        break
    try:
        response = json.loads(line.strip())
        if response.get("endpoint") == "/set/data/aliyun_auth_key":
            print(f"API key set: Status={response.get('status')}")
            break
    except json.JSONDecodeError:
        pass

# Get translation engines
print("\nGetting translation engines...")
request = {"endpoint": "/get/data/selectable_translation_engines"}
process.stdin.write(json.dumps(request) + '\n')
process.stdin.flush()

while True:
    line = process.stdout.readline()
    if not line:
        break
    try:
        response = json.loads(line.strip())
        if response.get("endpoint") == "/get/data/selectable_translation_engines":
            engines = response.get("result", [])
            print(f"Available engines: {engines}")
            if "Aliyun_LiveTranslate" in engines:
                print("✓ Aliyun_LiveTranslate is in the list!")
            else:
                print("✗ Aliyun_LiveTranslate is NOT in the list")
            break
    except json.JSONDecodeError:
        pass

# Cleanup
process.terminate()
process.wait(timeout=5)
print("\nTest complete")
