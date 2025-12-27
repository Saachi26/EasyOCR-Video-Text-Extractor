from flask import Flask, request, jsonify
from flask_cors import CORS
import easyocr
import numpy as np
import cv2
import base64

app = Flask(__name__)
CORS(app)

print("⏳ Loading AI Model...")
# Load the model with GPU
reader = easyocr.Reader(['en'], gpu=True)
print("✅ AI Model Loaded & Ready!")

def preprocess_image(img):
    """
    The 'Senior Engineer' cleaning pipeline.
    This makes blurry video frames look like crisp scanned documents.
    """
    # 1. UPSCALING: Resize the image to be 2x bigger (Zoom In)
    # This helps MASSIVELY with small code font.
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # 2. GRAYSCALE: Remove color syntax highlighting (confuses OCR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. CONTRAST / THRESHOLDING (Optional but powerful)
    # This forces text to be pure black and background pure white.
    # Note: If this breaks 'dark mode' code, comment this line out.
    # _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # For now, let's just use the sharpened grayscale image
    return gray

def read_base64_image(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_bytes = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

@app.route('/ocr', methods=['POST'])
def ocr_process():
    try:
        data = request.json
        image_data = data.get('image')

        if not image_data:
            return jsonify({"error": "No image provided"}), 400

        # 1. Decode Image
        original_img = read_base64_image(image_data)

        # 2. Clean the Image (The new magic step)
        clean_img = preprocess_image(original_img)

        # 3. Run AI with TUNED PARAMETERS
        # mag_ratio=2.0 -> Tells EasyOCR to magnify image internally (Critical for small text)
        # text_threshold=0.5 -> Be stricter about what counts as text
        # low_text=0.3 -> Help detect low-contrast text
        results = reader.readtext(
            clean_img, 
            mag_ratio=2.0,  
            text_threshold=0.6, 
            low_text=0.35
        )

        output = []
        for (bbox, text, prob) in results:
            if prob > 0.4: 
                (tl, tr, br, bl) = bbox
                
                # IMPORTANT: Since we upscaled the image 2x, 
                # we must divide the coordinates by 2 to match the original video size!
                scale_down = 0.5 
                
                output.append({
                    "text": text,
                    "confidence": float(prob),
                    "box": {
                        "x": int(tl[0] * scale_down),
                        "y": int(tl[1] * scale_down),
                        "width": int((tr[0] - tl[0]) * scale_down),
                        "height": int((bl[1] - tl[1]) * scale_down)
                    }
                })

        return jsonify({"success": True, "data": output})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)