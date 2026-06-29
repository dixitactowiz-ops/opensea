import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

driver.get("https://sandbox.oxylabs.io/products?page=1")

total_pages = 1 

try:

    max_page_xpath = "//ul[contains(@class, 'pagination')]//a[max(text())] | //div[contains(@id, 'pagination')]//a[last()]"
    
   
    pagination_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'page=')]"))
    )
    

    page_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'page=')]")
    page_numbers = []
    
    for elem in page_elements:
        text = elem.text.strip()
        if text.isdigit():
            page_numbers.append(int(text))
            
    if page_numbers:
        total_pages = max(page_numbers)
        print(f" Dynamically discovered total pages: {total_pages}")

except Exception as e:
    print("Could not detect total pages dynamically, defaulting to 5 pages. Error:", e)
    total_pages = 5


for page_number in range(1, total_pages + 1):
    print(f"--- Processing Page {page_number} / {total_pages} ---")
    
    url = f"https://sandbox.oxylabs.io/products?page={page_number}"
    driver.get(url)
    
    try:
        product_xpath = "//div[contains(@class,'products-wrapper')]//h4[contains(@class,'title')]"
        elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, product_xpath))
        )
        
        print(f"Found {len(elements)} products on Page {page_number}")
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Error loading page {page_number}:", e)
        break

driver.quit()



# import scrapy
# import json
# import os  # Added to ensure directory paths are handled correctly

# class OpensImageSpider(scrapy.Spider):
#     name = "opens_image"
#     allowed_domains = ["opensea.io"]

#     def start_requests(self):
#         url = "https://opensea.io/collection/ok-guy"
        
#         headers = {
#             'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#             'accept-language': 'en-US,en;q=0.9',
#             'cache-control': 'no-cache',
#             'pragma': 'no-cache',
#             'priority': 'u=0, i',
#             'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
#             'sec-ch-ua-mobile': '?0',
#             'sec-ch-ua-platform': '"Windows"',
#             'sec-fetch-dest': 'document',
#             'sec-fetch-mode': 'navigate',
#             'sec-fetch-site': 'same-origin',
#             'sec-fetch-user': '?1',
#             'upgrade-insecure-requests': '1',
#             'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
#             'cookie': 'os_privacy=%7B%22mode%22%3A%22notice%22%7D; os2AccessEx=Wdr6yywSUvHzIWYeBybn17MOdxKRbbhM; _ga=GA1.1.1459581578.1782453780; AMP_MKTG_f404321ce8=JTdCJTdE; AMP_f404321ce8=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI4MjE4ZTU1My04YTNkLTRjNmYtYjBhNC1hODE2Y2FhYWQyNjElMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzgyNDUzNzgwMTUwJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc4MjQ1NDM1MDcxOSUyQyUyMmxhc3RFdmVudElkJTIyJTNBOCUyQyUyMnBhZ2VDb3VudGVyJTIyJTNBNCUyQyUyMmNvb2tpZURvbWFpbiUyMiUzQSUyMi5vcGVuc2VhLmlvJTIyJTdE; _ga_3H5P1H8T7W=GS2.1.s1782453780$o1$g1$t1782454351$j58$l0$h0; _dd_s=aid=69ce0495-4b39-4bfb-9ce4-2e0545677f61&rum=0&expire=1782455551357; __cf_bm=k_GU0nZu2gvpjprRgf3Vr_e6BcxFyAagTdvuG6xr4GY-1782454651.4869106-1.0.1.1-a8XHLeNmMi.wvtU0eOOE59aOWCNyKFhvJXGdj_SJDPZXbAFtaQmd4vm2YkZ1sI8lVF4PgUcagQ0x0tms1fnxeMct3Zz.4eDjxGSuob97u4zKQRdW8WDOzc3cFFgI.H8x',
#         }

      
#         yield scrapy.Request(
#             url=url,
#             method="GET",
#             headers=headers,
#             callback=self.parse
#         )


#     def parse(self, response):
#         self.log(f"Fetched HTML Page Status: {response.status}")

#         title = response.xpath("//span[contains(@class,'leading-normal')]/text()").get()

#         folder_path = r"D:\pagesave\image"

#         os.makedirs(folder_path, exist_ok=True)

#         file_name = "opensea_collection.html"
#         full_file_path = os.path.join(folder_path, file_name)

#         with open(full_file_path, "wb") as f:
#             f.write(response.body)

#         self.log(f"Successfully saved page to: {full_file_path}")

#         yield {
#             "title": title,
#             "status": response.status,
#         }