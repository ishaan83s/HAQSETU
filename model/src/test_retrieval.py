import json

file_path = "ps25/model/data/legalstuff/kyr_relevant.jsonl"

records = []
with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

lengths = [len(r["legal_text"].split()) for r in records]

print("Total records:", len(records))
print("Min words:", min(lengths))
print("Max words:", max(lengths))
print("Mean words:", sum(lengths) / len(lengths))

# Sort and show the 5 longest, so we can inspect them directly
longest = sorted(records, key=lambda r: len(r["legal_text"].split()), reverse=True)[:5]
print("\nTop 5 longest legal_text records:")
for r in longest:
    print(f"- {r['document_id']} ({len(r['legal_text'].split())} words): {r['title']}")

# Simple bucket histogram
buckets = {"0-30": 0, "31-60": 0, "61-100": 0, "101-200": 0, "200+": 0}
for l in lengths:
    if l <= 30: buckets["0-30"] += 1
    elif l <= 60: buckets["31-60"] += 1
    elif l <= 100: buckets["61-100"] += 1
    elif l <= 200: buckets["101-200"] += 1
    else: buckets["200+"] += 1

print("\nLength buckets:")
for k, v in buckets.items():
    print(f"  {k} words: {v} records")