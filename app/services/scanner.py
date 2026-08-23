import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
except Exception:
    pyzbar_decode = None


def decode_image(contents: bytes):
    """
    Convert uploaded image bytes into an OpenCV image.
    """

    if not contents:
        return None

    np_image = np.frombuffer(contents, dtype=np.uint8)

    frame = cv2.imdecode(
        np_image,
        cv2.IMREAD_COLOR
    )

    return frame


def resize_for_scanning(frame, max_width=1600):
    """
    Resize very large images while preserving aspect ratio.
    """

    if frame is None:
        return None

    height, width = frame.shape[:2]

    if width <= max_width:
        return frame

    scale = max_width / width

    new_width = int(width * scale)
    new_height = int(height * scale)

    return cv2.resize(
        frame,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )


def create_preprocessed_versions(frame):
    """
    Create several image versions to improve
    QR/barcode detection.
    """

    versions = []

    # Original
    versions.append(frame)

    # Grayscale
    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    versions.append(gray)

    # Histogram equalization
    equalized = cv2.equalizeHist(gray)

    versions.append(equalized)

    # Gaussian blur
    blurred = cv2.GaussianBlur(
        gray,
        (3, 3),
        0
    )

    versions.append(blurred)

    # Adaptive threshold
    threshold = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    versions.append(threshold)

    return versions


def detect_qr(frame):
    """
    Detect QR codes using OpenCV.
    """

    detector = cv2.QRCodeDetector()

    # Normal QR detection
    try:
        value, points, _ = detector.detectAndDecode(frame)

        if value:
            return value
    except Exception:
        pass

    # Multiple QR codes
    try:
        result = detector.detectAndDecodeMulti(frame)

        if result is not None:
            decoded_info = result[1]

            if decoded_info:
                for value in decoded_info:
                    if value:
                        return value
    except Exception:
        pass

    return None


def detect_opencv_barcode(frame):
    """
    Try OpenCV's built-in BarcodeDetector.

    Availability depends on the installed OpenCV version.
    """

    try:
        detector = cv2.barcode.BarcodeDetector()

        result = detector.detectAndDecode(frame)

        if result is None:
            return None

        # Different OpenCV versions return different structures.
        if isinstance(result, tuple):

            for item in result:
                if isinstance(item, str) and item:
                    return item

                if isinstance(item, (list, tuple)):
                    for value in item:
                        if isinstance(value, str) and value:
                            return value

        elif isinstance(result, str):
            return result

    except Exception:
        pass

    return None


def detect_pyzbar_barcode(frame):
    """
    Detect traditional barcodes using pyzbar.
    """

    if pyzbar_decode is None:
        return None

    try:
        detected = pyzbar_decode(frame)

        if detected:

            for item in detected:

                try:
                    value = item.data.decode(
                        "utf-8",
                        errors="ignore"
                    )

                    if value:
                        return value

                except Exception:
                    continue

    except Exception:
        pass

    return None


def detect_food_code(frame):
    """
    Main QR/barcode detection pipeline.

    Returns:
        {
            "code": "...",
            "type": "QR" / "BARCODE"
        }

        or None
    """

    if frame is None:
        return None

    frame = resize_for_scanning(frame)

    versions = create_preprocessed_versions(frame)

    # --------------------------------------------------
    # QR CODE
    # --------------------------------------------------

    for image in versions:

        value = detect_qr(image)

        if value:
            return {
                "code": value,
                "type": "QR"
            }

    # --------------------------------------------------
    # OPENCV BARCODE
    # --------------------------------------------------

    for image in versions:

        value = detect_opencv_barcode(image)

        if value:
            return {
                "code": value,
                "type": "BARCODE"
            }

    # --------------------------------------------------
    # PYZBAR
    # --------------------------------------------------

    for image in versions:

        value = detect_pyzbar_barcode(image)

        if value:
            return {
                "code": value,
                "type": "BARCODE"
            }

    return None