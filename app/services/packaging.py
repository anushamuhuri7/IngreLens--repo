import cv2
import numpy as np


def analyze_image_quality(image_path: str):
    """
    Analyze the quality of the uploaded medicine image.

    Returns:
        score: 0-100
        issues: list of detected image-quality problems
    """

    image = cv2.imread(image_path)

    if image is None:
        return 0, ["Unable to read image"]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate image sharpness using Laplacian variance
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

    issues = []

    # These thresholds are approximate and intended
    # for an MVP/demo, not pharmaceutical authentication.
    if sharpness < 50:
        issues.append("Image appears blurry")

    elif sharpness < 100:
        issues.append("Image has low sharpness")

    # Brightness analysis
    brightness = np.mean(gray)

    if brightness < 40:
        issues.append("Image is too dark")

    elif brightness > 220:
        issues.append("Image is overexposed")

    score = 100

    if sharpness < 50:
        score -= 40
    elif sharpness < 100:
        score -= 20

    if brightness < 40 or brightness > 220:
        score -= 20

    score = max(0, score)

    return score, issues


def detect_packaging_edges(image_path: str):
    """
    Detect major edges in the medicine package.

    This is a basic computer-vision feature that can
    help identify whether the package is visually clear.
    """

    image = cv2.imread(image_path)

    if image is None:
        return {
            "edge_detected": False,
            "edge_density": 0
        }

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = np.count_nonzero(edges)

    total_pixels = edges.shape[0] * edges.shape[1]

    edge_density = edge_pixels / total_pixels

    return {
        "edge_detected": edge_density > 0.02,
        "edge_density": round(edge_density, 4)
    }


def calculate_packaging_risk(
    image_quality_score: int,
    packaging_edges: dict
):
    """
    Calculate a basic packaging anomaly risk.

    Higher score = higher risk.

    This is NOT proof of counterfeit packaging.
    """

    risk = 0
    reasons = []

    if image_quality_score < 60:
        risk += 25
        reasons.append(
            "Packaging image quality is too low for reliable analysis"
        )

    if not packaging_edges["edge_detected"]:
        risk += 20
        reasons.append(
            "Packaging boundaries could not be clearly detected"
        )

    risk = min(risk, 100)

    confidence = 100 - risk

    return risk, confidence, reasons