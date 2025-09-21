from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("Starting Construction Site Safety Monitoring Dashboard...")
    print("Connect your IP Webcam devices and configure them in the environment variables.")
    print("Access the dashboard at http://localhost:5000")
    
    # Start the Flask-SocketIO app
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 