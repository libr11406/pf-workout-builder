from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
from flask import Flask, request, jsonify
from generator import generate_workout
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

def get_selenium_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

@app.route('/generate_workout', methods=['GET'])
def api_generate():
    mins = int(request.args.get('mins', 45))
    crowd = int(request.args.get('crowd', 50))
    muscle = request.args.get('muscle', 'All')

    workout_plan, total_time = generate_workout(mins, crowd, muscle)
    return jsonify({
        'workout_plan': workout_plan,
        'total_time_mins': round(total_time / 60, 1)
    })

@app.route('/search_clubs', methods = ['GET'])
def search_clubs():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    driver = get_selenium_driver() # chrome_options.add_argument("--headless=new")
    try:
        driver.get("https://www.planetfitness.com/gyms")
        wait = WebDriverWait(driver, 15)
        search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder='City, State or Zip'], input[type='text']")))
        search_box.clear()
        search_box.send_keys(query)

        search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .search-icon, .btn-search")
        search_button.click()
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='club-card'], .gym-search-results")))
        clubs = driver.find_elements(By.CSS_SELECTOR, "div[class*='club-card']")
        formatted_clubs = []
        for club in clubs[:10]:
            try:
                name = club.find_element(By.CSS_SELECTOR, "h3, .club-name").text
                link = club.find_element(By.TAG_NAME, "a").get_attribute("href")
                slug = link.strip("/").split("/")[-1]
                formatted_clubs.append({"id": slug, "name": name})
            except:
                continue
        return jsonify(formatted_clubs)
    except Exception as e:
        print(f"Selenium Search Error: {e}")
        return jsonify({'error': 'The gym website blocked the search. Please wait a moment or try a different zip code.'}), 500
    finally:
        driver.quit()
@app.route('/get_crowd', methods=['GET'])
def get_crowd():
    club_id = request.args.get('club_id', 'perry-hall-md')
    if not club_id:
        return jsonify({'crowd': 50, 'error': 'No club selected'})
    driver = get_selenium_driver()
    
    try:
        crowd_val = get_historical_occupancy()
        import random
        crowd_val += random.randint(-3, 3)
        crowd_val = max(5, min(95, crowd_val))

        return jsonify({'crowd': crowd_val, 'status': 'Historical data used', 'location': club_id, 'timestamp': datetime.now().strftime("%I:%M %p")})
    except Exception as e:
        print(f"Error calculating crowd: {e}")
        return jsonify({'crowd': 50, 'error': 'Could not retrieve crowd data'})
def get_historical_occupancy():
    hour = datetime.now().hour
    occupancy_map = {
        0:5, 1:2, 2:2, 3:5, 4:10,
        5:25, 6:45, 7:60, 8:55, 9:40,
        10:35, 11:30, 12:35, 13:40, 14:45,
        15:55, 16:70, 17:85, 18:90, 19:75,
        20:60, 21:40, 22:25, 23:15
    }
    return occupancy_map.get(hour, 50)
if __name__ == '__main__':
    app.run(debug=True, port=5000)