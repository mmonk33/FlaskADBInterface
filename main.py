import os
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import subprocess
from flask_bootstrap import Bootstrap


UPLOAD_FOLDER = '/home/emil/DevicesFarm/apk/'
ALLOWED_EXTENSIONS = set(['apk'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bootstrap = Bootstrap(app)


@app.route('/adb/', methods=['post', 'get'])
def index():
    message = ''
    list3 = []
    list1 = subprocess.check_output(
        f'docker exec -i container-appium adb devices',
        shell=True)
    list1 = list1.decode()
    list1 = list1.replace("List of devices attached", "")
    list1 = list1.split()

    for i in range(0, len(list1), 2):
        list3.append((list1[i], list1[i + 1]))

    if request.method == 'POST':
        udid = request.form.get('udid')
        action = request.form.get('butt')
        if action == 'connect' or action == 'disconnect':
            if '192.168.2' in udid:
                message = subprocess.check_output(
                    f'docker exec -i container-appium adb {action} {udid}',
                    shell=True)
                message = message.decode()
    return render_template('index.html', devices=list3, message=message)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/install/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        udid = request.form['udid']
        file = request.files['file']
        if file and allowed_file(file.filename):
            file.save(os.path.join('/home/emil/DevicesFarm/apk/', secure_filename(file.filename)))
            print(subprocess.check_output(
                f'docker exec -i container-appium adb -s {udid} install -r -d /home/DevicesFarm/apk/{file.filename}',
                shell=True))
        return render_template('installed.html')