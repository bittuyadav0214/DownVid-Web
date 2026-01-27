from flask import Flask
from flask import url_for
from flask import request
from flask import Response
from flask import render_template
from flask import redirect
from flask import stream_with_context
from flask import send_from_directory
from assets.validator import url_validation
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import os
import json
import uuid
import time
import random
import threading
import requests
import glob
import logging

app = Flask(__name__)

limiter = Limiter(
   get_remote_address,
   app = app,
   default_limits=["551 per days","101 per 5 minute"]
)

logging.basicConfig(
  filename = "abuse.log",
  level = logging.WARNING,
  format = "%(asctime)s | %(message)s"
)


jobs = {}
delays = [1,0.5,2,1.5,1.8,0.8]


def downloader(job_id):
    if job_id not in jobs:
        return ""
    try:
        jobs[job_id]["status"]="Accessing URL"        
        time.sleep(random.choice(delays))
        url = jobs[job_id]["preurl"]
        jobs[job_id]["status"]="Accessing format"
        jobs[job_id]["url"] = url
        time.sleep(random.choice(delays)) 
        format = jobs[job_id]["preformat"]
        jobs[job_id]["status"] = "Checking validity"
        jobs[job_id]["format"] = format
        valid_code = url_validation(url)
        if str(valid_code) == '200':
            jobs[job_id]["status"] = "Accessing title"
            jobs[job_id]["validity"] = "True"
        else:
            jobs[job_id]["status"] = "Failed❌"
            jobs[job_id]["validity"] = "False"
            time.sleep(60)
            raise Exception("Url not valid")
        title = os.popen(f"yt-dlp --get-title {url}").read().strip()
        if title :
            jobs[job_id]["status"] = "Downloading"
            jobs[job_id]["title"] = title
        else:
            jobs[job_id]["status"] = "Failed❌"
            jobs[job_id]["title"] = "Not Found"
            time.sleep(60)
            raise Exception("title no found")
            
        download = os.popen(f"python assets/downloader2.py --link {url} --format {format} --JobId {job_id}").read().strip().split('\n')
        if download[-1].strip() == "success":
            jobs[job_id]["status"] = "Complete✅"
         
            time.sleep(600)
            files = glob.glob(f"assets/downloads/{job_id}.*")
            for file in files:
                try:
                    if file:
                        os.remove(file)
                except Exception as e:
                    pass
        else:
            jobs[job_id]["status"] = "Failed❌" 
            time.sleep(30)
    except Exception:
        pass
    finally :
        jobs.pop(job_id,None)    
    
    
    
     
    
    
    
@app.route('/',methods=["GET"])
def home():
    return render_template('index.html')
    
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')    
    
@app.route('/report')
def report():
    return render_template('report.html')          
    
@app.route('/processing',methods=["POST"])
def processing():
    if request.method == "POST":
        url = request.form.get('url')
        format = request.form.get('format')
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
        "preurl" : url,
        "preformat" : format,
        "url" : None,
        "format" : None,
        "validity" : None,
        "status" : "Please wait",
        "title" : None
        }
        threading.Thread(target=downloader,args=(job_id,),daemon=True).start()
        return f"{json.dumps({'job_id':job_id})}"
        
                      
             
@app.route('/process/status/<job_id>',methods=["GET","POST"])
def status(job_id):
   if job_id not in jobs:
       return redirect(url_for('home'))
   return render_template('processing.html',uid = job_id)
   
   
@app.route('/process/stream/<job_id>',methods=["GET","POST"])   
def stream(job_id):
    def streaming():
       while job_id not in jobs:
           time.sleep(0.2)
       while True:
           if job_id not in jobs:
               break
           yield f"data:{json.dumps(jobs[job_id])}\n\n"
           if jobs[job_id]["status"] == "Complete✅":
               break
           time.sleep(1)
    return Response(stream_with_context(streaming()),mimetype="text/event-stream")
       

@app.route("/content/preview/<job_id>")
def preview(job_id):
    job = jobs.get(job_id)
    if not job:
        return "Job expired", 404

    title = job.get("title")
    format = job.get("format")

    if not title or not format:
        return "File not ready", 404

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(BASE_DIR, "assets","downloads")
    print("Base dir :",BASE_DIR)
    print("Down d :",download_dir)

    if format == "video":
        filename = job_id + ".mp4"
    elif format == "audio":
        filename = job_id + ".mp3"
    else:
        return "Unsupported format", 400

    file_path = os.path.join(download_dir, filename)
    print("File :",file_path)
    if not os.path.exists(file_path):
        return f'File not found on server: {filename}', 404

    return send_from_directory(download_dir, filename, as_attachment=False)

    return "File not found", 404
            
@app.route('/content/download/<job_id>')
def download(job_id):
    job = jobs.get(job_id)
    if not job:
        return "Job expired", 404

    title = job.get("title")
    format = job.get("format")

    if not title or not format:
        return "File not ready", 404

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(BASE_DIR, "assets","downloads")

    if format == "video":
        filename = job_id + ".mp4"
        title = title+".mp4"
    elif format == "audio":
        filename = job_id + ".mp3"
        title = title+".mp3"
    else:
        return "Unsupported format", 400

    file_path = os.path.join(download_dir, filename)

    if not os.path.exists(file_path):
        return f'File not found on server: {filename}', 404

    return send_from_directory(download_dir, filename, as_attachment=True,download_name=title)

    return "File not found", 404    
    
    
@app.errorhandler(404)
def err_404(error):
    return render_template("error-404.html") ,404  
    
     
@app.errorhandler(500)
def err_500(e):
    return render_template("error-500.html") ,500
        
        

@app.route('/debuglog',methods=["GET","POST"])
@limiter.limit("10 per hour")
def debuglog():
    if request.method == "POST":
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        if username == os.environ.get("USERNAME") and password == os.environ.get("PASSWORD"):
           with open("assets/debug.txt","r") as logfile:
               logs = logfile.readlines()
               return logs      
        else:
           return Response("Invalid Credentials"),403
    return render_template('logauth.html')

                      
@app.route('/abuselog',methods=["GET","POST"])
@limiter.limit("10 per hour")
def abuselog():
    if request.method == "POST":
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        if username == "bittuyadav0214" and password == "bittuyadav0214!!(^°^)" :
           with open("abuse.log","r") as logfile:
               logs = logfile.readlines()
               return logs      
        else:
           return Response("Invalid Credentials"),403
    return render_template('logauth.html')
    
    
@app.errorhandler(RateLimitExceeded)
def block_ip(e):
           ip = request.remote_addr
           path = request.path
           ua = request.headers.get("User-Agent")
           logging.warning(f"IP : {ip} | PATH : {path} | UA : {ua} | LIMIT EXCEEDED")
           return render_template("limiter.html"),429  
           
if __name__ == "__main__":
    app.run(
    host = "0.0.0.0",
    port = 5000,
    debug = True
    )  
