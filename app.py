from flask import Flask, jsonify, render_template_string
from pathlib import Path
import subprocess
import sys
import threading

app = Flask(__name__)

state = {
    "running": False,
    "finished": False,
    "error": "",
    "parts": [False, False, False, False],
    "message": "Indirmeye hazir"
}
lock = threading.Lock()


HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Proje 7 - Indirme Yoneticisi</title>
<style>
body {
    background: #0f172a;
    color: #f8fafc;
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 40px 20px;
}
.container {
    max-width: 760px;
    margin: auto;
}
h1 { color: #38bdf8; }
.card {
    background: #1e293b;
    border-radius: 14px;
    padding: 24px;
    margin-top: 22px;
}
.part { margin: 20px 0; }
.label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}
.track {
    height: 16px;
    background: #334155;
    border-radius: 10px;
    overflow: hidden;
}
.fill {
    width: 0%;
    height: 100%;
    background: #22c55e;
    transition: width .35s;
}
button {
    background: #0284c7;
    color: white;
    border: none;
    border-radius: 9px;
    padding: 13px 25px;
    font-size: 16px;
    cursor: pointer;
}
button:disabled {
    opacity: .5;
    cursor: not-allowed;
}
#status { color: #cbd5e1; }
</style>
</head>
<body>
<div class="container">
    <h1>Proje 7</h1>
    <p>Eszamanli Parcali Dosya Indirme Yoneticisi</p>

    <div class="card">
        <h2>HTTP Range - 4 Worker</h2>
        <p>Test dosyasi: 1 MiB</p>
        <button id="start" onclick="startDownload()">
            Indirmeyi Baslat
        </button>
        <p id="status">Indirmeye hazir</p>
    </div>

    <div class="card">
        <h2>Parca Durumlari</h2>
        <div id="parts"></div>
    </div>
</div>

<script>
const root = document.getElementById("parts");

for (let i = 0; i < 4; i++) {
    root.innerHTML += `
      <div class="part">
        <div class="label">
          <span>Parca ${i + 1}</span>
          <span id="value${i}">Bekliyor</span>
        </div>
        <div class="track">
          <div class="fill" id="bar${i}"></div>
        </div>
      </div>`;
}

async function refresh() {
    try {
        const response = await fetch("/status");
        const data = await response.json();

        document.getElementById("status").textContent =
            data.message;

        document.getElementById("start").disabled =
            data.running;

        data.parts.forEach((finished, i) => {
            document.getElementById("bar" + i).style.width =
                finished ? "100%" : "0%";
            document.getElementById("value" + i).textContent =
                finished ? "Tamamlandi" : "Bekliyor";
        });
    } catch (error) {
        document.getElementById("status").textContent =
            "Sunucuya baglanilamadi.";
    }
}

async function startDownload() {
    const response = await fetch("/start", {
        method: "POST"
    });
    const data = await response.json();
    document.getElementById("status").textContent =
        data.message;
    refresh();
}

setInterval(refresh, 500);
refresh();
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(HTML)


@app.get("/status")
def status():
    with lock:
        return jsonify(dict(state))


def run_download():
    try:
        main_file = Path(__file__).with_name("main.py")

        process = subprocess.Popen(
            [sys.executable, "-u", str(main_file)],
            cwd=str(main_file.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        for line in process.stdout:
            print(line, end="")
            if "tamamlandi." in line.lower():
                import re
                match = re.search(
                    r"Parca (\d+) tamamlandi",
                    line,
                    re.IGNORECASE
                )
                if match:
                    index = int(match.group(1)) - 1
                    if 0 <= index < 4:
                        with lock:
                            state["parts"][index] = True

        code = process.wait()

        with lock:
            if code == 0:
                state["finished"] = True
                state["message"] = "Indirme basariyla tamamlandi!"
            else:
                state["error"] = "Python indirme hatasi"
                state["message"] = "Indirme basarisiz oldu."
    except Exception as exc:
        with lock:
            state["error"] = str(exc)
            state["message"] = "Hata: " + str(exc)
    finally:
        with lock:
            state["running"] = False


@app.post("/start")
def start():
    with lock:
        if state["running"]:
            return jsonify({"message": "Indirme zaten suruyor."})

        state["running"] = True
        state["finished"] = False
        state["error"] = ""
        state["parts"] = [False] * 4
        state["message"] = "Indirme baslatildi..."

    threading.Thread(
        target=run_download,
        daemon=True
    ).start()

    return jsonify({"message": "Indirme baslatildi."})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)