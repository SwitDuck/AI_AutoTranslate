import os
import requests
import gzip
from PIL import Image
import cairosvg
import io
import subprocess
import time

BOOK_ID = "B2622C1A-1C05-450C-9713-D1861D3037C7"
OUT_DIR = "urait_pages"
USE_INKSCAPE = False  # Включи, если установлен inkscape
RETRY_DELAY = 20      # Секунд между попытками
MAX_RETRIES = 1       # Количество повторов после неудачи

os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 YaBrowser/25.4.0.0 Safari/537.36",
    "Referer": f"https://urait.ru/viewer/{BOOK_ID}",
    "Accept-Encoding": "gzip",
    "Cookie": "cookie-policy-agreed=eyJpdiI6ImtCbmZwNlJqZ21sZEZaRVF5OTVmZ3c9PSIsInZhbHVlIjoiYno5Skg1QzN1YmlySVJJZE43OWhialFlZm1OVVkzMmYvQjJHU3VTWk4xMHppZmpxRmlFMUxpakRJbXM5U2pWZCIsIm1hYyI6IjJjNmRhYTc0N2I1YjVlZmY4ZTY3YzgxM2IyOTYwZWI1OGJhMmVlYWY4ZDI4MTIxM2E0MTdhYjg5ZGMzYjliZTYiLCJ0YWciOiIifQ%3D%3D; _ga=GA1.2.758888684.1738896039; auth-confirmed-with-subscription=eyJpdiI6Imx0QWtCUXlrWFFIRlh1TUg1YjhiU2c9PSIsInZhbHVlIjoiay9mTGZVRWsydVJFc1R5ZEJkZWR4bXB3KzF1VmRBdmxNVzdveUJ4cmRqaC9FZVRRQmhrbW5aQTBZeDdVeStHdSIsIm1hYyI6IjZhODBjYWI2NjBlYzczYzcwNGQ1NWNkMWE1NzI0OTI3ZmE2NGViZDFiYTJiMjlkNDQ4YWE0ZDUyMmU5NDA5YjYiLCJ0YWciOiIifQ%3D%3D; _gid=GA1.2.2126219989.1747040296; ebs_session=eyJpdiI6Ii9FMmVrd3dreXlWZjRqTHZIMlcvSWc9PSIsInZhbHVlIjoiVkdDMnlsSjc0RzRWcFBXODE5TFVEVU5oQm5PU3ZNdHJCbmN0WnAwUENlSVBoNk8rTnE3MHRDNGpFcUVMVVhIb29ka0dIellJbHRkREswMFdxYWdlZTJlVVBFS3Q5VmdqNkJYbWFhOWJWTVBSSUxMcWNrWEVBWlorVmRMbmxSNTAiLCJtYWMiOiJjYTEzMDM0MGNhYWQ2MWFlMWM1ZGMzN2ZhN2E0ZTdkNjE2MGIwNTFhNTNhNjU4MDVjZDFjZjM5OGIzYjZjZmY3IiwidGFnIjoiIn0%3D"
}


def try_download_svg(page):
    url = f"https://urait.ru/viewer/page/{BOOK_ID}/{page}"
    for attempt in range(MAX_RETRIES + 1):
        try:
            print(f"[+] Скачивается: страница {page} (попытка {attempt + 1})")
            r = requests.get(url, headers=HEADERS, timeout=10)

            if r.status_code != 200:
                print(f"[!] Страница {page} недоступна (код {r.status_code})")
                raise Exception("Недоступна")

            content_type = r.headers.get("Content-Type", "")
            if "svg" not in content_type:
                raise Exception(f"Неверный Content-Type: {content_type}")

            if r.content.startswith(b"<?xml"):
                return r.content
            else:
                return gzip.decompress(r.content)

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"[!] Ошибка загрузки страницы {page}: {e}. Повтор через {RETRY_DELAY} секунд...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"[×] Пропуск страницы {page} после неудачных попыток.")
                return None

def convert_svg_to_png(svg_path, png_path):
    if USE_INKSCAPE:
        subprocess.run(["inkscape", svg_path, "--export-type=png", f"--export-filename={png_path}"])
    else:
        cairosvg.svg2png(url=svg_path, write_to=png_path, background_color='white')

# === Шаг 1: Скачивание SVG ===
page = 1
skipped_pages = 0
MAX_SKIPPED = 4  # Если подряд слишком много пропусков — стоп

while skipped_pages < MAX_SKIPPED:
    svg_data = try_download_svg(page)
    if svg_data:
        svg_path = os.path.join(OUT_DIR, f"page_{page:03}.svg")
        with open(svg_path, 'wb') as f:
            f.write(svg_data)
        skipped_pages = 0
    else:
        skipped_pages += 1
    page += 1

if page == 1:
    print("[!] Ни одной страницы не удалось скачать.")
    exit()


def convert_svg_to_png(svg_path, png_path, dpi=200):
    cairosvg.svg2png(url=svg_path, write_to=png_path, background_color='white', dpi=dpi)
# === Шаг 2: SVG → PNG ===
for file in sorted(os.listdir(OUT_DIR)):
    if file.endswith(".svg"):
        svg_path = os.path.join(OUT_DIR, file)
        png_path = svg_path.replace(".svg", ".png")
        print(f"[~] Конвертация: {file} → PNG")
        try:
            convert_svg_to_png(svg_path, png_path)
        except Exception as e:
            print(f"[!] Ошибка конвертации {file}: {e}")

# === Шаг 3: PNG → PDF ===
images = []
for file in sorted(os.listdir(OUT_DIR)):
    if file.endswith(".png"):
        path = os.path.join(OUT_DIR, file)
        try:
            images.append(Image.open(path).convert("RGB"))
        except Exception as e:
            print(f"[!] Ошибка открытия {file}: {e}")

if images:
    images[0].save("управленческая деятельность.pdf", save_all=True, append_images=images[1:])
    print("[✓] PDF сохранён как управленческая деятельность.pdf")
else:
    print("[!] PNG-файлы не найдены — PDF не создан.")
