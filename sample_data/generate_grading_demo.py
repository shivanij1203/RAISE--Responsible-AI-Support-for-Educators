"""Generate a synthetic grading roster CSV for the RAISE demo.

Tests two flows in one file:
  1. Personal-info cleanup: name, email, phone, student_id columns get redacted.
  2. Grading prompt: submission_excerpt varies in quality so the AI tool
     can produce a real differentiated grade against any rubric.

All names, emails (.invalid TLD reserved by RFC 2606), and phones
(555-01xx reserved by NANP) are synthetic and safe.

Output: raise_demo_grading.csv (24 rows) in the same directory.
"""
import csv
import random
from pathlib import Path

random.seed(42)

FIRST_NAMES = [
    "Aarav", "Priya", "Marcus", "Aisha", "Diego", "Mei", "Jamal", "Sofia",
    "Liam", "Zara", "Noah", "Imani", "Lucas", "Fatima", "Ethan", "Yara",
    "Mateo", "Anika", "Andre", "Layla", "Kai", "Naomi", "Omar", "Tara",
]
LAST_NAMES = [
    "Patel", "Johnson", "Garcia", "Chen", "Williams", "Nguyen", "Brown",
    "Rodriguez", "Singh", "Davis", "Martinez", "Wang", "Jackson", "Khan",
    "Lopez", "Liu", "Thomas", "Gonzalez", "Kim", "Robinson", "Hernandez",
    "Park", "Washington", "Reyes",
]

COURSE = "MIS 4123"
SECTION = "001"
ASSIGNMENT = "Essay 2: Responsible AI Use in Business"

# Three quality tiers for submission excerpts so a grading prompt can
# actually produce different grades. Each excerpt is the first ~80 words
# of a hypothetical student essay.

STRONG = [
    "This paper argues that responsible AI use in business requires three concrete safeguards: a documented audit trail, a fairness review tied to specific protected attributes, and a publicly accessible disclosure to affected stakeholders. For example, when Amazon retired its internal hiring tool in 2018, the company cited disparate impact against women in technical roles (Reuters, 2018). I will apply these three safeguards to a hypothetical hiring system at Acme Corp and show how each one closes a specific compliance gap identified by the EU AI Act.",
    "Drawing on the 2024 NIST AI Risk Management Framework, I propose a three-stage governance model: pre-deployment risk classification, in-deployment monitoring against drift, and post-deployment contestation rights for affected users. Each stage maps to a specific regulatory requirement under the Colorado AI Act §6-1-1707. To make this concrete, I trace the lifecycle of a fictional credit-scoring AI through all three stages and identify exactly which artifacts the firm must produce at each step.",
    "Responsible AI use is best understood not as a single checklist but as a sustained organizational capability. This essay defends that thesis using three case studies (Apple Card 2019, COMPAS 2016, GPT in admissions 2024) and shows that in each case the failure was structural rather than technical. The pattern is clear: firms that treat AI ethics as a one-time review fail; firms that build continuous governance succeed.",
]

MEDIUM = [
    "AI is changing how businesses operate. Companies use AI for hiring, marketing, and customer service. There are some risks though, like bias and privacy issues. This essay will discuss responsible AI in business and suggest some best practices. I will look at examples from companies and discuss what they did right and wrong. Overall, AI can be useful but companies need to be careful.",
    "In the modern business world, AI tools are everywhere. From ChatGPT for writing emails to recommendation engines, AI helps companies be more efficient. However, there are concerns about how these tools are used. Some people worry about jobs being lost, others worry about bias. This paper will discuss some of these issues and offer thoughts on how companies should handle AI responsibly going forward.",
    "Responsible AI matters because companies that misuse AI face legal and reputational risk. This essay covers three main topics: what responsible AI means, why it matters, and how companies can do it. I will use some examples and refer to ideas from class. The conclusion is that companies should be careful with AI and follow good practices.",
]

WEAK = [
    "AI is good and bad. Companies use it a lot. This essay will talk about AI in business and why it should be responsible. There are many things to consider when using AI, like ethics. I think AI is important and will continue to grow in the future.",
    "Artificial intelligence is a powerful technology that businesses are using more and more. It can do many things that humans used to do. But it can also have problems. Companies need to use it the right way. In this paper I will discuss this topic.",
    "AI ethics is a big topic. There are many opinions about it. Some people think AI is good and some think it is bad. Companies should think about ethics when they use AI. This paper will explore this issue.",
]


def make_email(first: str, last: str) -> str:
    return f"{first.lower()}.{last.lower()}@students.usf.invalid"


def make_phone() -> str:
    last_two = random.randint(1, 30)
    return f"555-01{last_two:02d}"


def make_student_id() -> str:
    return f"U{random.randint(10000000, 99999999)}"


def main() -> None:
    out_path = Path(__file__).parent / "raise_demo_grading.csv"
    rows: list[dict] = []
    used_pairs: set[tuple[str, str]] = set()

    # 24 rows: 8 strong, 10 medium, 6 weak
    plan = (
        [("strong", e) for e in STRONG] * 3
        + [("medium", e) for e in MEDIUM] * 4
        + [("weak", e) for e in WEAK] * 2
    )
    random.shuffle(plan)
    plan = plan[:24]

    for i, (tier, excerpt) in enumerate(plan, start=1):
        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            if (first, last) not in used_pairs:
                used_pairs.add((first, last))
                break
        rows.append({
            "student_id": make_student_id(),
            "first_name": first,
            "last_name": last,
            "email": make_email(first, last),
            "phone": make_phone(),
            "course": COURSE,
            "section": SECTION,
            "assignment": ASSIGNMENT,
            "submitted_on": f"2026-04-{random.randint(20, 30):02d}",
            "word_count": len(excerpt.split()) + random.randint(700, 1100),
            "submission_excerpt": excerpt,
            "quality_tier_internal": tier,
            "current_grade": "",
        })

    fieldnames = list(rows[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    print(f"Tiers: strong={sum(1 for r in rows if r['quality_tier_internal']=='strong')}, "
          f"medium={sum(1 for r in rows if r['quality_tier_internal']=='medium')}, "
          f"weak={sum(1 for r in rows if r['quality_tier_internal']=='weak')}")


if __name__ == "__main__":
    main()
