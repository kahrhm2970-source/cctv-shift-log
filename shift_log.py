"""Offline educational shift handover generator. No camera connections."""
import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path

FIELDS = ['camera_id', 'live', 'playback', 'image', 'ticket', 'action']
CHECKS = ['live', 'playback', 'image']

def load(path):
    if Path(path).stat().st_size > 1_000_000:
        raise ValueError('Input exceeds 1 MB')
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError('Expected columns: ' + ','.join(FIELDS))
        rows = list(reader)
    if not 1 <= len(rows) <= 1000:
        raise ValueError('Expected 1–1000 cameras')
    seen = set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('Invalid CSV row width')
        if not re.fullmatch(r'CAM-[0-9]{3,6}', row['camera_id']):
            raise ValueError('Use synthetic CAM-001 style IDs')
        if row['camera_id'] in seen:
            raise ValueError('Duplicate camera ID')
        seen.add(row['camera_id'])
        if any(row[k] not in {'pass', 'fail', 'unchecked'} for k in CHECKS):
            raise ValueError('Checks must be pass, fail or unchecked')
        if row['ticket'] and not re.fullmatch(r'LAB-[0-9]{3,6}', row['ticket']):
            raise ValueError('Use fictional LAB-001 style ticket IDs')
        if len(row['action']) > 300 or any(ord(c) < 32 for c in row['action']):
            raise ValueError('Action must be a single line up to 300 characters')
    return rows

def status(row):
    if any(row[k] == 'fail' for k in CHECKS):
        return 'follow_up'
    if any(row[k] == 'unchecked' for k in CHECKS):
        return 'incomplete'
    return 'checked'

def summarize(rows):
    counts = Counter(status(r) for r in rows)
    return {'total': len(rows), **{k: counts[k] for k in ['checked', 'follow_up', 'incomplete']},
            'failed_without_ticket': sum(status(r) == 'follow_up' and not r['ticket'] for r in rows)}

def render(rows):
    labels = {'checked': 'اكتمل الفحص', 'follow_up': 'يتطلب متابعة', 'incomplete': 'الفحص غير مكتمل'}
    body = ''.join('<tr>' + ''.join('<td>' + html.escape(str(v)) + '</td>' for v in
        [r['camera_id'], labels[status(r)], r['live'], r['playback'], r['image'], r['ticket'], r['action']]) + '</tr>' for r in rows)
    return '''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CCTV Shift Log</title><style>body{font:18px system-ui;background:#edf3f8;color:#16324f;margin:5%}table{border-collapse:collapse;background:white;width:100%}td,th{border:1px solid #cbd5e1;padding:12px}header{background:#16324f;color:white;padding:24px;border-radius:12px}section{overflow:auto}pre{direction:ltr;text-align:left} @media print{body{margin:0}}</style><header><h1>CCTV Shift Log | تسليم الوردية</h1><p>نموذج تدريبي • بيانات افتراضية • نتائج فحص يدوي</p></header><h2>ملخص الفحص</h2><pre>''' + html.escape(json.dumps(summarize(rows), indent=2)) + '''</pre><p>checked: اكتملت الفحوص المدخلة فقط؛ لا تعني ضمان التغطية أو استمرارية التسجيل. incomplete: توجد فحوص لم تنفذ. follow_up: يوجد فحص فاشل.</p><section><table><thead><tr><th>الكاميرا</th><th>الحالة</th><th>مباشر</th><th>استرجاع</th><th>الصورة</th><th>بلاغ</th><th>الإجراء التالي</th></tr></thead><tbody>''' + body + '</tbody></table></section></html>'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file')
    parser.add_argument('--out', default='reports')
    args = parser.parse_args()
    try:
        rows = load(args.csv_file)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / 'handover.html').write_text(render(rows), encoding='utf-8')
        (out / 'summary.json').write_text(json.dumps(summarize(rows), indent=2), encoding='utf-8')
        print(json.dumps(summarize(rows)))
        return 0
    except (ValueError, OSError, csv.Error, UnicodeError) as exc:
        parser.exit(2, str(exc) + '\n')

if __name__ == '__main__':
    main()
