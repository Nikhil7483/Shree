import urllib.request
import os

def download_fonts():
    font_dir = os.path.dirname(os.path.abspath(__file__))
    regular_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf"
    bold_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Bold.ttf"
    
    reg_path = os.path.join(font_dir, "NotoSansKannada-Regular.ttf")
    bold_path = os.path.join(font_dir, "NotoSansKannada-Bold.ttf")
    
    print(f"Target directory: {font_dir}")
    
    try:
        print("Downloading NotoSansKannada-Regular.ttf...")
        urllib.request.urlretrieve(regular_url, reg_path)
        print(f"Saved Regular font to: {reg_path}")
        
        print("Downloading NotoSansKannada-Bold.ttf...")
        urllib.request.urlretrieve(bold_url, bold_path)
        print(f"Saved Bold font to: {bold_path}")
        print("Font download complete!")
    except Exception as e:
        print(f"Error downloading fonts: {e}")

if __name__ == "__main__":
    download_fonts()
