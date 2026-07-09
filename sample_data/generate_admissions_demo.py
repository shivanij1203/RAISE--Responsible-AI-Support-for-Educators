"""Generate a synthetic MS CS admissions CSV for the RAISE demo.

Two screenshots come out of this single file:
  1. PII scan: file contains seeded fake SSNs, emails, phones — scanner flags them.
  2. Bias audit: ai_recommendation is biased against Black + Hispanic applicants
     even at matched GPA/GRE, so the audit surfaces disparate impact.

All names, SSNs (900-prefix is reserved by IRS), emails (.invalid TLD reserved
by RFC 2606), and phones (555-01xx reserved by NANP) are guaranteed fake.

Output: raise_demo_admissions.csv (200 rows) in the same directory.
"""
import csv
import random
from pathlib import Path

random.seed(42)

FIRST_NAMES = [
    "Aarav", "Priya", "Marcus", "Aisha", "Diego", "Mei", "Jamal", "Sofia",
    "Liam", "Zara", "Noah", "Imani", "Lucas", "Fatima", "Ethan", "Yara",
    "Mateo", "Anika", "Andre", "Layla", "Kai", "Naomi", "Omar", "Tara",
    "Reese", "Kenji", "Dante", "Lila", "Theo", "Esme",
]
LAST_NAMES = [
    "Patel", "Johnson", "Garcia", "Chen", "Williams", "Nguyen", "Brown",
    "Rodriguez", "Singh", "Davis", "Martinez", "Wang", "Jackson", "Khan",
    "Lopez", "Liu", "Thomas", "Gonzalez", "Kim", "Robinson", "Hernandez",
    "Park", "Washington", "Reyes", "Sharma", "Taylor", "Diaz", "Wilson",
]

# Realistic distribution for an MS CS applicant pool
RACES = (
    ["Asian"] * 70 +
    ["White"] * 60 +
    ["Hispanic"] * 35 +
    ["Black"] * 25 +
    ["Other"] * 10
)
GENDERS = ["Male"] * 110 + ["Female"] * 80 + ["Non-binary"] * 10


def fake_ssn() -> str:
    # 900-999 area numbers are reserved (ITINs) — never issued as real SSNs.
    return f"9{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def fake_phone() -> str:
    # 555-0100 through 555-0199 are reserved for fictional use.
    return f"(813) 555-0{random.randint(100, 199)}"


def fake_email(first: str, last: str) -> str:
    # .invalid is a reserved TLD that will never resolve.
    return f"{first.lower()}.{last.lower()}{random.randint(1, 99)}@example.invalid"


def biased_recommendation(race: str, gpa: float, gre: int) -> str:
    """Engineer disparate impact: same credentials, lower advance rate for Black/Hispanic."""
    base_score = (gpa - 3.0) * 50 + (gre - 290) * 1.5  # ~0 to 100

    # Penalize underrepresented groups — this is the bias the audit should catch.
    if race in ("Black", "Hispanic"):
        base_score -= 18
    elif race == "Asian":
        base_score += 4

    if base_score >= 55:
        return "advance"
    if base_score >= 30:
        return "hold"
    return "decline"


def main() -> None:
    out_path = Path(__file__).parent / "raise_demo_admissions.csv"
    rows = []

    for i in range(1, 201):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        race = random.choice(RACES)
        gender = random.choice(GENDERS)
        gpa = round(random.uniform(3.0, 4.0), 2)
        gre = random.randint(290, 340)
        rec = biased_recommendation(race, gpa, gre)

        rows.append({
            "applicant_id": f"APP-2026-{i:04d}",
            "first_name": first,
            "last_name": last,
            "email": fake_email(first, last),
            "phone": fake_phone(),
            "ssn": fake_ssn(),
            "gender": gender,
            "race": race,
            "undergrad_gpa": gpa,
            "gre_score": gre,
            "ai_recommendation": rec,
        })

    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Quick sanity print so you can verify the disparate impact before uploading.
    print(f"Wrote {len(rows)} rows to {out_path}\n")
    print("Advance rate by race (this is what the bias audit will surface):")
    by_race: dict[str, list[str]] = {}
    for r in rows:
        by_race.setdefault(r["race"], []).append(r["ai_recommendation"])
    for race, recs in sorted(by_race.items()):
        adv = sum(1 for x in recs if x == "advance")
        print(f"  {race:10s} n={len(recs):3d}  advance={adv:3d}  rate={adv/len(recs):.0%}")


if __name__ == "__main__":
    main()
