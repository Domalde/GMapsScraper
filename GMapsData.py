from selenium import webdriver
from selenium.webdriver.common.by import By
import time

class GMapsData:
      
    def __init__(self):
        self.navegador = webdriver.Chrome()

    def next_page(self):
        self.navegador.find_element(By.XPATH, '/html/body/div[3]/div[9]/div[3]/div[1]/div[1]/div[1]/div[1]/button').click()
        time.sleep(5)
        self.navegador.find_element(By.XPATH, '/html/body/div[3]/div[9]/div[8]/div/div[1]/div/div/div[2]/div[2]/div/div[1]/div/button[2]').click()
        time.sleep(5)
        try:
            self.scroll_page()
        except:
            print("The end")

    def scroll_page(self):
        for i in range(1,24):
            if i == 1:
                self.navegador.find_element(By.XPATH, '//*[@id="pane"]/div/div[1]/div/div/div[2]/div[1]/div[3]/div/a').click()
                time.sleep(1)
                name = self.get_name()
                time.sleep(1)
                address = self.get_address()
                time.sleep(1)
                tel = self.get_phone()
                # TODO: Registrar em uma planilha
            else:
                try:
                    self.navegador.find_element(By.XPATH, f'/html/body/div[3]/div[9]/div[23]/div[2]/div/div[1]/div/div[1]/div/div/div/div[2]/div[2]/div[{i}]').click()
                    time.sleep(1)
                    name = self.get_name()
                    time.sleep(1)
                    address = self.get_address()
                    time.sleep(1)
                    tel = self.get_phone()
                    # TODO: Registrar em uma planilha
                except:
                    self.next_page()

    def get_name(self):
        try:
            return self.navegador.find_element(By.XPATH, "//h1[contains(@class,'header-title')]").text
        except:
            return ""

    def get_address(self):
        try:
            return self.navegador.find_element(By.CSS_SELECTOR, "[data-item-id='address']").text
        except:
            return ""
    
    def get_phone(self):
        try:
            return self.navegador.find_element(By.CSS_SELECTOR, "[data-tooltip='Copiar número de telefone']").text
        except:
            return ""

    def scrape(self, url):
        self.navegador.get(url)
        self.scroll_page()

term = "restaurante maceió"
url = "https://www.google.com.br/maps/search/"+term.replace(" ", "+")+"/"
GMapsData().scrape(url)