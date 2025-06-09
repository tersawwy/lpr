# 🚗 Smart Parking System

## Overview

[cite_start]This project implements a Smart Parking System that uses computer vision (OCR) to detect and validate vehicle license plates, automatically controlling barrier access for authorized vehicles. It integrates an Arduino-based sensor system for slot occupancy detection and logs vehicle entry/exit.

**Key Features:**
* **Automatic License Plate Recognition (LPR):** Utilizes OpenCV and EasyOCR for real-time license plate detection and text extraction.
* **Advanced Image Preprocessing:** Employs multiple image processing techniques (grayscale inversion, CLAHE, adaptive thresholding, Otsu's thresholding, Canny edge detection with dilation) to enhance OCR accuracy under varying lighting conditions.
* **Fuzzy Matching:** Allows for minor variations in detected license plates by comparing them against an `allowed_plates.txt` list using fuzzy string matching.
* **ESP32 Integration (Optional):** Communicates with an ESP32 microcontroller (or similar) to control physical barriers (e.g., servo motor for a gate).
* [cite_start]**Occupancy Detection:** (Conceptual, integrates with Arduino/ESP32) Uses ultrasonic sensors (or similar) to determine parking slot availability.
* **Real-time Monitoring:** Displays camera feed with ROI and system status.
* **Configurable Parameters:** Easily adjust settings like scan interval, OCR confidence, and fuzzy match threshold.

## Demo

(You can add a GIF or short video here demonstrating the system in action. For example, a car approaching, plate being recognized, gate opening, and then closing.)

## Technologies Used

* **Python:** Main programming language.
* **OpenCV:** For image processing and video capture.
* **EasyOCR:** For robust Optical Character Recognition.
* **`pyserial`:** For communication with the ESP32 microcontroller.
* **`difflib`:** For fuzzy string matching.
* [cite_start]**Arduino/ESP32 (External Hardware):** For sensor integration and gate control.

## Setup Instructions

### Prerequisites

* Python 3.x
* OpenCV
* EasyOCR
* `pyserial`
* `numpy`
* A webcam or camera connected to your system.
* (Optional) An ESP32 or Arduino board programmed to receive serial commands (e.g., "OK" for access granted).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/tersawwy/lpr/](https://github.com/tersawwy/lpr/)
    cd lpr
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install opencv-python easyocr pyserial numpy
    ```
    *Note: EasyOCR might require additional dependencies for specific environments. Refer to the [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR) for detailed installation instructions if you encounter issues.*

### Configuration

1.  **`allowed_plates.txt`:**
    Create a file named `allowed_plates.txt` in the root directory of the project. Each line in this file should contain an allowed license plate number. Blank lines or lines consisting only of whitespace will be ignored. License plates are case-insensitive and spaces are removed before matching.

    Example `allowed_plates.txt`:
    ```
    ABC123
    XYZ 789
    م ع 1234
    ```

2.  **Configuration Parameters (in `main.py`):**
    You can adjust parameters directly in the `main.py` script:

    ```python
    SERIAL_PORT = '/dev/cu.usbserial-110'  # Your ESP32/Arduino serial port
    BAUD_RATE = 115200
    ALLOWED_FILE = 'allowed_plates.txt'
    CAMERA_INDEX = 0                    # Your webcam index (0 is usually default, try 1, 2, etc.)
    FUZZY_MATCH_THRESHOLD = 0.8         # Sensitivity for fuzzy matching (0.0 to 1.0)
    SCAN_INTERVAL = 6                   # Time in seconds between automatic scans
    PADDING = 15                        # Padding around ROI for OCR
    COOLDOWN_AFTER_MATCH = 10           # Time in seconds after a successful match before scanning again
    ```
    * **`SERIAL_PORT`**: On Linux, this might be `/dev/ttyUSB0` or `/dev/ttyACM0`. On Windows, it will be `COMX` (e.g., `COM3`).
    * **`CAMERA_INDEX`**: If `0` doesn't work, try `1`, `2`, etc., depending on your camera setup.

### Running the System

Execute the `main.py` script:

```bash
python main.py
