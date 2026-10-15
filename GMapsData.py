"""Coleta nome, endereço, telefone e outros dados de estabelecimentos no Google Maps.

Uso:
    python GMapsData.py "restaurante maceió"
    python GMapsData.py "padaria recife" --max 50 --saida padarias.csv --headless
"""

import argparse
import csv
import re
import time
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FEED = 'div[role="feed"]'
# Link de cada resultado da lista. "a.hfpxzc" é a classe atual; o href é o fallback.
RESULT_LINK = 'a.hfpxzc, a[href*="/maps/place/"]'
# Mensagem exibida quando a lista termina ("Você chegou ao final da lista.").
END_OF_LIST = "span.HlvSq"

FIELDS = ["nome", "categoria", "endereco", "telefone", "site", "nota", "avaliacoes",
          "latitude", "longitude", "url"]


class GMapsData:

    def __init__(self, headless=False, timeout=15):
        options = webdriver.ChromeOptions()
        options.add_argument("--lang=pt-BR")
        options.add_argument("--window-size=1400,1000")
        if headless:
            options.add_argument("--headless=new")
        # O Selenium 4 baixa o chromedriver compatível sozinho (Selenium Manager).
        self.navegador = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.navegador, timeout)

    def close(self):
        self.navegador.quit()

    def accept_consent(self):
        """Aceita a tela de cookies, que aparece em alguns países/sessões novas."""
        if "consent." not in self.navegador.current_url:
            return
        for xpath in ('//button[.//span[contains(., "Aceitar tudo")]]',
                      '//button[.//span[contains(., "Accept all")]]',
                      '//form//button'):
            try:
                self.navegador.find_element(By.XPATH, xpath).click()
                self.wait.until(lambda d: "consent." not in d.current_url)
                return
            except (NoSuchElementException, TimeoutException):
                continue

    def collect_links(self, max_results):
        """Rola a lista lateral até o fim (ou até max_results) e devolve os links."""
        feed = self.navegador.find_element(By.CSS_SELECTOR, FEED)
        links = []
        stalled = 0
        while True:
            for a in feed.find_elements(By.CSS_SELECTOR, RESULT_LINK):
                href = a.get_attribute("href")
                if href and href not in links:
                    links.append(href)
            if max_results and len(links) >= max_results:
                return links[:max_results]
            if feed.find_elements(By.CSS_SELECTOR, END_OF_LIST):
                return links

            before = len(links)
            self.navegador.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(2)
            new_count = len(feed.find_elements(By.CSS_SELECTOR, RESULT_LINK))
            stalled = stalled + 1 if new_count <= before else 0
            if stalled >= 5:
                return links

    def _text(self, selector):
        try:
            return self.navegador.find_element(By.CSS_SELECTOR, selector).text.strip()
        except NoSuchElementException:
            return ""

    def _label(self, selector):
        """Lê o aria-label ("Endereço: Rua X, 10") e devolve só o valor."""
        try:
            label = self.navegador.find_element(By.CSS_SELECTOR, selector).get_attribute("aria-label") or ""
        except NoSuchElementException:
            return ""
        return label.split(":", 1)[1].strip() if ":" in label else label.strip()

    def get_name(self):
        return self._text("h1.DUwDvf") or self._text("h1")

    def get_category(self):
        return self._text("button.DkEaL")

    def get_address(self):
        return self._label('button[data-item-id="address"]')

    def get_phone(self):
        return self._label('button[data-item-id^="phone:tel:"]')

    def get_website(self):
        try:
            return self.navegador.find_element(
                By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute("href") or ""
        except NoSuchElementException:
            return ""

    def get_rating(self):
        summary = self._text("div.F7nice")
        rating = re.search(r"\d[.,]\d", summary)
        reviews = re.search(r"\(([\d.]+)\)", summary)
        return (rating.group(0) if rating else "",
                reviews.group(1).replace(".", "") if reviews else "")

    def get_place(self, url):
        self.navegador.get(url)
        self.wait.until(lambda d: d.find_elements(By.CSS_SELECTOR, "h1")
                        and d.find_element(By.CSS_SELECTOR, "h1").text.strip())
        time.sleep(1)  # endereço/telefone carregam logo depois do título
        return self.read_place()

    def read_place(self):
        url = self.navegador.current_url
        coords = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
        rating, reviews = self.get_rating()
        return {
            "nome": self.get_name(),
            "categoria": self.get_category(),
            "endereco": self.get_address(),
            "telefone": self.get_phone(),
            "site": self.get_website(),
            "nota": rating,
            "avaliacoes": reviews,
            "latitude": coords.group(1) if coords else "",
            "longitude": coords.group(2) if coords else "",
            "url": url,
        }

    def scrape(self, url, max_results=0):
        self.navegador.get(url)
        self.accept_consent()
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, FEED)))
        except TimeoutException:
            # Busca com um único resultado abre direto a página do lugar.
            if self.navegador.find_elements(By.CSS_SELECTOR, "h1"):
                return [self.read_place()]
            raise

        links = self.collect_links(max_results)
        print(f"{len(links)} resultados encontrados")
        places = []
        for i, link in enumerate(links, 1):
            try:
                place = self.get_place(link)
            except TimeoutException:
                print(f"[{i}/{len(links)}] não carregou: {link}")
                continue
            print(f"[{i}/{len(links)}] {place['nome']} | {place['telefone']}")
            places.append(place)
        return places


def search_url(term):
    return "https://www.google.com.br/maps/search/" + quote_plus(term) + "/?hl=pt-BR"


def save_csv(places, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(places)


def main():
    parser = argparse.ArgumentParser(description="Coleta dados de estabelecimentos no Google Maps.")
    parser.add_argument("termo", nargs="?", default="restaurante maceió", help='ex.: "restaurante maceió"')
    parser.add_argument("--max", type=int, default=0, help="limite de resultados (0 = todos)")
    parser.add_argument("--saida", default="resultados.csv", help="arquivo CSV de saída")
    parser.add_argument("--headless", action="store_true", help="roda sem abrir a janela do Chrome")
    args = parser.parse_args()

    scraper = GMapsData(headless=args.headless)
    try:
        places = scraper.scrape(search_url(args.termo), args.max)
    finally:
        scraper.close()
    save_csv(places, args.saida)
    print(f"{len(places)} registros salvos em {args.saida}")


if __name__ == "__main__":
    main()
