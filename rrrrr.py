from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import requests
import pandas as pd



def scrape_course_details(course_url):

    options = Options()
    options.add_argument("--headless")  


    driver = webdriver.Chrome(options=options)
    

    driver.get(course_url)

   
    # time.sleep(5)


    page_source = driver.page_source
    

    driver.quit()


    soup = BeautifulSoup(page_source, "html.parser")
    

    h1_tag = soup.find("h1", class_="titPage")
    if h1_tag:
        name = h1_tag.text.strip()
    else:
        name = "Name not found"
  
    mission_div = soup.find('div', text='MISSION')


    if mission_div:
        p_element = mission_div.find_next_sibling('div').find('p')
        if p_element:
            mission = p_element.text.strip()
        else:
            print("No adjacent p element found.")
    else:
        print("MISSION div not found.")

    # summary_div = soup.find('div', text='CONTENT SUMMARY')
    summary_div = soup.find('div', text=['CONTENT SUMMARY', 'PROGRAMMA SINTETICO', 'PROGRAMMA SINTETICO / CONTENT SUMMARY'])
    if summary_div:
        p_element = summary_div.find_next_sibling('div')
        p_elements = p_element.find_all('p') if p_element else []
        
        p_element2 = summary_div.find_next_sibling('div')
        p_elements2 = p_element2.find_all('li') if p_element2 else []
        
        combined_elements = [p.text for p in p_elements] + [li.text for li in p_elements2]
        
        summary = ' '.join(combined_elements).strip()
        
        if not summary:
            summary = 'not found'
    else:
        print("CONTENT SUMMARY div not found.")



    txt_blue_div = soup.find('div', text=['Intended Learning Outcomes (ILO)','Risultati di Apprendimento Attesi (RAA)','Risultati di Apprendimento Attesi (RAA) / Intended Learning Outcomes (ILO)'])
    if txt_blue_div:
        tit_blue_div = txt_blue_div.find_next_sibling()
        tit_blue_texts = []
        while tit_blue_div:
            tit_blue_texts.append(tit_blue_div.text)
            tit_blue_div = tit_blue_div.find_next_sibling()
        alio = ' '.join(tit_blue_texts)
    return name , mission , summary , alio

url = "https://didattica.unibocconi.eu/ts/tsn_ord_alf.php?anno=2023"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")
# print(soup.prettify())

course_links = soup.find_all("a")
data = []
blocked_data = []

base_url = "https://didattica.unibocconi.eu/ts/"
names_obtained = 0

try:
    existing_data_df = pd.read_csv('scraped_data.csv')
except FileNotFoundError:
    existing_data_df = pd.DataFrame()

# try:
#     existing_blocked_df = pd.read_csv('blocked_data.csv')
# except FileNotFoundError:
#     existing_blocked_df = pd.DataFrame()

data = existing_data_df.to_dict('records') if not existing_data_df.empty else []
# blocked_data = existing_blocked_df.to_dict('records') if not existing_blocked_df.empty else []

for link in course_links:
    course_url = link.get("href")
    if course_url and "tsn_anteprima" in course_url:
        full_url = base_url + course_url
        
        # Check if the URL is already in existing_data_df or existing_blocked_df
        if full_url in [item['Course URL'] for item in data] or full_url in [item['Blocked URL'] for item in blocked_data]:
            print(f"Skipping {full_url} as it already exists in the file.")
            continue
        
        try:
            name, mission, summary, alio = scrape_course_details(full_url)
            data.append({
                "Course URL": full_url,
                "Course Name": name,
                "Mission": mission,
                "Summary": summary,
                "ILO": alio
            })
            df = pd.DataFrame(data)
            df.to_csv('scraped_data.csv', index=False)
            print(f"Data for {full_url} has been scraped and saved to scraped_data.csv")
        except Exception as e:
            print(f"Error scraping data from {full_url}: {e}")
            blocked_data.append({
                "Blocked URL": full_url,
                "Error Message": str(e)
            })
            df_blocked = pd.DataFrame(blocked_data)
            df_blocked.to_csv('blocked_data.csv', index=False)
            print(f"Blocked URL {full_url} and error message saved to blocked_data.csv")

print("Scraping completed. Check scraped_data.csv and blocked_data.csv for results.")
