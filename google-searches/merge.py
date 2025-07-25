"""
Write a Python program to pick up all the entries whose .title begins with "Searched for " in
google.json which looks like this:

```json
[{
  "header": "Search",
  "title": "Visited How to Export Google Search History - Stack Overflow",
  ...
},{
  "header": "Search",
  "title": "Searched for google search history export",
  ...
},{
...
```

... and merges it with `topics.txt` which is a tab delimited file with column
headers text, best_match, ... (the rest don't matter). If the title is
"Searched for abc" then look up the row in topics.txt where text is "abc",
get the best_match, add it as "topic". Then, for each month, for each topic,
count the number of entries and print that as a CSV file with columns
month (yyyy-mm), topic, count.
"""

import json
import csv
import sys
from collections import defaultdict

# Load topic mappings from topics.txt
topics_map = {}
with open("topics.txt", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        topics_map[row["text"]] = row["best_match"]

# Count occurrences per month and topic
counts = defaultdict(lambda: defaultdict(int))

with open("google.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for entry in data:
    title = entry.get("title", "")
    prefix = "Searched for "
    if not title.startswith(prefix):
        continue
    query = title[len(prefix) :].strip()
    topic = topics_map.get(query)
    if not topic:
        continue  # skip if no matching topic
    month = entry.get("time", "")[:7]  # yyyy-mm
    counts[month][topic] += 1

# Output CSV to stdout
writer = csv.writer(sys.stdout)
writer.writerow(["month", "topic", "count"])
for month in sorted(counts):
    for topic in sorted(counts[month]):
        writer.writerow([month, topic, counts[month][topic]])
