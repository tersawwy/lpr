import cv2
import easyocr
import serial
import time
import difflib
import ssl
import numpy as np


ssl._create_default_https_context = ssl._create_unverified_context


SERIAL_PORT = '/dev/cu.usbserial-110'  
BAUD_RATE = 115200
ALLOWED_FILE = 'allowed_plates.txt'
CAMERA_INDEX = 0
FUZZY_MATCH_THRESHOLD = 0.8
SCAN_INTERVAL = 6  
PADDING = 15
COOLDOWN_AFTER_MATCH = 10  

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"[INFO] Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"[ERROR] Could not open serial port: {e}")
    print(f"[INFO] Running in demo mode without ESP32 connection")
    ser = None


try:
    with open(ALLOWED_FILE, 'r') as f:
        allowed_plates = set(
            line.strip().replace(" ", "").upper()
            for line in f if line.strip()
        )
    print(f"[INFO] Loaded {len(allowed_plates)} allowed plates")
except FileNotFoundError:
    print(f"[ERROR] File '{ALLOWED_FILE}' not found. Creating empty list.")
    allowed_plates = set()


cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print(f"[ERROR] Cannot open camera index {CAMERA_INDEX}. Try another index.")
    exit()

ret, frame = cap.read()
if not ret:
    print("[ERROR] Could not read from camera to get frame size.")
    exit()

frame_height, frame_width = frame.shape[:2]
roi_width = int(frame_width * 0.4)   # Slightly larger ROI
roi_height = int(frame_height * 0.25)
roi_x = (frame_width - roi_width) // 2
roi_y = (frame_height - roi_height) // 2
REGION = (roi_x, roi_y, roi_width, roi_height)

# Initialize OCR reader
reader = easyocr.Reader(['en', 'ar'], gpu=False)
print("[INFO] EasyOCR initialized")

def preprocess_image(image):
    """Enhanced image preprocessing pipeline specifically for license plates"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    dark_pixels = sum(hist[:127])[0]
    light_pixels = sum(hist[127:])[0]
    
 
    if dark_pixels > light_pixels:
        gray = cv2.bitwise_not(gray)
    
  
    preprocessed_images = []
    

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    preprocessed_images.append(enhanced)
    
    
    adaptive_thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    preprocessed_images.append(adaptive_thresh)
    
   
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    _, otsu_thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    preprocessed_images.append(otsu_thresh)
    
   
    edges = cv2.Canny(enhanced, 100, 200)
    dilated_edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    preprocessed_images.append(dilated_edges)
    
    return preprocessed_images

def fuzzy_match(detected_plate, allowed_plates, threshold=FUZZY_MATCH_THRESHOLD):
    """Check if detected plate matches any allowed plate with fuzzy matching"""
    for allowed_plate in allowed_plates:
        similarity = difflib.SequenceMatcher(None, detected_plate, allowed_plate).ratio()
        if similarity >= threshold:
            print(f"[INFO] Fuzzy match: '{detected_plate}' matches '{allowed_plate}' ({similarity:.2f})")
            return True, allowed_plate
    return False, None


last_scan_time = time.time()
last_match_time = 0
last_detected_plate = None
print("[INFO] Automatic scanning enabled. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[WARNING] Failed to grab frame. Retrying...")
        time.sleep(0.5)
        continue

   
    x, y, w, h = REGION
    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(frame, "Place plate in box", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    
    current_time = time.time()
    
   
    in_cooldown = current_time - last_match_time < COOLDOWN_AFTER_MATCH
    
    
    if in_cooldown:
        cooldown_remaining = COOLDOWN_AFTER_MATCH - (current_time - last_match_time)
        status_text = f"Access granted. Cooldown: {cooldown_remaining:.1f}s"
        status_color = (0, 255, 0)  # Green for success
    else:
        scan_remaining = SCAN_INTERVAL - (current_time - last_scan_time)
        if scan_remaining > 0:
            status_text = f"Next scan in {scan_remaining:.1f}s"
        else:
            status_text = "Ready to scan"
        status_color = (0, 255, 255)  # Yellow for waiting
    
    cv2.putText(frame, status_text, (10, frame_height - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    cv2.imshow("License Plate Scanner", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        print("[INFO] Exiting.")
        break
    elif key == ord('s') and not in_cooldown:  
        print("[INFO] Manual scan triggered")
        last_scan_time = current_time - SCAN_INTERVAL  

  
    if not in_cooldown and current_time - last_scan_time >= SCAN_INTERVAL:
        last_scan_time = current_time
        print("\n[INFO] Scanning for license plate...")

        
        x_pad = max(0, x - PADDING)
        y_pad = max(0, y - PADDING)
        w_pad = min(frame_width - x_pad, w + 2 * PADDING)
        h_pad = min(frame_height - y_pad, h + 2 * PADDING)
        roi = frame[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
        
      
        cv2.imwrite("debug_original_roi.jpg", roi)
        
        # Apply enhanced preprocessing
        preprocessed_images = preprocess_image(roi)
        
        # Save debug images
        for i, img in enumerate(preprocessed_images):
            cv2.imwrite(f"debug_preprocess_{i}.jpg", img)
        
        # Try OCR on each preprocessed image until successful
        plate_text = None
        confidence = 0
        
        for i, img in enumerate(preprocessed_images):
            result = reader.readtext(img)
            print(f"[DEBUG] OCR results for method {i}: {result}")
            
            if result:
                # Sort by confidence and filter out low confidence results
                valid_results = [r for r in result if r[2] > 0.3]  # Filter by minimum confidence
                if valid_results:
                    valid_results.sort(key=lambda x: -x[2])  # Sort by confidence
                    if valid_results[0][2] > confidence:  # Take highest confidence across all methods
                        confidence = valid_results[0][2]
                        plate_text = valid_results[0][1]
        
        if plate_text:
           
            normalized_plate = plate_text.strip().replace(" ", "").upper()
            print(f"[INFO] Detected Plate: '{normalized_plate}' with confidence: {confidence:.2f}")
            
            
            if normalized_plate == last_detected_plate:
                print("[INFO] Same plate detected again. Skipping to avoid duplicate actions.")
                continue
                
            
            last_detected_plate = normalized_plate
            
            
            if normalized_plate in allowed_plates:
                print("[SUCCESS] Exact match found. Access granted.")
                last_match_time = current_time  
                
                if ser:
                    try:
                        ser.write("OK\n".encode())
                        feedback = ser.readline().decode('utf-8').strip()
                        print(f"[INFO] ESP32 Response: {feedback}")
                    except Exception as e:
                        print(f"[ERROR] Failed to communicate with ESP32: {e}")
            else:
                # Try fuzzy matching
                match_found, matched_plate = fuzzy_match(normalized_plate, allowed_plates)
                if match_found:
                    print(f"[SUCCESS] Fuzzy match found with '{matched_plate}'. Access granted.")
                    last_match_time = current_time  # Set the last match time for cooldown
                    
                    if ser:
                        try:
                            ser.write("OK\n".encode())
                            feedback = ser.readline().decode('utf-8').strip()
                            print(f"[INFO] ESP32 Response: {feedback}")
                        except Exception as e:
                            print(f"[ERROR] Failed to communicate with ESP32: {e}")
                else:
                    print("[DENIED] No match found - access denied.")
        else:
            print("[WARNING] No text detected in this scan.")
            last_detected_plate = None  

# Clean up
cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()