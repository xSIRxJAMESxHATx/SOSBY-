from PIL import Image
import os

def generate_favicon():
    img_name = "Copilot_20260726_103333.png"
    
    if not os.path.exists(img_name):
        print(f"Error: {img_name} not found in the current directory.")
        return

    # Open the provided image
    img = Image.open(img_name)

    # Crop coordinates (Left, Top, Right, Bottom) - tightly framing the owl's head/crown
    crop_area = (150, 50, 750, 650)
    cropped_img = img.crop(crop_area)

    # Resize to standard favicon sizes
    icon_sizes = [(16,16), (32, 32), (64, 64), (192, 192)]
    cropped_img.save("favicon.ico", format="ICO", sizes=icon_sizes)
    print("favicon.ico created successfully!")

if __name__ == "__main__":
    generate_favicon()