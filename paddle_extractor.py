import os
from paddleocr import PaddleOCR
import re

# Initialize PaddleOCR (using english and hindi, with angle classification)
ocr = PaddleOCR(use_angle_cls=True, lang='hi')

def extract_land_record(image_path: str) -> dict:
    """
    Runs PaddleOCR on the given image and parses the raw text into structured fields.
    """
    result = ocr.ocr(image_path)
    
    raw_texts = []
    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            raw_texts.append(text)
            
    full_text = " ".join(raw_texts)
    
    # Initialize default structure
    parsed_record = {
        "khasraNumber": "",
        "ownerName": "",
        "area": "",
        "landType": "",
        "district": "",
        "tehsil": "",
        "state": "",
        "village": "",
        "taxAmount": "",
        "raw_text": full_text # Keeping raw text for reference
    }

    # Basic regex patterns to attempt field extraction
    # Since OCR can be noisy, these are best-effort heuristics.
    
    # Khasra Number (e.g., Khasra No. 123/4)
    khasra_match = re.search(r'(?i)(khasra\s*(no\.?|number)?\s*:?\s*)([0-9a-zA-Z/-]+)', full_text)
    if khasra_match:
        parsed_record["khasraNumber"] = khasra_match.group(3).strip()

    # Owner Name (e.g., Owner: John Doe, or Name of Owner: Jane Doe)
    owner_match = re.search(r'(?i)(owner\s*name|name\s*of\s*owner|owner)\s*:?\s*([A-Za-z\s]+)', full_text)
    if owner_match:
        parsed_record["ownerName"] = owner_match.group(2).strip()
        
    # Area (e.g., 12.5 Hectares, 100 Sq m)
    area_match = re.search(r'(?i)(area\s*:?\s*)([0-9.]+\s*(hectare|sq\s*m|acre|bigha|biswa)s?)', full_text)
    if area_match:
        parsed_record["area"] = area_match.group(2).strip()

    # District
    district_match = re.search(r'(?i)(district|zila)\s*:?\s*([A-Za-z]+)', full_text)
    if district_match:
        parsed_record["district"] = district_match.group(2).strip()

    # Tehsil
    tehsil_match = re.search(r'(?i)(tehsil)\s*:?\s*([A-Za-z]+)', full_text)
    if tehsil_match:
        parsed_record["tehsil"] = tehsil_match.group(2).strip()

    # Village
    village_match = re.search(r'(?i)(village|gram)\s*:?\s*([A-Za-z]+)', full_text)
    if village_match:
        parsed_record["village"] = village_match.group(2).strip()

    # State
    state_match = re.search(r'(?i)(state)\s*:?\s*([A-Za-z\s]+)', full_text)
    if state_match:
        parsed_record["state"] = state_match.group(2).strip()
        
    # Tax/Revenue Amount
    tax_match = re.search(r'(?i)(tax|revenue|lagaan)\s*:?\s*(rs\.?|₹|inr)?\s*([0-9.,]+)', full_text)
    if tax_match:
        parsed_record["taxAmount"] = tax_match.group(3).strip()

    return parsed_record
