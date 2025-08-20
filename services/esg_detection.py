import re
from collections import defaultdict

# ESG frameworks and detection patterns
FRAMEWORKS = {
    "Science Based Targets initiative (SBTi)": [r"\bSBTi\b", r"science based targets?"],
    "Global Reporting Initiative (GRI)": [r"\bGRI\b", r"global reporting initiative"],
    "GHG Protocol": [r"\bGHG Protocol\b", r"greenhouse gas protocol"],
    "Social & Labor Convergence Program (SLCP)": [r"\bSLCP\b"],
    "Carbon Disclosure Project (CDP)": [r"\bCDP\b", r"carbon disclosure project"],
    "Net Zero": [r"\bnet zero\b"],
    "ISO 14001": [r"\bISO 14001\b"],
    "UN Global Compact": [r"\bUN Global Compact\b"]
}

# Section headers to detect
SECTION_HEADERS = [
    "climate", "environment", "emissions", "energy",
    "governance", "ethics", "board", "compliance",
    "social", "labor", "community", "diversity", "equity", "inclusion",
    "supply chain", "sustainability strategy"
]

def detect_esg_with_sections(text: str, company_name: str = "Company"):
    """Detect ESG initiatives with section-level tagging and return a Markdown summary."""
    lines = text.split("\n")
    current_section = "General"
    results = defaultdict(list)

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        # Simple check for a section header. You might want a more robust check.
        # This checks if the line is short and contains a keyword.
        is_header = any(h.lower() in clean_line.lower() for h in SECTION_HEADERS) and len(clean_line) < 100
        if is_header:
            current_section = clean_line.strip()
            continue

        # Search for ESG frameworks in this line
        for framework, patterns in FRAMEWORKS.items():
            for pat in patterns:
                if re.search(pat, clean_line, re.IGNORECASE):
                    results[framework].append({
                        "section": current_section,
                        "evidence": clean_line
                    })
                    break  # Stop at first match for this line

    # ---- ESG Score + Grade ----
    total_mentions = sum(len(v) for v in results.values())
    score = min(100, total_mentions) # Adjusted scoring to be 1 mention = 1 point, max 100
    grade = "A - Excellent" if score >= 80 else "B - Good" if score >= 50 else "C - Needs Improvement"

    # ---- NEW: Build Markdown Summary ----
    summary_lines = []
    
    # Main Title
    summary_lines.append(f"### 📊 ESG Analysis: **{company_name}.pdf**")
    summary_lines.append("\nHere is a summary of the ESG analysis, designed for clarity and quick insights.")
    summary_lines.append("\n---\n")

    # Executive Summary Table
    summary_lines.append("### **Executive Summary**")
    summary_lines.append("\n| Metric | Result |")
    summary_lines.append("| :--- | :--- |")
    summary_lines.append(f"| 🏆 **Overall ESG Score** | **{score} (Grade: {grade})** |")
    summary_lines.append(f"| ✅ **Total ESG Mentions** | **{total_mentions}** |")
    summary_lines.append(f"| 🔎 **Frameworks Detected** | **{len(results)}** |")
    summary_lines.append("\n---\n")

    # Detailed Breakdown
    summary_lines.append("### **Detailed Framework Breakdown**")

    if not results:
        summary_lines.append("No specific ESG framework mentions were detected in the document.")
    else:
        # Sort frameworks by number of mentions for a cleaner report
        sorted_frameworks = sorted(results.items(), key=lambda item: len(item[1]), reverse=True)
        
        for framework, mentions in sorted_frameworks:
            unique_sections = set(m['section'] for m in mentions)
            summary_lines.append(f"\n#### **1. {framework}**")
            summary_lines.append(f"*   **Total Mentions:** {len(mentions)}")
            summary_lines.append(f"*   **Unique Sections:** {len(unique_sections)}")
            summary_lines.append(f"*   **Example Evidence:**")
            
            # Show up to 2 evidence snippets
            for mention in mentions[:2]:
                evidence_snippet = mention['evidence']
                if len(evidence_snippet) > 150:
                    evidence_snippet = evidence_snippet[:150] + "..."
                summary_lines.append(f"    *   *\"...{evidence_snippet}...\"*")

    summary = "\n".join(summary_lines)

    # Return the 4 values cleanly
    return results, score, grade, summary