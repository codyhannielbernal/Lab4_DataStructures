"""Student Performance Report Generator

Usage:
    python student_performance.py
    python student_performance.py SANTOS 42 "Taylor Swift"
"""
import sys
from collections import defaultdict

SUBJECTS = ["PROGRAMMING", "MATHEMATICS", "ELECTRONICS", "PHYSICS", "ENGLISH"]
NUM_STUDENTS = 5


# 1. GENERATE RECORDS ---------------------------------------------------------
def get_inputs():
    if len(sys.argv) == 4:
        last, seed, artist = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        last = input("LAST_NAME: ")
        seed = input("SEED_NUM: ")
        artist = input("FAVORITE_ARTIST: ")
    return last.strip().upper(), int(seed), artist.strip().upper()


def make_score(seed, artist_chars, student_idx, subject_idx):
    """Score (40-100) from SEED_NUM and a character position of FAVORITE_ARTIST."""
    pos = (student_idx * len(SUBJECTS) + subject_idx) % len(artist_chars)
    ch = artist_chars[pos]
    return (seed + ord(ch) * (student_idx + 1) + subject_idx * 7) % 61 + 40


def generate_records(last_name, seed, artist):
    artist_chars = [c for c in artist if c.isalpha()]
    if not artist_chars:
        raise ValueError("FAVORITE_ARTIST must contain letters.")
    students = [f"{last_name}_{i:02d}" for i in range(1, NUM_STUDENTS + 1)]

    records = []
    for i, student in enumerate(students):
        for j, subject in enumerate(SUBJECTS):
            records.append({"student": student, "subject": subject,
                            "score": make_score(seed, artist_chars, i, j)})

    records.append(dict(records[0]))   # one repeated student-subject record
    records[-6]["score"] = None        # one incomplete record (missing score)
    return students, records


# 2-4. ORGANIZE, IDENTIFY ISSUES, CATEGORIZE ---------------------------------
def categorize(score):
    if score >= 90: return "Outstanding"
    if score >= 80: return "Very Good"
    if score >= 75: return "Satisfactory"
    if score >= 60: return "Fair"
    return "Needs Improvement"


def analyze(records):
    seen, repeated, incomplete, valid = set(), [], [], []
    for r in records:
        key = (r["student"], r["subject"])
        if r["score"] is None:
            incomplete.append(r)
            continue
        if key in seen:
            repeated.append(r)
            continue
        seen.add(key)
        valid.append({**r, "category": categorize(r["score"])})

    by_student, by_subject = defaultdict(dict), defaultdict(dict)
    for r in valid:
        by_student[r["student"]][r["subject"]] = r["score"]
        by_subject[r["subject"]][r["student"]] = r["score"]
    return valid, repeated, incomplete, by_student, by_subject


# 5-6. SUMMARIZE AND ORDER ------------------------------------------------------
def summarize(grouped):
    out = []
    for name, scores in grouped.items():
        vals = list(scores.values())
        out.append({"name": name, "avg": sum(vals) / len(vals),
                    "high": max(vals), "low": min(vals), "count": len(vals)})
    return sorted(out, key=lambda s: (-s["avg"], s["name"]))  # best first


# 7. REPORT ---------------------------------------------------------------------
def build_report(last, seed, artist, records, valid, repeated, incomplete,
                 by_student, by_subject):
    L = []
    line = "=" * 64
    L += [line, "FINAL STUDENT PERFORMANCE REPORT", line,
          f"LAST_NAME: {last} | SEED_NUM: {seed} | FAVORITE_ARTIST: {artist}", ""]

    L += ["1. GENERATED PERFORMANCE RECORDS", "-" * 64,
          f"{'Student':<14}{'Subject':<14}{'Score':<8}"]
    for r in records:
        L.append(f"{r['student']:<14}{r['subject']:<14}"
                 f"{'MISSING' if r['score'] is None else r['score']:<8}")

    L += ["", "2. ORGANIZED STUDENT / SUBJECT DATA", "-" * 64,
          f"{'Student':<14}" + "".join(f"{s[:6]:<8}" for s in SUBJECTS)]
    for st in sorted(by_student):
        L.append(f"{st:<14}" + "".join(
            f"{by_student[st].get(s, '-'):<8}" for s in SUBJECTS))

    L += ["", "3. REPEATED / INCOMPLETE RECORDS", "-" * 64]
    for r in repeated:
        L.append(f"Repeated  : {r['student']} - {r['subject']} ({r['score']})")
    for r in incomplete:
        L.append(f"Incomplete: {r['student']} - {r['subject']} (no score)")

    L += ["", "4. PERFORMANCE CATEGORIES (valid records)", "-" * 64]
    for r in valid:
        L.append(f"{r['student']:<14}{r['subject']:<14}{r['score']:<6}{r['category']}")

    stu, sub = summarize(by_student), summarize(by_subject)
    L += ["", "5. SUMMARIES / 6. ORDERED RESULTS", "-" * 64,
          "Students ranked by average:",
          f"{'Rank':<6}{'Student':<14}{'Avg':<8}{'High':<6}{'Low':<6}Category"]
    for i, s in enumerate(stu, 1):
        L.append(f"{i:<6}{s['name']:<14}{s['avg']:<8.2f}{s['high']:<6}"
                 f"{s['low']:<6}{categorize(s['avg'])}")
    L += ["", "Subjects ranked by average:",
          f"{'Rank':<6}{'Subject':<14}{'Avg':<8}{'High':<6}{'Low':<6}"]
    for i, s in enumerate(sub, 1):
        L.append(f"{i:<6}{s['name']:<14}{s['avg']:<8.2f}{s['high']:<6}{s['low']:<6}")

    L += ["", "7. CONSOLIDATED SUMMARY", "-" * 64,
          f"Total records generated : {len(records)}",
          f"Valid records           : {len(valid)}",
          f"Repeated records        : {len(repeated)}",
          f"Incomplete records      : {len(incomplete)}",
          f"Top student             : {stu[0]['name']} ({stu[0]['avg']:.2f})",
          f"Strongest subject       : {sub[0]['name']} ({sub[0]['avg']:.2f})",
          f"Weakest subject         : {sub[-1]['name']} ({sub[-1]['avg']:.2f})", line]
    return "\n".join(L)


def main():
    last, seed, artist = get_inputs()
    students, records = generate_records(last, seed, artist)
    valid, repeated, incomplete, by_student, by_subject = analyze(records)
    report = build_report(last, seed, artist, records, valid, repeated,
                          incomplete, by_student, by_subject)
    print(report)
    with open("student_performance_report.txt", "w") as f:
        f.write(report)


if __name__ == "__main__":
    main()