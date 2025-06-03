import os
import io
import base64
from django.conf import settings
from django.shortcuts import render
from PIL import Image, ImageDraw, ImageFont
import easyocr

# Initialize EasyOCR reader globally (loads model once)
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have GPU support


def group_words_by_line(ocr_result, line_tol=10):
    """
    Groups OCR words by their vertical position into lines.
    line_tol: vertical tolerance in pixels to group words in the same line.
    """
    # Sort by the y-coordinate (top-left corner of bounding box)
    ocr_result = sorted(ocr_result, key=lambda x: x[0][0][1])

    lines = []
    current_line = []
    current_y = None

    for bbox, text, conf in ocr_result:
        y = bbox[0][1]  # top-left y coordinate
        if current_y is None or abs(y - current_y) <= line_tol:
            current_line.append((bbox, text))
            if current_y is None:
                current_y = y
        else:
            lines.append(current_line)
            current_line = [(bbox, text)]
            current_y = y
    if current_line:
        lines.append(current_line)
    return lines


def lines_to_text(lines):
    """
    Convert grouped lines to text, sorting words from left to right.
    """
    all_lines_text = []
    for line in lines:
        # Sort words in the line by x-coordinate (left to right)
        line = sorted(line, key=lambda x: x[0][0][0])
        line_text = " ".join([word for bbox, word in line])
        all_lines_text.append(line_text)
    return "\n".join(all_lines_text)


def index(request):
    extracted_text = ""
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']
        img = Image.open(image_file).convert('RGB')  # Ensure RGB format

        # Convert PIL Image to bytes for EasyOCR
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Run OCR on image bytes
        result = reader.readtext(buffer.getvalue())

        # Group words by lines, preserving layout
        grouped_lines = group_words_by_line(result)
        extracted_text = lines_to_text(grouped_lines)

    return render(request, 'converter/index.html', {'extracted_text': extracted_text})


def handwriting(request):
    generated_image_data = None
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            font_path = os.path.join(
                settings.BASE_DIR, 'converter', 'static', 'converter', 'fonts', 'EduQLDHand-Regular.ttf'
            )
            font_size = 40
            font = ImageFont.truetype(font_path, font_size)

            image_width = 800
            lines = text.split('\n')  # Preserve line breaks from extracted text

            # Calculate height of image based on number of lines
            line_height = font.getbbox("Ay")[3] + 10
            image_height = 20 + line_height * len(lines)

            # Create blank white image
            img = Image.new('RGB', (image_width, image_height), color='white')
            draw = ImageDraw.Draw(img)

            y = 10
            for line in lines:
                draw.text((10, y), line, font=font, fill=(0, 0, 255))  # Blue text
                y += line_height

            # Encode image as base64 for embedding in HTML
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            generated_image_data = f"data:image/png;base64,{img_str}"

    return render(request, 'converter/handwriting.html', {'generated_image_data': generated_image_data})
