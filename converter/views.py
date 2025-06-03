# converter/views.py
import os
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import io
import base64


def index(request):
    extracted_text = ""
    if request.method == 'POST' and 'image' in request.FILES:
        image_file = request.FILES['image']
        img = Image.open(image_file)

        # OCR processing
        extracted_text = pytesseract.image_to_string(img)

        context = {
            'extracted_text': extracted_text,
        }
        return render(request, 'converter/index.html', context)

    return render(request, 'converter/index.html')


def handwriting(request):
    generated_image_data = None
    if request.method == 'POST':
        text = request.POST.get('text', '')
        if text.strip():
            font_path = os.path.join(settings.BASE_DIR, 'converter', 'static', 'converter', 'fonts', 'EduQLDHand-Regular.ttf')
            font_size = 40
            font = ImageFont.truetype(font_path, font_size)

            # Set fixed image width
            image_width = 800
            dummy_image = Image.new("RGB", (image_width, 1))
            draw = ImageDraw.Draw(dummy_image)

            # Wrap text manually
            lines = []
            words = text.split()
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if draw.textlength(test_line, font=font) < image_width - 20:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)

            line_height = font.getbbox("Ay")[3] + 10
            image_height = 20 + line_height * len(lines)

            img = Image.new('RGB', (image_width, image_height), color='white')
            draw = ImageDraw.Draw(img)

            y = 10
            for line in lines:
                draw.text((10, y), line, font=font, fill=(0, 0, 255))  # Blue color
                y += line_height

            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            generated_image_data = f"data:image/png;base64,{img_str}"

    return render(request, 'converter/handwriting.html', {'generated_image_data': generated_image_data})
