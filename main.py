import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import subprocess
from flask_bootstrap import Bootstrap

UPLOAD_FOLDER = '/home/emil/DevicesFarm/apk/'
ALLOWED_EXTENSIONS = {'apk'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bootstrap = Bootstrap(app)


def sp_adb_devces():
    adb_devices = []
    subp_output = subprocess.check_output(
        f'docker exec -i container-appium adb devices',
        shell=True)
    subp_output = subp_output.decode()
    subp_output = subp_output.replace("List of devices attached", "")
    subp_output = subp_output.split()
    for i in range(0, len(subp_output), 2):
        if subp_output[i + 1] == 'device':

            build_version = subprocess.check_output(
                f'docker exec -i container-appium adb -s {subp_output[i]} shell getprop ro.build.display.id',
                shell=True).decode()
            adb_devices.append((subp_output[i], subp_output[i + 1], build_version))

    return adb_devices


@app.route('/')
@app.route('/adb/', methods=['POST', 'GET'])
def index():
    message = ''
    adb_devices = sp_adb_devces()
    if request.method == 'POST':
        udid = request.form.get('udid')
        action = request.form.get('butt')
        if action == 'connect' or action == 'disconnect':
            if '192.168.2' in udid:
                message = subprocess.check_output(
                    f'docker exec -i container-appium adb {action} {udid}',
                    shell=True).decode()
    return render_template('index.html', devices=adb_devices, message=message)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/install/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        udid = request.form['udid']
        file = request.files['file']
        if file and allowed_file(file.filename):
            file.save(os.path.join(UPLOAD_FOLDER, secure_filename(file.filename)))
            subprocess.check_output(
                f'docker exec -i container-appium adb -s {udid} install -r -d /home/DevicesFarm/apk/{file.filename}',
                shell=True)
        return render_template('installed.html')


@app.route('/', methods=['POST'])
def shell():
    if request.method == 'POST':
        udid = request.form['udid']
        shell_command = request.form['shell']
        message = subprocess.check_output(f'docker exec -i container-appium adb -s {udid} shell {shell_command}', shell=True).decode()
        adb_devices = sp_adb_devces()
        return render_template('index.html', message=message, devices=adb_devices)
