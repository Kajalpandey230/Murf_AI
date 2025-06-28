<<<<<<< HEAD
# Driver's Drowsiness Detection System

A real-time drowsiness detection system that monitors driver alertness and sends emergency SMS alerts using computer vision and Twilio integration.

## Features

- Real-time face and eye detection
- Eye Aspect Ratio (EAR) calculation for drowsiness detection
- SMS alerts via Twilio when drowsiness is detected
- Web interface for monitoring
- Secure configuration using environment variables

## Prerequisites

- Python 3.8 or higher
- Webcam
- Twilio account (for SMS alerts)
- Shape predictor file (download instructions below)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd drowsiness_detection
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Download the shape predictor file:
```bash
# Download the file from:
# http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# Extract it and place it in the project root directory
```

5. Configure environment variables:
- Rename `.env.example` to `.env`
- Update the following variables in `.env`:
  - TWILIO_ACCOUNT_SID
  - TWILIO_AUTH_TOKEN
  - TWILIO_NUMBER
  - EMERGENCY_NUMBER

## Usage

1. Activate the virtual environment:
```bash
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Run the application:
```bash
python app.py
```

3. Open a web browser and navigate to:
```
http://localhost:5000
```

## How it Works

1. The system uses dlib's facial landmark detection to identify eye regions
2. Eye Aspect Ratio (EAR) is calculated to determine eye openness
3. If EAR falls below threshold for a certain number of consecutive frames, drowsiness is detected
4. When drowsiness is detected, an SMS alert is sent to the specified emergency contact
5. The web interface displays the live feed and current status

## Configuration

- `EYE_AR_THRESH`: Threshold for eye aspect ratio (default: 0.25)
- `EYE_AR_CONSEC_FRAMES`: Number of consecutive frames for drowsiness detection (default: 20)

## Troubleshooting

1. If the webcam doesn't start:
   - Check if another application is using the webcam
   - Verify webcam permissions

2. If SMS alerts aren't working:
   - Verify Twilio credentials in `.env`
   - Check if the phone number format is correct
   - Ensure you have sufficient Twilio credits

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
=======
# Murf_AI
>>>>>>> 782ed586bcdb969352a538c603c014d4227dd70a
