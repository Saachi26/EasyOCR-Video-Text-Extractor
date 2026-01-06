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
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # GRAYSCALE: Remove color syntax highlighting
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # CONTRAST / THRESHOLDING
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
 
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

        # 2. Clean the Image
        clean_img = preprocess_image(original_img)

        # 3. Run AI with TUNED PARAMETERS
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
                
                # IMPORTANT: Since we upscaled the image 2x
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
