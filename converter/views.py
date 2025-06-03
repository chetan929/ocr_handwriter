import os
import io
import base64
from django.conf import settings
from django.shortcuts import render
from PIL import Image, ImageDraw, ImageFont
import easyocr

# Create the OCR reader once globally to avoid reloading models on every request
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if GPU available


def group_words_by_line(ocr_result, line_tol=10):
    """
    Groups OCR words by their vertical position into lines.
    line_tol: vertical tolerance in pixels to group words in same line.
    """
    lines = []
    ocr_result = sorted(ocr_result, key=lambda x: x[0][0][1])  # Sort by top-left y coordinate

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
    Convert grouped lines to text, sorting words left-to-right.
    """
    all_lines_text = []
    for line in lines:
        # Sort words by left coordinate (x)
        line = sorted(line, key=lambda x: x[0][0][0])
        line_text = " ".join([word for bbox, word in line])
        all_lines_text.append(line_text)
    return "\n".join(all_lines_text)


def index(request):
    extracted_text = ""
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']
        img = Image.open(image_file).convert('RGB')  # Ensure RGB format

        # Convert PIL image to bytes for EasyOCR
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Run OCR using EasyOCR on the image bytes
        result = reader.readtext(buffer.getvalue())

        # Group words into lines preserving their layout
        grouped_lines = group_words_by_line(result)
        extracted_text = lines_to_text(grouped_lines)

    return render(request, 'converter/index.html', {'extracted_text': extracted_text})


def handwriting(request):
    generated_image_data = None
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            font_path = os.path.join(settings.BASE_DIR, 'converter', 'static', 'converter', 'fonts', 'EduQLDHand-Regular.ttf')
            font_size = 40
            font = ImageFont.truetype(font_path, font_size)

            image_width = 800
            # Use line breaks as-is, no extra wrapping
            lines = text.split('\n')

            line_height = font.getbbox("Ay")[3] + 10
            image_height = 20 + line_height * len(lines)

            img = Image.new('RGB', (image_width, image_height), color='white')
            draw = ImageDraw.Draw(img)

            y = 10
            for line in lines:
                draw.text((10, y), line, font=font, fill=(0, 0, 255))  # Blue text
                y += line_height

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            generated_image_data = f"data:image/png;base64,{img_str}"

    return render(request, 'converter/handwriting.html', {'generated_image_data': generated_image_data})
