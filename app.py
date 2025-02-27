from flask import Flask, request, jsonify
import os
import base64
import io
from PIL import Image, ImageDraw

app = Flask(__name__)

def base64_to_image(base64_string):
    """ Convert base64 string to a PIL image """
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data)).convert("RGBA")

def image_to_base64(image):
    """ Convert PIL image to a base64 string """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Save as PNG to maintain transparency
    return base64.b64encode(buffered.getvalue()).decode()

def apply_circular_mask(image, size=(300, 300), border_width=5):
    """ Apply a circular mask and add a left-to-right green-to-blue gradient border """
    image = image.resize(size, Image.LANCZOS)

    # Create a circular mask
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((border_width, border_width, size[0] - border_width, size[1] - border_width), fill=255)

    # Apply mask to image
    circular_image = Image.new("RGBA", size, (0, 0, 0, 0))
    circular_image.paste(image, (0, 0), mask)

    # Create a left-to-right gradient border
    border = Image.new("RGBA", size, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)

    for x in range(size[0]):
        # Transition from Green (#1AE735) to Blue (#00A0DE)
        r = int(26 + (0 - 26) * (x / size[0]))   # Red component
        g = int(231 + (160 - 231) * (x / size[0])) # Green component
        b = int(53 + (222 - 53) * (x / size[0]))  # Blue component
        color = (r, g, b, 255)  # RGBA

        # Draw vertical gradient line
        border_draw.line([(x, 0), (x, size[1])], fill=color, width=border_width)

    # Mask the border to ensure it's circular
    border_mask = Image.new("L", size, 0)
    border_mask_draw = ImageDraw.Draw(border_mask)
    border_mask_draw.ellipse((0, 0, size[0], size[1]), fill=255)
    border.putalpha(border_mask)

    # Combine border and circular image
    final_image = Image.alpha_composite(border, circular_image)
    return final_image

@app.route("/process-image", methods=["POST"])
def process_image():
    """ Endpoint to process base64 image """
    try:
        req_data = request.json
        base64_string = req_data.get("image", "")

        if not base64_string:
            return jsonify({"error": "No image provided"}), 400

        # Convert Base64 to Image
        image = base64_to_image(base64_string)

        # Apply Circular Mask & Gradient Border
        modified_image = apply_circular_mask(image)

        # Convert back to Base64
        result_base64 = image_to_base64(modified_image)

        return jsonify({"image": result_base64})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    """ Default route to check if API is running """
    return "Image Processing API is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Ensure Flask binds to Render's assigned port
    app.run(host="0.0.0.0", port=port)
