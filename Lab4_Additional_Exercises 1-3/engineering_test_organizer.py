"""Engineering Test Data Organizer

Usage:
    python engineering_test_data.py
    python engineering_test_data.py SANTOS 42 "Taylor Swift"
"""
import statistics
import sys
from collections import defaultdict

# category: (unit, low, high) - measurement values are scaled into this range
CATEGORIES = {
    "TEMPERATURE": ("C", 20.0, 100.0),
    "VOLTAGE": ("V", 1.0, 24.0),
    "CURRENT": ("A", 0.1, 5.0),
    "PRESSURE": ("kPa", 80.0, 200.0),
    "SPEED": ("RPM", 100.0, 3000.0),
}
CAT_LIST = list(CATEGORIES)
NUM_SOURCES = 5
CATS_PER_SOURCE = 3  # each source tests 3 categories -> every category gets multiple readings


# 1. GENERATE ----------------------------------------------------------------
def get_inputs():
    if len(sys.argv) == 4:
        last, seed, artist = sys.argv[1:4]
    else:
        last = input("LAST_NAME: ")
        seed = input("SEED_NUM: ")
        artist = input("FAVORITE_ARTIST: ")
    return last.strip().upper(), int(seed), artist.strip().upper()


def make_sources(last):
    """Five test sources: LAST_NAME with the labels T1-T5."""
    return [f"{last}_T{i}" for i in range(1, NUM_SOURCES + 1)]


def generate_records(last, seed, artist):
    chars = [c for c in artist if c.isalpha()]
    if not chars:
        raise ValueError("FAVORITE_ARTIST must contain letters.")

    def value(n, cat):
        """Value from SEED_NUM and the artist's character at position n, scaled to the category range."""
        unit, lo, hi = CATEGORIES[cat]
        frac = (seed * (n + 1) + ord(chars[n % len(chars)]) * (n + 3)) % 1000 / 1000
        return round(lo + frac * (hi - lo), 2)

    sources = make_sources(last)
    pairs = [(sources[i], CAT_LIST[(i + k) % len(CAT_LIST)])
             for i in range(NUM_SOURCES) for k in range(CATS_PER_SOURCE)]
    pairs.append(pairs[0])  # repeated test-source/category record

    return sources, [{"id": f"R{n + 1:03d}", "source": s, "category": c,
                      "value": value(n, c), "unit": CATEGORIES[c][0]}
                     for n, (s, c) in enumerate(pairs)]


# 2-5. ORGANIZE, IDENTIFY, SUMMARIZE, PROCESS ------------------------------------
def organize(records):
    by_cat, by_src, by_pair = defaultdict(list), defaultdict(list), defaultdict(list)
    for r in records:
        by_cat[r["category"]].append(r)
        by_src[r["source"]].append(r)
        by_pair[(r["source"], r["category"])].append(r)
    return by_cat, by_src, by_pair


def cat_stats(by_cat):
    out = {}
    for cat, rs in by_cat.items():
        v = [r["value"] for r in rs]
        out[cat] = {"n": len(v), "min": min(v), "max": max(v), "mean": statistics.mean(v),
                    "range": max(v) - min(v),
                    "stdev": statistics.pstdev(v) if len(v) > 1 else 0.0}
    return out


def process(records, stats):
    """Deviation of each reading from its category mean, with a simple status."""
    for r in records:
        s = stats[r["category"]]
        r["dev"] = r["value"] - s["mean"]
        tol = 0.10 * (CATEGORIES[r["category"]][2] - CATEGORIES[r["category"]][1])
        r["status"] = "NEAR MEAN" if abs(r["dev"]) <= tol else ("ABOVE MEAN" if r["dev"] > 0 else "BELOW MEAN")


# 6-7. REPORT ---------------------------------------------------------------------
def build_report(last, seed, artist, sources, records):
    by_cat, by_src, by_pair = organize(records)
    stats = cat_stats(by_cat)
    process(records, stats)
    repeated = {k: v for k, v in by_pair.items() if len(v) > 1}
    bar, dash, L = "=" * 78, "-" * 78, []

    L += [bar, "FINAL ORGANIZED AND SUMMARIZED TEST DATASET", bar,
          f"LAST_NAME: {last} | SEED_NUM: {seed} | FAVORITE_ARTIST: {artist}", ""]

    L += ["1. GENERATED TEST DATA", dash,
          f"{'ID':<6}{'Test Source':<22}{'Category':<13}{'Value':>11}  Unit"]
    for r in records:
        L.append(f"{r['id']:<6}{r['source']:<22}{r['category']:<13}{r['value']:>11.2f}  {r['unit']}")

    L += ["", "2. ORGANIZED TEST DATA (by source, then category)", dash]
    for s in sources:
        L.append(s)
        for cat in CAT_LIST:
            vals = [f"{r['value']:.2f}" for r in by_pair.get((s, cat), [])]
            if vals:
                L.append(f"    {cat:<13}{', '.join(vals)} {CATEGORIES[cat][0]}")

    L += ["", "3. REPEATED / DISTINCT DATA", dash,
          f"Total records           : {len(records)}",
          f"Distinct test sources   : {len(by_src)}",
          f"Distinct categories     : {len(by_cat)}",
          f"Distinct source/category: {len(by_pair)}"]
    for (s, c), rs in repeated.items():
        L.append(f"Repeated record         : {s} / {c} appears {len(rs)}x "
                 f"({', '.join(r['id'] for r in rs)}; values "
                 f"{', '.join(f'{r['value']:.2f}' for r in rs)})")
    multi = [c for c, rs in by_cat.items() if len(rs) > 1]
    L.append(f"Categories with multiple measurements: {', '.join(c for c in CAT_LIST if c in multi)}")

    L += ["", "4. NUMERICAL AND CATEGORICAL SUMMARIES", dash, "Numerical (per category):",
          f"{'Category':<13}{'N':<4}{'Min':>10}{'Max':>10}{'Mean':>10}{'Range':>10}{'StDev':>10}  Unit"]
    for cat in CAT_LIST:
        s = stats[cat]
        L.append(f"{cat:<13}{s['n']:<4}{s['min']:>10.2f}{s['max']:>10.2f}{s['mean']:>10.2f}"
                 f"{s['range']:>10.2f}{s['stdev']:>10.2f}  {CATEGORIES[cat][0]}")
    L += ["", "Categorical (record counts):"]
    for cat in CAT_LIST:
        L.append(f"  {cat:<13}{len(by_cat[cat]):<4}({len(by_cat[cat]) / len(records):.0%})")
    for s in sources:
        cats = sorted({r['category'] for r in by_src[s]}, key=CAT_LIST.index)
        L.append(f"  {s:<22}{len(by_src[s])} records: {', '.join(cats)}")

    L += ["", "5. PROCESSED RESULTS (deviation from category mean)", dash,
          f"{'ID':<6}{'Test Source':<22}{'Category':<13}{'Value':>10}{'Dev':>10}  Status"]
    for r in records:
        L.append(f"{r['id']:<6}{r['source']:<22}{r['category']:<13}{r['value']:>10.2f}"
                 f"{r['dev']:>+10.2f}  {r['status']}")

    L += ["", "6. ORDERED RESULTS", dash, "Categories by number of measurements (then mean, highest first):"]
    for i, cat in enumerate(sorted(CAT_LIST, key=lambda c: (-stats[c]['n'], -stats[c]['mean'])), 1):
        L.append(f"  {i}. {cat:<13}n={stats[cat]['n']}  mean={stats[cat]['mean']:.2f} {CATEGORIES[cat][0]}")
    L.append("Measurements within each category (highest value first):")
    for cat in CAT_LIST:
        L.append(f"  {cat}:")
        for r in sorted(by_cat[cat], key=lambda r: (-r['value'], r['id'])):
            L.append(f"      {r['value']:>9.2f} {r['unit']:<4}{r['source']} ({r['id']})")

    L += ["", "7. FINAL SUMMARY", dash,
          f"Test sources           : {len(by_src)}",
          f"Categories             : {len(by_cat)}",
          f"Total records          : {len(records)}",
          f"Repeated records       : {sum(len(v) - 1 for v in repeated.values())}",
          f"Most-measured category : {max(CAT_LIST, key=lambda c: stats[c]['n'])}",
          f"Most variable category : {max(CAT_LIST, key=lambda c: stats[c]['stdev'] / (CATEGORIES[c][2] - CATEGORIES[c][1]))}"
          " (largest spread relative to its range)", bar]
    return "\n".join(L)


def main():
    last, seed, artist = get_inputs()
    sources, records = generate_records(last, seed, artist)
    report = build_report(last, seed, artist, sources, records)
    print(report)
    with open("engineering_test_report.txt", "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()