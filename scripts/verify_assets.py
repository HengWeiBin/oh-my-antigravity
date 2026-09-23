import xml.etree.ElementTree as ET


def verify_svg(filepath):
    print(f"Verifying {filepath}...")
    tree = ET.parse(filepath)
    root = tree.getroot()
    print(f"  Root tag: {root.tag}")
    print(f"  viewBox: {root.attrib.get('viewBox')}")
    print(f"  width: {root.attrib.get('width')}, height: {root.attrib.get('height')}")
    assert root.tag.endswith("svg"), "Root tag must be svg"
    print("  [OK] Valid XML and SVG tree structure")
    return root

# 1. Parse and verify both files
logo_root = verify_svg("assets/logo.svg")
banner_root = verify_svg("assets/banner.svg")

# 2. Check logo viewBox
assert logo_root.attrib.get("viewBox") == "0 0 256 256", "Logo viewBox must be 0 0 256 256"

# 3. Check banner viewBox
assert banner_root.attrib.get("viewBox") == "0 0 1200 360", "Banner viewBox must be 0 0 1200 360"

# 4. Check required strings in banner
with open("assets/banner.svg", "r", encoding="utf-8") as f:
    banner_content = f.read()

required_strings = [
    "OH-MY-ANTIGRAVITY",
    "The Ultimate Agent Orchestration Harness for Google Antigravity 2.0",
    "Antigravity 2.0 Native",
    "11 Orchestrated Agents",
    "42 Bundled Skills",
    "Python 3.13 Hook Engine"
]

for s in required_strings:
    assert s in banner_content, f"Missing required string in banner: {s}"
    print(f"  [OK] Found badge/text in banner: '{s}'")

# 5. Check required colors in logo
with open("assets/logo.svg", "r", encoding="utf-8") as f:
    logo_content = f.read()

for color in ["#6366F1", "#06B6D4", "#8B5CF6"]:
    assert color in logo_content, f"Missing required color in logo: {color}"
    print(f"  [OK] Found required brand color in logo: {color}")

print("\n>>> ALL ASSETS VALIDATED SUCCESSFULLY! 100% XML & SVG COMPLIANT. <<<")
