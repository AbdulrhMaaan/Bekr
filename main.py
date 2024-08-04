from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

def setup_webdriver():
    chrome_driver_path = r'/usr/local/bin/chromedriver'
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Ensure GUI is not required
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=5000')
    chrome_options.binary_location = r'/usr/bin/google-chrome'

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_amazon_prices_and_links(product_name):
    driver = setup_webdriver()
    amazon_url = f"https://www.amazon.sa/s?k={product_name.replace(' ', '+')}"
    driver.get(amazon_url)
    products = []

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.s-main-slot'))
        )
        product_elements = driver.find_elements(By.CSS_SELECTOR, '.s-main-slot .s-result-item')
        for product in product_elements:
            try:
                price = ''
                link = ''
                description = ''
                image = ''

                price_element = product.find_element(By.CSS_SELECTOR, '.a-price-whole')
                price = price_element.text if price_element else "No Price"
                symbol = 'ر س'

                description_element = product.find_element(By.CSS_SELECTOR, 'div[data-cy="title-recipe"] h2 a span.a-size-base-plus')
                description = description_element.text

                link_element = product.find_element(By.CSS_SELECTOR, '.a-link-normal.a-text-normal')
                link = link_element.get_attribute('href')

                image_element = product.find_element(By.CSS_SELECTOR, '.s-image')
                image = image_element.get_attribute('src')

                products.append((price, symbol, description, image, link))
            except Exception as e:
                logging.error(f"Error extracting product data from Amazon: {e}")
                continue
        return products[:3]
    except Exception as e:
        logging.error(f"Error loading Amazon page: {e}")
        return []
    finally:
        driver.quit()


@app.route('/leastpricelist', methods=['GET'])
def get_leastpricelist():
    product_name = request.args.get('product_name')
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400

    amazon_products = get_amazon_prices_and_links(product_name)
    #jarir_products = get_jarir_prices_and_links(product_name)
    #extra_products = get_extra_prices_and_links(product_name)
    #all_products = amazon_products + jarir_products + extra_products
    all_products = amazon_products

    products_with_float_prices = []
    for price, symbol, description, image, link in all_products:
        numeric_part = ''.join(filter(lambda x: x.isdigit() or x == '.', price))
        float_price = float(numeric_part) if numeric_part else float('inf')
        products_with_float_prices.append((float_price, symbol, description, image, link))

    sorted_products = sorted(products_with_float_prices, key=lambda x: x[0])
    sorted_products = [{"price": price, "symbol": symbol, "description": description, "image": image, "link": link} for price, symbol, description, image, link in sorted_products]

    return jsonify(sorted_products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
