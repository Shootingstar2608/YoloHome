"""Chuyển `device_history.jsonl` thành dataset bảng cho bài toán occupancy.

Logic:
- Windowing theo bước 5 giây: gom các sự kiện vào cửa sổ thời gian liên tiếp.
- Features: last_light, last_temp, pir_count (số lần PIR phát hiện trong cửa sổ),
  face_flag (có sự kiện face trong cửa sổ hay không), hour_of_day (0-23).
- Label: occupied = 1 nếu pir_count>0 hoặc face_flag==1, else 0.

Output: `ml/occupancy_dataset.csv`
"""
import os
import json
import csv
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(__file__))
INPUT = os.path.join(ROOT, 'device_history.jsonl')
OUTPUT = os.path.join(ROOT, 'occupancy_dataset.csv')

WINDOW_SECONDS = 5


def parse_lines(path):
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                yield obj
            except Exception:
                continue


def build_windows(events):
    # Convert timestamps to datetime and sort
    parsed = []
    for e in events:
        try:
            t = datetime.fromisoformat(e['timestamp'])
            parsed.append((t, e))
        except Exception:
            continue
    if not parsed:
        return []
    parsed.sort(key=lambda x: x[0])

    start = parsed[0][0]
    end = parsed[-1][0]
    windows = []
    cur = start
    i = 0
    n = len(parsed)
    while cur <= end:
        win_end = cur + timedelta(seconds=WINDOW_SECONDS)
        bucket = []
        while i < n and parsed[i][0] < win_end:
            bucket.append(parsed[i][1])
            i += 1
        windows.append((cur, bucket))
        cur = win_end
    return windows


def extract_features_label(window_start, events):
    # default values
    last_light = None
    last_temp = None
    pir_count = 0
    face_flag = 0

    for e in events:
        topic = e.get('topic')
        val = e.get('value')
        if topic == 'V1':
            try:
                last_light = float(val)
            except Exception:
                pass
        elif topic == 'V2':
            try:
                last_temp = float(val)
            except Exception:
                pass
        elif topic == 'V3':
            try:
                if str(val) == '1':
                    pir_count += 1
            except Exception:
                pass
        elif topic == 'V7':
            # face recognition event seen
            face_flag = 1

    # fallback fill
    if last_light is None:
        last_light = 0.0
    if last_temp is None:
        last_temp = 0.0

    hour = window_start.hour

    label = 1 if (pir_count > 0 or face_flag == 1) else 0

    return {
        'ts': window_start.isoformat(),
        'hour': hour,
        'light': last_light,
        'temp': last_temp,
        'pir_count': pir_count,
        'face_flag': face_flag,
        'occupied': label
    }


def main():
    if not os.path.exists(INPUT):
        print('Không tìm thấy', INPUT)
        return
    events = list(parse_lines(INPUT))
    windows = build_windows(events)
    rows = []
    for start, bucket in windows:
        r = extract_features_label(start, bucket)
        rows.append(r)

    # write CSV
    fieldnames = ['ts', 'hour', 'light', 'temp', 'pir_count', 'face_flag', 'occupied']
    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print('Wrote', OUTPUT, 'rows=', len(rows))


if __name__ == '__main__':
    main()
