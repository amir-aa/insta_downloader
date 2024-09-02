import instaloader
from flask import Flask,request,send_from_directory,send_file,jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import configparser,os
app = Flask(__name__)
conf=configparser.ConfigParser()
conf.read('config.ini')

DAYLIMIT=conf['settings']['limit_per_day']
HOURLIMIT=conf['settings']['limit_per_hour']
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[f"{DAYLIMIT} per day", f"{HOURLIMIT} per hour"],
    storage_uri="memory://",
)


L = instaloader.Instaloader(filename_pattern='{target}/{shortcode}_{profile}_{date:%Y-%m-%d}')
username = conf['settings']['instagram_user']
password = conf['settings']['instagram_pass']

L.context.log("Loading session from file...")
try:
    L.load_session_from_file(username)
except FileNotFoundError:
    L.context.log("Session file not found. Logging in...")
    L.login(username, password)
    L.save_session_to_file()

@app.route('/',methods=['POST'])
def insta():
    data=request.get_json()
    try:
        post_url= str(data['url'])  
        post=instaloader.Post.from_shortcode(L.context, post_url.split('/')[-2])

        L.download_post(post,target="downloads/")
        downloaded_filename=L.format_filename(post) + ".mp4"
        file_path=os.path.join("downloads/", downloaded_filename)
        if os.path.exists(file_path):
                return send_file(file_path,as_attachment=True,download_name=downloaded_filename)
        else:
                return jsonify({"error":"File not found"}),404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
