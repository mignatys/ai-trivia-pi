from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO
import threading
import time
import socket
from logger import log
from . import network_manager as net
from config import WEB_PORT

app = Flask(__name__)
app.secret_key = 'pi_trivia_secret_key'
socketio = SocketIO(app, async_mode='threading')

game_is_ready = False

@app.route('/')
def index():
    if not net.is_connected():
        return redirect(url_for('setup'))
    if game_is_ready:
        return render_template('index.html')
    else:
        return render_template('loading.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        if not ssid or not password:
            flash('SSID and password cannot be empty.', 'error')
            return redirect(url_for('setup'))
        log.info(f"Received network credentials for SSID: {ssid}")
        if net.connect_to_wifi(ssid, password):
            flash('Successfully connected to WiFi!', 'success')
            time.sleep(5)
            hostname = socket.gethostname()
            return f"<h1>Connection Successful!</h1><p>Please connect your computer back to your main WiFi network and access the device at <a href='http://{hostname}.local:{WEB_PORT}'>http://{hostname}.local:{WEB_PORT}</a> or its new IP address.</p>"
        else:
            flash('Failed to connect. Please check your credentials and try again.', 'error')
            net.start_hotspot()
            return redirect(url_for('setup'))
    
    current_ssid = net.get_current_ssid()
    return render_template('setup.html', current_ssid=current_ssid)

def run_web_server():
    log.info(f"Starting Flask-SocketIO web server on port {WEB_PORT}...")
    socketio.run(app, host='0.0.0.0', port=WEB_PORT, debug=False, allow_unsafe_werkzeug=True)

def start_in_thread():
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

def set_game_ready_status(is_ready):
    global game_is_ready
    log.info(f"Web UI game_ready status set to: {is_ready}")
    game_is_ready = is_ready
    if is_ready:
        socketio.emit('game_ready')

def emit_game_update(data):
    """Emits a game state update to all connected clients."""
    socketio.emit('game_update', data)
