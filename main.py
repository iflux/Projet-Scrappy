import requests
from scrapy import Selector
import pandas as pd
import time
from urllib.parse import urljoin
import os

def scrape_book(url):
    response = requests.get(url)
    sel_book = Selector(text=response.text)
    title = sel_book.css("div.product_main h1::text").get()
    price = sel_book.css("p.price_color::text").get()
    stock_list_raw = sel_book.css("p.instock.availability::text").getall()
    stock = " ".join([s.strip() for s in stock_list_raw if s.strip()])
    rating = sel_book.css("p.star-rating").attrib.get("class")
    upc = sel_book.css("table.table.table-striped tr:nth-child(1) td::text").get()
    img_src = sel_book.css("div.item.active img::attr(src)").get()
    img_url = urljoin(url, img_src)
    return {
        "title": title,
        "price": price,
        "stock": stock,
        "rating": rating,
        "upc": upc,
        "image_url": img_url,
        "product_page": url
    }

def scrape_category(category_url, category_name):
    books_data = []
    page_number = 1
    while True:
        if page_number == 1:
            page_url = category_url
        else:
            page_url = category_url.replace("index.html", f"page-{page_number}.html")
        print(f"Catégorie {category_name} - Page {page_number}")
        response_categorie = requests.get(page_url)
        sel_categories = Selector(text=response_categorie.text)
        book_links = sel_categories.css("article.product_pod h3 a::attr(href)").getall()
        if not book_links:
            break
        book_urls = [urljoin(page_url, link) for link in book_links]
        print("Nombre de livres trouvés :", len(book_urls))
        for link in book_urls:
            data = scrape_book(link)
            books_data.append(data)
            print(f"Livre extrait : {data['title']}")
        page_number += 1
    os.makedirs("outputs/csv", exist_ok=True)
    df = pd.DataFrame(books_data)
    csv_name = f"outputs/csv/category_{category_name.lower().replace(' ', '_')}.csv"
    df.to_csv(csv_name, index=False)
    print("CSV enregistré :", csv_name)
    os.makedirs(f"outputs/images/{category_name.lower().replace(' ', '_')}", exist_ok=True)
    for b in books_data:
        image_url = b["image_url"]
        file_name = b["title"].replace(" ", "_") + ".jpg"
        file_path = f"outputs/images/{category_name.lower().replace(' ', '_')}/" + file_name
        r = requests.get(image_url)
        with open(file_path, "wb") as f:
            f.write(r.content)
        print("Image enregistrée :", file_path)

def scrape_all():
    url = "https://books.toscrape.com/"
    response = requests.get(url)
    sel = Selector(text=response.text)
    category_links = sel.css("div.side_categories ul li ul li a::attr(href)").getall()
    category_names = sel.css("div.side_categories ul li ul li a::text").getall()
    for i in range(len(category_links)):
        name = category_names[i].strip()
        link = category_links[i]
        category_url = urljoin(url, link)
        scrape_category(category_url, name)
