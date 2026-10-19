"""Consolidated Transaction Report Generator

Usage:
    python transaction_report.py
    python transaction_report.py SANTOS 42 "Taylor Swift"
"""
import sys
from collections import defaultdict

CURRENCY = "PHP"
PRICES = {"NOTEBOOK": 45, "PEN": 12, "USB": 350, "HEADPHONES": 1200, "CALCULATOR": 500}
PRODUCTS = list(PRICES)
NUM_CUSTOMERS = 5
TXNS_PER_CUSTOMER = 3


# 1. GENERATE RECORDS ---------------------------------------------------------
def get_inputs():
    if len(sys.argv) == 4:
        last, seed, artist = sys.argv[1:4]
    else:
        last = input("LAST_NAME: ")
        seed = input("SEED_NUM: ")
        artist = input("FAVORITE_ARTIST: ")
    return last.strip().upper(), int(seed), artist.strip().upper()


def generate_records(last, seed, artist):
    chars = [c for c in artist if c.isalpha()]
    if not chars:
        raise ValueError("FAVORITE_ARTIST must contain letters.")

    def qty(n):  # quantity 1-9 from SEED_NUM + character position in FAVORITE_ARTIST
        return (seed + ord(chars[n % len(chars)])) % 9 + 1

    customers = [f"{last}_C{i}" for i in range(1, NUM_CUSTOMERS + 1)]
    pairs = [(customers[i], PRODUCTS[(i + k) % len(PRODUCTS)])
             for i in range(NUM_CUSTOMERS) for k in range(TXNS_PER_CUSTOMER)]
    pairs.append(pairs[0])  # repeated customer-product purchase

    records = []
    for n, (cust, prod) in enumerate(pairs):
        q = qty(n)
        records.append({"id": f"T{n + 1:03d}", "customer": cust, "product": prod,
                        "qty": q, "price": PRICES[prod], "value": q * PRICES[prod]})
    return customers, records


# 2-4. ORGANIZE, VALUE, IDENTIFY REPEATS --------------------------------------
def analyze(records):
    pair_count = defaultdict(list)
    for r in records:
        pair_count[(r["customer"], r["product"])].append(r)
    repeated = {k: v for k, v in pair_count.items() if len(v) > 1}
    return {
        "repeated": repeated,
        "distinct_customers": sorted({r["customer"] for r in records}),
        "distinct_products": sorted({r["product"] for r in records}),
        "distinct_pairs": len(pair_count),
        "grand_total": sum(r["value"] for r in records),
        "grand_qty": sum(r["qty"] for r in records),
    }


# 5-6. SUMMARIES ----------------------------------------------------------------
def summarize(records, key):
    g = defaultdict(lambda: {"txns": 0, "qty": 0, "value": 0})
    for r in records:
        s = g[r[key]]
        s["txns"] += 1
        s["qty"] += r["qty"]
        s["value"] += r["value"]
    return g


# 7-8. ORDER AND REPORT -------------------------------------------------------
def money(v):
    return f"{CURRENCY} {v:,.2f}"


def build_report(last, seed, artist, records, info, by_cust, by_prod):
    L, bar = [], "=" * 70
    L += [bar, "FINAL CONSOLIDATED TRANSACTION REPORT", bar,
          f"LAST_NAME: {last} | SEED_NUM: {seed} | FAVORITE_ARTIST: {artist}", ""]

    L += ["1. GENERATED TRANSACTION RECORDS", "-" * 70,
          f"{'ID':<6}{'Customer':<14}{'Product':<13}{'Qty':<5}{'Price':<10}"]
    for r in records:
        L.append(f"{r['id']:<6}{r['customer']:<14}{r['product']:<13}"
                 f"{r['qty']:<5}{r['price']:<10}")

    L += ["", "2. ORGANIZED TRANSACTION DATA (customer x product, qty)", "-" * 70,
          f"{'Customer':<14}" + "".join(f"{p[:6]:<8}" for p in PRODUCTS)]
    for c in info["distinct_customers"]:
        row = {p: sum(r["qty"] for r in records
                      if r["customer"] == c and r["product"] == p) for p in PRODUCTS}
        L.append(f"{c:<14}" + "".join(f"{row[p] or '-':<8}" for p in PRODUCTS))

    L += ["", "3. REPEATED / DISTINCT TRANSACTIONS", "-" * 70,
          f"Distinct customers     : {len(info['distinct_customers'])}",
          f"Distinct products      : {len(info['distinct_products'])}",
          f"Distinct cust-product  : {info['distinct_pairs']}"]
    for (c, p), rs in info["repeated"].items():
        L.append(f"Repeated purchase      : {c} bought {p} {len(rs)}x "
                 f"({', '.join(r['id'] for r in rs)})")

    L += ["", "4. TRANSACTION VALUES (qty x price)", "-" * 70,
          f"{'ID':<6}{'Customer':<14}{'Product':<13}{'Value':>14}"]
    for r in records:
        L.append(f"{r['id']:<6}{r['customer']:<14}{r['product']:<13}{money(r['value']):>14}")
    L.append(f"{'TOTAL':<33}{money(info['grand_total']):>14}")

    for title, grp in (("5. CUSTOMER SUMMARIES", by_cust), ("6. PRODUCT SUMMARIES", by_prod)):
        L += ["", title, "-" * 70, f"{'Name':<14}{'Txns':<6}{'Qty':<6}{'Total Value':>16}"]
        for name in sorted(grp):
            s = grp[name]
            L.append(f"{name:<14}{s['txns']:<6}{s['qty']:<6}{money(s['value']):>16}")

    L += ["", "7. ORDERED RESULTS (highest value first)", "-" * 70]
    for title, grp in (("Customers", by_cust), ("Products", by_prod)):
        L.append(f"{title}:")
        for i, (n, s) in enumerate(sorted(grp.items(), key=lambda x: (-x[1]["value"], x[0])), 1):
            L.append(f"  {i}. {n:<14}{money(s['value']):>16}")
    L.append("Top 5 transactions:")
    for i, r in enumerate(sorted(records, key=lambda r: (-r["value"], r["id"]))[:5], 1):
        L.append(f"  {i}. {r['id']} {r['customer']} - {r['product']:<11}{money(r['value']):>16}")

    top_c = max(by_cust.items(), key=lambda x: x[1]["value"])
    top_p = max(by_prod.items(), key=lambda x: x[1]["value"])
    L += ["", "8. OVERALL TRANSACTION SUMMARY", "-" * 70,
          f"Total transactions : {len(records)}",
          f"Total quantity     : {info['grand_qty']}",
          f"Total value        : {money(info['grand_total'])}",
          f"Average per txn    : {money(info['grand_total'] / len(records))}",
          f"Top customer       : {top_c[0]} ({money(top_c[1]['value'])})",
          f"Top product        : {top_p[0]} ({money(top_p[1]['value'])})", bar]
    return "\n".join(L)


def main():
    last, seed, artist = get_inputs()
    _, records = generate_records(last, seed, artist)
    info = analyze(records)
    report = build_report(last, seed, artist, records, info,
                          summarize(records, "customer"), summarize(records, "product"))
    print(report)
    with open("transaction_report.txt", "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()