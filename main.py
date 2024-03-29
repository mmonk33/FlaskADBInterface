import os
from transliterate import translit
from flask import Flask, request, render_template, redirect
from werkzeug.utils import secure_filename
import subprocess
import pythonping
from flask_bootstrap import Bootstrap

UPLOAD_FOLDER = '/home/emil/DevicesFarm/apk/'
ALLOWED_EXTENSIONS = {'apk'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bootstrap = Bootstrap(app)


def sp_adb_devices():
    adb_devices = []
    subp_output = subprocess.check_output(
        f'docker exec -i container-appium adb devices',
        shell=True)
    subp_output = subp_output.decode()
    subp_output = subp_output.replace("List of devices attached", "")
    subp_output = subp_output.split()
    for i in range(0, len(subp_output), 2):
        subp_output[i] = subp_output[i].replace(':5555', '')
        if subp_output[i + 1] == 'device':
            if pythonping.ping(subp_output[i], count=3, verbose=False).success():
                build_version = subprocess.check_output(
                    f'docker exec -i container-appium adb -s {subp_output[i]} shell getprop ro.build.display.id',
                    shell=True).decode()
                adb_devices.append((subp_output[i], subp_output[i + 1], build_version))
            else:
                adb_devices.append((subp_output[i], subp_output[i + 1], ''))
        else:
            adb_devices.append((subp_output[i], subp_output[i + 1]))
    return adb_devices


@app.route('/')
@app.route('/adb/', methods=['POST', 'GET'])
def index():
    message = ''
    adb_devices = sp_adb_devices()
    if request.method == 'POST':
        udid = request.form.get('udid')
        action = request.form.get('butt')
        if action == 'connect':
            if '192.168.2' in udid:
                message = subprocess.check_output(
                    f'docker exec -i container-appium adb {action} {udid}',
                    shell=True).decode()
                adb_devices = sp_adb_devices()
        elif action == 'disconnect':
            for i in adb_devices:
                if udid in i:
                    message = subprocess.check_output(
                        f'docker exec -i container-appium adb {action} {udid}',
                        shell=True).decode()
                    adb_devices = sp_adb_devices()
    return render_template('index.html', devices=adb_devices, message=message)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/install/', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        udid = request.form['udid']
        file = request.files['file']
        file.filename = file.filename.replace(' ', '_')
        file.filename = translit(file.filename, language_code='ru', reversed=True)
        if file.filename != '':
            if file and allowed_file(file.filename):
                file.save(os.path.join(UPLOAD_FOLDER, secure_filename(file.filename)))
                subprocess.check_output(
                    f'docker exec -i container-appium adb -s {udid} install -r -d \"/home/DevicesFarm/apk/{file.filename}\"',
                    shell=True)
                return render_template('installed.html')
            adb_devices = sp_adb_devices()
            return render_template('index.html', devices=adb_devices, message='Not allowed file extension!')
        else:
            adb_devices = sp_adb_devices()
            return render_template('index.html', devices=adb_devices, message='File is not selected')


@app.route('/', methods=['POST', 'GET'])
def shell():
    if request.method == 'POST':
        udid = request.form['udid']
        shell_command = request.form['shell']
        if shell_command is not '':
            try:
                message = subprocess.check_output(
                    f'docker exec -i container-appium adb -s {udid} shell {shell_command}', shell=True).decode()
            except:
                message = 'Uncorrect shell command'
        else:
            message = 'Empty request'
        adb_devices = sp_adb_devices()
        return render_template('index.html', message=message, devices=adb_devices)


@app.route('/remote/<string:udid>/', methods=['POST', 'GET'])
def remote(udid):
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            subprocess.check_output(
                f'docker exec -i container-appium adb -s {udid} shell input keyevent {action}',
                shell=True)
            subprocess.check_output(
                f'docker exec -i container-appium adb -s {udid} exec-out screencap -p > '
                f'/home/emil/DevicesFarm/static/{udid}_screen.png',
                shell=True)
        elif request.method == 'GET':
            subprocess.check_output(
                f'docker exec -i container-appium adb -s {udid} exec-out screencap -p > '
                f'/home/emil/DevicesFarm/static/{udid}_screen.png',
                shell=True)
    except:
        return redirect('../../')
    return render_template('remote.html', udid=udid)

