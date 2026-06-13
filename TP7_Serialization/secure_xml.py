import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

MAX_XML_SIZE = 1_000_000
EXPECTED_FIELDS = {"id", "subject", "creator", "date"}

def parse_report_xml(raw_xml: str) -> dict:
    if len(raw_xml) > MAX_XML_SIZE:
        logger.warning("XML too large: %d bytes", len(raw_xml))
        raise ValueError("Payload too large")

    upper_xml = raw_xml.upper()

    if "<!DOCTYPE" in upper_xml or "<!ENTITY" in upper_xml:
        logger.warning("DOCTYPE or ENTITY detected")
        raise ValueError("Invalid payload")

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as e:
        logger.warning("Malformed XML: %s", e)
        raise ValueError("Invalid payload")

    result = {}

    for field in EXPECTED_FIELDS:
        element = root.find(field)

        if element is not None and element.text:
            result[field] = element.text.strip()

    missing = {"id", "subject"} - result.keys()

    if missing:
        logger.warning("Missing fields: %s", missing)
        raise ValueError("Invalid payload")

    return result

if __name__ == "__main__":
    valid_xml = """<?xml version="1.0"?>
<report>
    <id>42</id>
    <subject>Network audit</subject>
    <creator>Mouaad</creator>
    <date>2026-04-25</date>
</report>"""

    result = parse_report_xml(valid_xml)
    print("Parsed XML:")
    print(result)

    malicious_xml = """<?xml version="1.0"?>
<!DOCTYPE report [
<!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<report>
    <id>1</id>
    <subject>&xxe;</subject>
</report>"""

    try:
        parse_report_xml(malicious_xml)
    except ValueError as e:
        print("Rejected:", e)