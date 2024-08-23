import os
import json
import cv2
import pytesseract
import re

# Configuration du chemin vers l'exécutable Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    """Convertit l'image en niveaux de gris et applique un seuillage pour binariser."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def corriger_texte(texte):
    """Corrige les erreurs communes dans le texte OCR pour le set, le type et les termes spécifiques."""
    corrections = {
        # Types
        r'\beapon\b': 'weapon',
        r'\bWeapon\b': 'weapon',
        r'\bBreastplate\b': 'breastplate',
        r'\bAmulet\b': 'amulet',
        r'\bBangle\b': 'bangle',
        r'\bRing\b': 'ring',

        # Sets
        r'\bWarlord\b': 'warlord',
        r'\bSoulbound\b': 'soulbound_arcana',
        r'\bInvigoration\b': 'invigoration',
        r'\bInfernal\b': 'infernal_roar',
        r'\bAgeless\b': 'ageless_wrath',
    }
    
    for erreur, correction in corrections.items():
        texte = re.sub(erreur, correction, texte, flags=re.IGNORECASE)
    
    return texte

def extract_info(text):
    """Extrait le set, le type et les statistiques à partir du texte corrigé."""
    item_data = {
        "set": "",
        "type": "",
        "stats": {}
    }

    # Extraction du set et du type après correction du texte
    ancient_match = re.search(r"Ancient:\s*([\w\s]+)", text)
    type_match = re.search(r"(weapon|breastplate|amulet|bangle|ring)", text, re.IGNORECASE)

    if ancient_match:
        item_data["set"] = ancient_match.group(1).lower().strip()

    if type_match:
        item_data["type"] = type_match.group(1).lower()

    # Extraction des statistiques
    stats = {
        "ATK": r"ATK\s+(\d+)",
        "ATK Bonus": r"ATK\s*Bonus\s*([\d.]+)%",
        "Crit. DMG": r"Crit\.?\s*DMG\s*([\d.]+)%",
        "Crit. Rate": r"Crit\.?\s*Rate\s*([\d.]+)%",
        "ATK Spd.": r"ATK\s*Spd\.?\s*(\d+)",
        "HP": r"HP\s+(\d+)",
        "HP Bonus": r"HP\s*Bonus\s*([\d.]+)%",
        "DEF Bonus": r"DEF\s*Bonus\s*([\d.]+)%",
        "Healing Effect": r"Healing\s*Effect\s*(\d+)",
        "Rage Regen": r"Rage\s*Regen\s*([\d.]+)%"
    }

    for stat, pattern in stats.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            item_data["stats"][stat] = float(value) if '.' in value else int(value)

    # Vérification des Variants
    if "Aggression" in text:
        item_data["stats"]["Variant"] = "aggression"
    elif "Last Stand" in text:
        item_data["stats"]["Variant"] = "last_stand"
    
    return item_data

def analyze_image(image_path):
    """Analyse une image, extrait le texte, corrige le texte et en extrait les informations pertinentes."""
    print(f"Analyzing image: {image_path}")
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"Failed to load image: {image_path}")
        return None
    
    preprocessed = preprocess_image(img)
    
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(preprocessed, config=custom_config)
    
    # Appliquer les corrections sur le texte extrait
    corrected_text = corriger_texte(text)
    
    print(f"Extracted and corrected text:\n{corrected_text}")

    return extract_info(corrected_text)

def process_images(directory):
    """Parcourt un répertoire, analyse chaque image, et compile les résultats."""
    results = []
    print(f"Processing images in directory: {directory}")
    
    for filename in os.listdir(directory):
        print(f"Found file: {filename}")
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(directory, filename)
            item_data = analyze_image(image_path)
            if item_data:
                results.append({"data": item_data})
                
    return results

if __name__ == "__main__":
    image_directory = r"C:\wamp64\www\img"
    print(f"Starting analysis in directory: {image_directory}")
    output = process_images(image_directory)
    
    with open("item_analysis.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Analysis complete. Results saved in item_analysis.json")
    print(f"Number of items processed: {len(output)}")
