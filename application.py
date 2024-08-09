from flask import Flask, Response, render_template, flash, redirect, request
import pandas as pd
import threading
import csv
import scrape_cookies2
import io
#import logging
import os
#3.11.9 (main, Apr  2 2024, 08:25:04) [Clang 15.0.0 (clang-1500.3.9.4)]
application = Flask(__name__)
application.secret_key = os.urandom(12)
results = []
'''
# Configure logging
logging.basicConfig(
    filename='/tmp/flask_app.log',  # Log file path
    level=logging.DEBUG,  # Log level
    format='%(asctime)s %(levelname)s: %(message)s'
)
'''
@application.route('/')
def index():
    return render_template('index.html')  #form page

@application.route('/submit', methods=['POST']) #gets form information and run scrape.py
def submit():
    cookies = request.form['cookies']
    #password = request.form['password']
    api_key = request.form['api_key']
    #urls = request.form['urls'].split(",")  #POSSIBLE CHANGE TO CSV INPUT
    #urls = [url.strip() for url in urls]

    file = request.files['url_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file:
        # Read the CSV file directly into a DataFrame
        urls_df = pd.read_csv(file)
        print(urls_df)
        urls = urls_df.iloc[:,0].tolist()  # Assumes URLs are in the first column
        print(urls)

    #logging.debug("urls:", urls)
    thread = threading.Thread(target=run_scraper, args=(cookies, api_key, urls))
    thread.start()

    return render_template('progress.html') 

def run_scraper(cookies, api_key, urls):
    global results, is_scraping_complete
    is_scraping_complete = False
    results = scrape_cookies2.process_profiles(cookies, urls, api_key) #from scrape.py
    #logging.debug("results", results)
    #print("Scraping complete, data is ready for download.")
    is_scraping_complete = True

@application.route('/download') #writes output from scrape.py to CSV
def download():
    global results 
    f = io.StringIO()

    if results: 
        writer = csv.DictWriter(f, fieldnames=['URL', 'School(s)', 'Age', 'Veteran', 'Mutual Connections', 'Notes']) #columns for now
        writer.writeheader()
        writer.writerows(results)  

        output = io.BytesIO()
        output.write(f.getvalue().encode())
        output.seek(0)
        #output = f.getvalue()
        f.close()

        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=output.csv"})
    else:
        return "No data available for download.", 404

@application.route('/status') #displays progress and download when ready
def status():
    global is_scraping_complete
    if is_scraping_complete:
        return {"status": "completed",
                "current": scrape_cookies2.progress['current'], #pull what profile we're on from scrape.py "progress" variable
                "total": scrape_cookies2.progress['total']
                }, 200
    else:
        return {"status": "in_progress",
                "current": scrape_cookies2.progress['current'],
                "total": scrape_cookies2.progress['total']
                }, 202


if __name__ == '__main__':
    application.run(debug=True)
