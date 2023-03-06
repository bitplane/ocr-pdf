#!/usr/bin/env python3
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
  
  
def pdf_to_img(pdf_bytes: bytes, dpi: int) -> Image:
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    for image in images:
        yield image


def extract_text(image: Image, dpi: int):
    rgb_image = image.convert('RGB')

    data = pytesseract.image_to_data(rgb_image, output_type=pytesseract.Output.DICT, config=f'--dpi {dpi}')

    regions = data['block_num']

    region_ids = set(regions)

    for region_id in region_ids:
        word_ids = [i for i, r in enumerate(regions) if r == region_id]
        region_words = [data['text'][i] for i in word_ids if data['text'][i].strip()]
        x0 = min(data['left'][i] for i in word_ids)
        x1 = max(data['left'][i] + data['width'][i] for i in word_ids)
        y0 = min(data['top'][i] for i in word_ids)
        y1 = max(data['top'][i] + data['height'][i] for i in word_ids)

        text = ' '.join(region_words)

        if not text:
            continue
        
        yield {
            'text': text,
            'x0': x0,
            'x1': x1,
            'y0': y0,
            'y1': y1,
        }


def extract_pdf(pdf_bytes: bytes, dpi: int) -> dict:
    result = {}
    for page, image in enumerate(pdf_to_img(pdf_bytes, dpi)):
        for box in extract_text(image, dpi):
            if page not in result:
                result[page] = {"width": image.width, "height": image.height, "text": []}
            result[page]["text"].append(box)

    return result


if __name__ == '__main__':
    import sys
    import json

    with open(sys.argv[1], 'rb') as f:
        pdf_bytes = f.read()

    result = extract_pdf(pdf_bytes, 200)

    print(json.dumps(result, indent=4))
