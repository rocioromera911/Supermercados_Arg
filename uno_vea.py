import time
import json
import os
from playwright.sync_api import sync_playwright
import re

##################################################
# 1. Seleccionar sucursal (solo una vez)
##################################################
def seleccionar_sucursal(page, provincia, tienda):
    """
    Función para seleccionar la provincia y la sucursal en el sitio de Vea.
    """
    try:
        print("Seleccionando método de entrega...")
        page.click('a:has-text("Seleccioná el método de entrega")')
        page.wait_for_timeout(2356)

        print("Esperando campo de email...")
        page.wait_for_selector('input[placeholder="Micorreo@correo.com"]', timeout=4020)
        page.click('input[placeholder="Micorreo@correo.com"]')
        page.fill('input[placeholder="Micorreo@correo.com"]', "nitins22@gmail.com")
        page.click('button:has-text("Enviar")')
        page.wait_for_timeout(3000)

        print("Seleccionando 'Retirar en una tienda'...")
        page.click('.veaargentina-delivery-modal-1-x-deliveryInfo:has-text("Retirar en una tienda")')
        page.wait_for_timeout(2356)

        print(f"Seleccionando provincia: {provincia}...")
        page.locator('select[style="appearance: menulist-button;"]').first.select_option(label=provincia)
        page.wait_for_timeout(2356)

        print(f"Seleccionando tienda: {tienda}...")
        page.locator('select[style="appearance: menulist-button;"]').nth(1).select_option(label=tienda)
        page.wait_for_timeout(2356)

        print("Esperando botón 'Confirmar' habilitado...")
        confirm_button = page.locator('button:has-text("Confirmar")')
        for _ in range(30):  # Esperar hasta ~15 segundos
            if confirm_button.is_enabled():
                confirm_button.click()
                print("Botón 'Confirmar' presionado.")
                break
            time.sleep(0.5)
        else:
            print("Error: El botón no se habilitó después de 15 segundos.")

        print("Esperando 10 segundos para terminar de configurar la sucursal...")
        time.sleep(10)
        print("Sucursal configurada correctamente.")
    except Exception as e:
        print(f"Error durante la selección de sucursal: {e}")

##################################################
# 2. Funciones para extraer datos de la página
##################################################
def extraer_json(page):
    """
    Extrae el JSON embebido en el <script> de la página (body > div:nth-child(2) ...).
    Ajusta el selector si cambia la estructura del DOM.
    """
    try:
        script_tag = page.locator('//body/div[2]/div/div[1]/div/script').text_content()
        return json.loads(script_tag) if script_tag else {}
    except Exception as e:
        print(f"Error al extraer JSON: {e}")
        return {}

def extraer_texto_visible(page):
    """
    Retorna todo el texto visible del <body>.
    """
    try:
        return page.inner_text("body")
    except Exception as e:
        print(f"Error al extraer texto visible: {e}")
        return ""

def scrollear_pagina(page, veces=1, espera=5):
    """
    Realiza scroll en la página varias veces, con esperas entre cada scroll.
    """
    try:
        for i in range(veces):
            print(f"Realizando scroll {i+1}/{veces}...")
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            time.sleep(espera)
    except Exception as e:
        print(f"Error al scrollear la página: {e}")

##################################################
# 3. Función de scraping
#    Recorre páginas desde start_page hasta end_page
##################################################
def scrape_vea(page, category, start_page=1, end_page=1):
    """
    Pagina sobre la categoría y extrae JSON + texto de cada página.
    Además, toma capturas de pantalla de cada página procesada.
    """
    base_url = "https://www.vea.com.ar/"
    compiled_json = []
    compiled_text = []

    # Crear carpeta para capturas de pantalla si no existe
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)

    for page_num in range(start_page, end_page + 1):
        # Construir la URL de la categoría
        if page_num == 1:
            url = f"{base_url}{category}"
        else:
            url = f"{base_url}{category}?page={page_num}"

        print(f"Navegando a: {url}")
        page.goto(url)
        page.wait_for_load_state("networkidle")
        time.sleep(8)

        scrollear_pagina(page, veces=2, espera=1)
        page.reload()
        page.wait_for_load_state("load")
        time.sleep(8)

        # Extraer datos
        json_data = extraer_json(page)
        texto_visible = extraer_texto_visible(page)

        compiled_json.append(json_data)
        compiled_text.append(texto_visible)

        # Guardar captura de pantalla
        screenshot_path = os.path.join(screenshots_dir, f"{category}_page_{page_num}.png")
        page.screenshot(path=screenshot_path)
        print(f"Captura de pantalla guardada en: {screenshot_path}")

        print(f"Página {page_num} procesada con éxito.\n")

    return compiled_json, compiled_text

##################################################
# 4. main() - Ejecuta todo el flujo
##################################################
def main():
    provincia = "CORDOBA"
    tienda = "Vea Ciudad de Córdoba Av Juan B Justo"
    category = "bebidas"
    start_page = 1
    end_page = 32

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        print("Abriendo sitio de Vea...")
        page.goto("https://www.vea.com.ar/")
        page.wait_for_timeout(4000)

        seleccionar_sucursal(page, provincia, tienda)

        print(f"Iniciando scraping de la categoría: {category}")
        all_json, all_text = scrape_vea(page, category, start_page, end_page)

        with open("vea_datos.json", "w", encoding="utf-8") as jf:
            json.dump(all_json, jf, ensure_ascii=False, indent=4)
        print("Datos JSON guardados en: vea_datos.json")

        with open("vea_texto.txt", "w", encoding="utf-8") as tf:
            for texto in all_text:
                tf.write(texto)
                tf.write("\n\n" + ("-"*60) + "\n\n")
        print("Texto visible guardado en: vea_texto.txt")

        print("Cerrando navegador...")
        browser.close()
        print("Scraping finalizado.")

if __name__ == "__main__":
    main()
