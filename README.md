# Construction Site Safety Monitoring Dashboard

A real-time monitoring system for construction sites that integrates multiple IP webcam feeds with computer vision models to detect safety gear violations and proximity to heavy machinery.

## Features

- Real-time monitoring of 4 construction site cameras
- Safety gear detection (helmets, vests, etc.)
- Proximity detection between workers and heavy machinery
- Alert system for safety violations
- Dashboard with statistics and historical alerts
- Configurable settings for detection sensitivity

## Requirements

- Python 3.7+
- IP Webcam app on Android devices (or other compatible IP cameras)
- Network connection between cameras and monitoring computer

## Installation

1. Clone this repository:
```
git clone <repository-url>
cd construction-site-monitoring
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure your camera URLs:
Edit the `.env` file and replace the default URLs with your actual IP Webcam URLs:
```
CAMERA_0_URL=http://your-camera-ip-1:8080/video
CAMERA_1_URL=http://your-camera-ip-2:8080/video
CAMERA_2_URL=http://your-camera-ip-3:8080/video
CAMERA_3_URL=http://your-camera-ip-3:8080/video
```

## Usage

1. Start the IP Webcam app on your Android devices and get their local IP addresses.

2. Run the application:
```
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Setting Up IP Webcams

1. Install the "IP Webcam" app from Google Play Store on Android devices.
2. Open the app and scroll down to "Start server".
3. Note the IP address shown at the bottom of the screen.
4. Use this IP with the port (usually 8080) in your configuration.
   For example: `http://192.168.1.100:8080/video`

## Customization

- The detection models can be replaced with your own trained models.
- Adjust proximity thresholds in `app/utils/detection.py`.
- Modify the alert thresholds and durations as needed.

## License

MIT

## Acknowledgements

- OpenCV for computer vision functionality
- Flask for web framework
- Bootstrap for dashboard UI 