import json
import re
import pandas as pd
from datetime import datetime

# Rutas de los archivos
file_path_json = "script_text_im.txt"
file_path_text = "body_text_im.txt"

# Leer el contenido del archivo script_text.txt
with open(file_path_json, "r", encoding="utf-8") as file:
    data_json = file.read()

# Extraer todas las listas de productos contenidas en los objetos JSON
matches = re.findall(r'"items":(\[.*?\])\s*\}', data_json, re.DOTALL)

# Parsear los datos JSON
products_json = []
for match in matches:
    items = json.loads(match)  # Convertir string JSON a lista de diccionarios
    products_json.extend(items)  # Agregar los productos a la lista final

# Crear DataFrame a partir del JSON
df_json = pd.DataFrame(products_json)

# Leer el contenido del archivo body_text.txt
with open(file_path_text, "r", encoding="utf-8") as archivo:
    texto = archivo.read()

# Expresión regular mejorada para capturar datos
patron = re.compile(
    r'\$([\d,]+\.\d{2})x un\.?'
    r'(?:antes\$([\d,]+\.\d{2})x un\.?)?'
    r'\.?([^$]+)\$ ([\d.]+) x (Unidad|Gramos)'
    r'(\d+)?(?:Llevando (\d+):\$([\d,]+\.\d{2})c/u)?')

datos_texto = []
for match in patron.finditer(texto):
    precio_actual = match.group(1).replace(',', '')
    precio_anterior = match.group(2).replace(',', '') if match.group(2) else ''
    producto = match.group(3).strip()
    precio_unidad = match.group(4)
    tipo_unidad = match.group(5)

    oferta = ''
    if match.group(7) and match.group(8):
        oferta = f"Llevando {match.group(7)}: ${match.group(8).replace(',', '')} c/u"

    datos_texto.append({
        'Producto': producto,
        'Precio Actual': float(precio_actual),
        'Precio Anterior': float(precio_anterior) if precio_anterior else None,
        'Precio Unitario': float(precio_unidad),
        'Unidad': tipo_unidad,
        'Oferta': oferta if oferta else None
    })

# Crear DataFrame con pandas para body_text.txt
df_text = pd.DataFrame(datos_texto)

# Unir los DataFrames utilizando la columna 'item_name' y 'Producto' como referencia
df_merged = df_json.merge(df_text, left_on="item_name", right_on="Producto", how="left")

# Eliminar duplicados y columnas innecesarias
df_merged.drop(columns=["Producto"], inplace=True)

# Agregar columna con la fecha de extracción y el nombre del supermercado
df_merged["Fecha Extraccion"] = datetime.today().strftime('%Y-%m-%d')
df_merged["Supermercado"] = "Mami"

# Agregar columna de categoría vacía para que el usuario la complete
df_merged["Categoria"] = "almacen"

# Guardar el DataFrame en un archivo Excel
output_file_path = "productos_combinados.xlsx"
df_merged.to_excel(output_file_path, index=False, engine='openpyxl')

print(f"Archivo guardado en: {output_file_path}")
