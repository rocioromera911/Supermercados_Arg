import json
import asyncio
import re
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from PIL import Image
from fpdf import FPDF

# Directorio donde se guardarán las capturas de pantalla
SCREENSHOT_DIR = "screenshots"
PDF_FILENAME = "paginas_scrapeadas.pdf"

# Crear directorio si no existe
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def auto_scroll(page):
    await page.evaluate(""" 
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    const scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if (totalHeight >= scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }
    """)

async def download_html(total_pages):
    base_url = "https://www.dinoonline.com.ar/super/categoria/supermami-almacen/_/N-1tjm8rd"
    #https://www.dinoonline.com.ar/super/categoria/supermami-bebidas/_/N-1500t13

    Nrpp = 36  # Productos por página

    urls = [f"{base_url}?Nf=product.endDate%7CGTEQ+1.7381088E12%7C%7Cproduct.startDate%7CLTEQ+1.7381088E12%7C%7C&No={i * Nrpp}&Nrpp={Nrpp}" 
            for i in range(total_pages)]
    
    print(f"Iniciando descarga de datos para {total_pages} páginas...")

    all_json_data = []
    all_body_text = []
    all_script_text = []
    screenshots = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for i, url in enumerate(urls):
            try:
                print(f"Descargando página: {url}")
                await page.goto(url, wait_until="networkidle")
                await auto_scroll(page)

                page_content = await page.content()

                # Extraer JSON
                json_data = None
                try:
                    json_match = re.search(r'var dataLayer = (\[.*?\]);', page_content, re.DOTALL)
                    if json_match:
                        json_data = json.loads(json_match.group(1))
                        all_json_data.extend(json_data)
                except Exception as e:
                    print(f"Error al extraer JSON: {e}")

                # Extraer contenido de la página
                soup = BeautifulSoup(page_content, 'html.parser')
                
                # 1. Texto de productos
                product_section = soup.select_one('#categoryLandingPage > div.col-lg-8.col-md-7.col-sm-12 > div.row.categoryProduct.xsResponse.clearfix')
                if product_section:
                    body_text = product_section.get_text(strip=True)
                    all_body_text.append(body_text)

                # 2. Texto del script especificado
                script_content = soup.select_one('#categoryLandingPage > div.col-lg-8.col-md-7.col-sm-12 > script')
                if script_content:
                    script_text = script_content.get_text(strip=True)
                    all_script_text.append(script_text)

                # Capturar captura de pantalla
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"pagina_{i+1}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                screenshots.append(screenshot_path)
                print(f"Captura de pantalla guardada: {screenshot_path}")

            except Exception as e:
                print(f"Error en la página {url}: {e}")
            
        await browser.close()

        # Guardar datos
        if all_json_data:
            with open("json_data.json", "w", encoding="utf-8") as json_file:
                json.dump(all_json_data, json_file, ensure_ascii=False, indent=4)
            print("Datos JSON guardados en 'json_data.json'.")

        if all_body_text:
            with open("body_text_im.txt", "w", encoding="utf-8") as text_file:
                text_file.write("\n".join(all_body_text))
            print("Texto de productos guardado en 'body_text.txt'.")

        if all_script_text:
            with open("script_text_im.txt", "w", encoding="utf-8") as script_file:
                script_file.write("\n".join(all_script_text))
            print("Texto del script guardado en 'script_text.txt'.")

        # Crear PDF con las capturas de pantalla
        if screenshots:
            create_pdf(screenshots)

    print("Descarga completada.")

def create_pdf(image_paths):
    """Genera un PDF con las imágenes de las capturas de pantalla."""
    pdf = FPDF()
    
    for image_path in image_paths:
        img = Image.open(image_path)
        img_width, img_height = img.size

        # Convertir tamaño a milímetros (1 px ≈ 0.264 mm)
        width_mm = img_width * 0.264
        height_mm = img_height * 0.264

        # Añadir nueva página (A4 por defecto)
        pdf.add_page()

        # Ajustar imagen para que quepa en la página
        pdf.image(image_path, x=10, y=10, w=180)  # Ancho de imagen ajustado a 180 mm

    pdf.output(PDF_FILENAME, "F")
    print(f"PDF generado: {PDF_FILENAME}")

if __name__ == "__main__":
    total_pages = int(input("¿Cuántas páginas deseas procesar? "))
    asyncio.run(download_html(total_pages))
