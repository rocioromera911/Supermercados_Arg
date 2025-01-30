import json
import re
import pandas as pd
from difflib import SequenceMatcher
from datetime import datetime

# Función para encontrar coincidencias similares en el JSON
def find_best_match(name, json_products):
    best_match = None
    best_ratio = 0.0
    for product in json_products:
        ratio = SequenceMatcher(None, name.lower(), product['name'].lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = product
    return best_match if best_ratio > 0.7 else None  # Ajusta el umbral si es necesario

# Cargar el archivo JSON con los productos
json_file = 'vea_datos.json'
with open(json_file, 'r', encoding='utf-8') as js_file:
    js_data = json.load(js_file)

# Obtener lista de productos desde el JSON
json_products = [item['item'] for data in js_data for item in data.get('itemListElement', [])]

# Cargar el archivo de texto
text_file = 'vea_texto.txt'
with open(text_file, 'r', encoding='utf-8') as file:
    lines = [line.strip() for line in file if line.strip()]  # Eliminar líneas vacías

# Lista para almacenar los productos extraídos
products = []

# Procesar los productos en el TXT
i = 0
while i < len(lines):
    if "Ver Producto" in lines[i]:  # Identificar un nuevo producto
        brand = None
        name = None
        prices = []
        promotion_details = None
        price_per_unit = None

        # Obtener la marca y el nombre del producto
        if i + 1 < len(lines):
            brand = lines[i + 1]
        if i + 2 < len(lines):
            name = lines[i + 2]

        # Procesar precios y promociones dentro del bloque del producto
        j = i + 3
        while j < len(lines) and "Agregar" not in lines[j]:  # El bloque termina en "Agregar"
            if re.match(r'\$\d+[.,]?\d*', lines[j]):  # Detectar precios
                prices.append(float(lines[j].replace('$', '').replace('.', '').replace(',', '.')))
            elif re.match(r'(2x1|2do al \d+%|Llevando \d+)', lines[j]):  # Detectar promociones
                promotion_details = lines[j]
            elif "Precio" in lines[j]:  # Detectar precio por unidad
                price_per_unit = lines[j]  # Capturar la línea completa
            j += 1

        # Ordenar precios y asignar valores correctos
        prices = sorted(prices)
        promo_price = prices[0] if len(prices) > 0 else None
        previous_price = prices[1] if len(prices) > 1 else None

        # Buscar información en el JSON con coincidencia flexible
        json_product = find_best_match(name, json_products) if name else None

        # Obtener la fecha de extracción
        extraction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Guardar el producto en la lista final
        products.append({
            "name": name,
            "brand": brand,
            "promo_price": promo_price,
            "previous_price": previous_price,
            "price_per_unit": price_per_unit,
            "promotion_details": promotion_details,
            "image": json_product.get("image") if json_product else None,
            "description": json_product.get("description") if json_product else None,
            "mpn": json_product.get("mpn") if json_product else None,
            "gtin(js)": json_product.get("gtin") if json_product else None,
            "category(js)": None,  # Ajustar si el JSON tiene categorías
            "price_currency": json_product.get("offers", {}).get("priceCurrency") if json_product else None,
            "extraction_date": extraction_date
        })

        # Avanzar al siguiente bloque de producto
        i = j
    else:
        i += 1

# Guardar los datos en JSON y CSV
output_json = 'consolidated_data.json'
output_csv = 'consolidated_data.csv'

with open(output_json, 'w', encoding='utf-8') as json_file:
    json.dump(products, json_file, ensure_ascii=False, indent=4)

df = pd.DataFrame(products)
df.to_csv(output_csv, index=False)

print(f"Datos consolidados guardados en:\nJSON: {output_json}\nCSV: {output_csv}")
