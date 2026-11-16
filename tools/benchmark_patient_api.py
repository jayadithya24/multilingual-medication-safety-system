"""Measure local API requests using synthetic fixtures; does not save patient data."""
import io
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image, ImageDraw, ImageFont

BASE = 'http://127.0.0.1:8000'


def measure(method, path, **kwargs):
    start = time.perf_counter()
    response = requests.request(method, BASE + path, timeout=60, **kwargs)
    elapsed = round(time.perf_counter() - start, 3)
    return {'status': response.status_code, 'seconds': elapsed}


def main():
    report = {}
    for lang in ('en', 'kn', 'tulu'):
        report[f'search_{lang}'] = [measure('GET', f'/neo4j/search?term=Metformin&lang={lang}') for _ in range(3)]
    image = Image.new('RGB', (900, 240), 'white')
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 50)
    except OSError:
        font = ImageFont.load_default(size=50)
    ImageDraw.Draw(image).text((30, 65), 'Metformin 500 mg', fill='black', font=font)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    data = buffer.getvalue()
    report['ocr'] = []
    for _ in range(3):
        with ThreadPoolExecutor(max_workers=1) as pool:
            work = pool.submit(measure, 'POST', '/prescription-ocr?lang=en', files={'file': ('synthetic.png', data, 'image/png')})
            time.sleep(0.15)
            report.setdefault('health_during_ocr', []).append(measure('GET', '/health'))
            report['ocr'].append(work.result())
    audio = (Path(__file__).resolve().parents[1] / 'tests/fixtures/voice/metformin-en.wav').read_bytes()
    report['voice_en_fixture'] = [measure('POST', '/voice-search?lang=en', files={'file': ('fixture.wav', audio, 'audio/wav')}) for _ in range(2)]
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
