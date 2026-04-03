"""
Category Taxonomy Configuration

Defines the keyword-to-category mapping used by the TopicCategorizer.
Each keyword (including known typos, abbreviations, and misspellings) is mapped
to a strategic category that aligns with organizational improvement initiatives.

In the production system, this taxonomy contains ~280 keywords across ~10 categories,
including domain-specific abbreviations and commonly observed misspellings. The
example below demonstrates the structure and design intent with generic entries.

Design decisions:
- Keywords include known misspellings to ensure topic extraction succeeds on
  malformed input (see ADR-006)
- Single-word keywords are matched on both exact text and lemma form
- Multi-word phrases are matched as exact token sequences
- Categories align with organizational strategic initiatives, not abstract topics
"""

from dataclasses import dataclass


@dataclass
class CategoryEntry:
    """A single keyword-to-category mapping."""
    keyword: str
    category: str


# Example taxonomy - production version contains ~280 entries
CATEGORY_TAXONOMY: list[CategoryEntry] = [
    # Product / Platform
    CategoryEntry("platform", "product"),
    CategoryEntry("product", "product"),
    CategoryEntry("feature", "product"),
    CategoryEntry("functionality", "product"),
    CategoryEntry("integration", "product"),
    CategoryEntry("automation", "product"),
    CategoryEntry("workflow", "product"),
    CategoryEntry("interface", "product"),
    CategoryEntry("upgrade", "product"),
    CategoryEntry("deployment", "product"),
    CategoryEntry("scalability", "product"),
    CategoryEntry("reliability", "product"),
    CategoryEntry("customization", "product"),
    # Typo / misspelling variants -> same category
    CategoryEntry("customisation", "product"),
    CategoryEntry("reliablity", "product"),
    CategoryEntry("flexability", "product"),

    # Customer Engagement
    CategoryEntry("engagement", "engagement"),
    CategoryEntry("partnership", "engagement"),
    CategoryEntry("relationship", "engagement"),
    CategoryEntry("communication", "engagement"),
    CategoryEntry("responsive", "engagement"),
    CategoryEntry("proactive", "engagement"),
    CategoryEntry("professional", "engagement"),
    CategoryEntry("account manager", "engagement"),
    CategoryEntry("ease of doing business", "engagement"),

    # Support
    CategoryEntry("support", "support"),
    CategoryEntry("documentation", "support"),
    CategoryEntry("training", "support"),
    CategoryEntry("ticket", "support"),
    CategoryEntry("resolution", "support"),
    CategoryEntry("knowledge", "support"),
    CategoryEntry("timely", "support"),

    # Pricing
    CategoryEntry("price", "price"),
    CategoryEntry("cost", "price"),
    CategoryEntry("budget", "price"),
    CategoryEntry("affordable", "price"),
    CategoryEntry("spend", "price"),

    # High Price (always maps to "price is bad")
    CategoryEntry("expensive", "high-price"),
    CategoryEntry("overpriced", "high-price"),
    CategoryEntry("costly", "high-price"),
    CategoryEntry("pricey", "high-price"),

    # Licensing
    CategoryEntry("license", "licensing"),
    CategoryEntry("licensing", "licensing"),
    CategoryEntry("licence", "licensing"),
    # Common misspelling variants
    CategoryEntry("lisence", "licensing"),
    CategoryEntry("licensce", "licensing"),

    # Value / ROI
    CategoryEntry("value", "monetization"),
    CategoryEntry("investment", "monetization"),
    CategoryEntry("roi", "monetization"),

    # Transparency
    CategoryEntry("transparency", "transparency"),
    CategoryEntry("transparent", "transparency"),
    CategoryEntry("visibility", "transparency"),
]


def get_categories() -> dict[str, list[str]]:
    """
    Return the taxonomy as a dict of {category: [keywords]}.

    Used by the TopicCategorizer to build spaCy Matcher patterns.
    """
    taxonomy: dict[str, list[str]] = {}
    for entry in CATEGORY_TAXONOMY:
        taxonomy.setdefault(entry.category, []).append(entry.keyword)
    return taxonomy
