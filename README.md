# Construction Site Safety Monitoring System - Setup Instructions

## Overview
This system provides real-time monitoring of construction site safety with the following features:
- Real-time camera feeds with proper alignment
- Safety gear violation detection (helmet, vest)
- Proximity violation detection between workers and machinery
- Violation analysis page with screenshots and detailed reports
- Database storage for violation history
- Web-based dashboard with modern UI

## Features Implemented

### 1. Frontend Improvements ✅
- Fixed camera feed alignment and layout
- Responsive design with proper Bootstrap grid
- Equal height cards for consistent appearance
- Improved visual hierarchy and spacing

### 2. Real-time Detection ✅
- Removed fake detection elements
- Implemented actual computer vision-based detection
- Safety gear detection using color analysis
- Proximity detection using distance calculations
- Automatic screenshot capture for violations

### 3. Proximity Violation Detection ✅
- Real-time detection of workers too close to machinery
- Color-based machinery detection (yellow/orange equipment)
- Configurable safety distance threshold (80 pixels)
- Alert cooldown to prevent spam

### 4. Violation Analysis Page ✅
- Comprehensive violation dashboard
- Filtering by date, camera, and violation type
- Interactive charts and statistics
- Detailed violation information with screenshots
- Export functionality for data analysis

### 5. Database Integration ✅
- SQLite database for persistent storage
- Violation history tracking
- Camera status monitoring
- Statistics and reporting

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- OpenCV (cv2)
- Flask and Flask-SocketIO
- SQLite3

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python app.py
```

### Step 3: Access the Dashboard
- Main Dashboard: http://localhost:5000
- Violation Analysis: http://localhost:5000/violations

## Configuration

### Camera Setup
The system supports multiple camera sources:
- Webcam (camera index 0, 1, 2, 3)
- IP cameras (RTSP streams)
- Video files

To configure cameras, set environment variables:
```bash
export CAMERA_0_URL="0"  # Webcam
export CAMERA_1_URL="1"  # Second webcam
export CAMERA_2_URL="rtsp://your-ip-camera-url"
export CAMERA_3_URL="path/to/video/file.mp4"
```

### Detection Parameters
You can adjust detection sensitivity in `app/utils/detection.py`:

**Safety Gear Detection:**
- `alert_threshold`: Time before alert (default: 3 seconds)
- Color thresholds for helmet and vest detection

**Proximity Detection:**
- `proximity_threshold`: Safety distance in pixels (default: 80)
- `alert_cooldown`: Time between alerts (default: 5 seconds)

## Usage

### Main Dashboard
1. **Camera Feeds**: View real-time camera feeds with detection overlays
2. **Safety Alerts**: Monitor safety gear violations in real-time
3. **Proximity Alerts**: Monitor worker-machinery proximity violations
4. **Statistics**: View compliance rates and worker counts
5. **Settings**: Toggle detection features and audio alerts

### Violation Analysis Page
1. **Summary Cards**: Overview of total violations by type
2. **Filters**: Filter violations by date, camera, and type
3. **Charts**: Visual representation of violation trends
4. **Violation Table**: Detailed list with screenshots
5. **Export**: Download violation data as CSV

### Key Features

#### Real-time Detection
- **Safety Gear**: Detects missing helmets and safety vests using color analysis
- **Proximity**: Monitors distance between workers and machinery
- **Screenshots**: Automatically captures violation images
- **Alerts**: Real-time notifications via WebSocket

#### Database Storage
- All violations are stored in SQLite database
- Screenshots saved to `static/violations/` directory
- Violation history with timestamps and analysis
- Camera status tracking

#### Analysis & Reporting
- Interactive charts showing violation trends
- Filterable violation history
- Detailed violation analysis with recommendations
- Export functionality for compliance reporting

## File Structure
```
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # API endpoints and routes
│   ├── database.py          # Database operations
│   ├── templates/
│   │   ├── index.html       # Main dashboard
│   │   └── violations.html  # Violation analysis page
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css    # Main styles
│   │   │   └── violations.css # Violation page styles
│   │   └── js/
│   │       ├── dashboard.js # Main dashboard logic
│   │       └── violations.js # Violation page logic
│   └── utils/
│       ├── camera.py        # Camera management
│       └── detection.py     # Detection algorithms
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── violations.db           # SQLite database (created automatically)
```

## Troubleshooting

### Camera Issues
- Ensure cameras are properly connected
- Check camera permissions
- Verify camera indices (0, 1, 2, 3)
- For IP cameras, test RTSP URLs

### Detection Issues
- Adjust detection thresholds in `detection.py`
- Ensure good lighting conditions
- Check camera positioning and angles
- Verify color contrast for safety gear

### Performance Issues
- Reduce camera resolution if needed
- Adjust detection frequency
- Close unnecessary applications
- Use hardware acceleration if available

## API Endpoints

### Violations
- `GET /api/violations` - Get violations with filters
- `POST /api/violations/<id>/resolve` - Resolve a violation
- `GET /api/statistics` - Get violation statistics

### Camera Feeds
- `GET /video_feed/<camera_id>` - Stream camera feed

## Customization

### Adding New Detection Types
1. Extend the detection classes in `detection.py`
2. Add new violation types to the database schema
3. Update the frontend to display new violation types

### Modifying UI
1. Edit HTML templates in `templates/`
2. Update CSS in `static/css/`
3. Modify JavaScript in `static/js/`

### Database Schema
The system uses SQLite with the following tables:
- `violations`: Stores violation records
- `camera_status`: Tracks camera status
- `statistics`: Stores daily statistics

## Support
For issues or questions, check the console output for error messages and ensure all dependencies are properly installed.
