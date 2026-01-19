import ee
from datetime import datetime, timedelta

# initialize once per process (call ee.Initialize externally in production)

def initialize_ee(service_account_email: str = None, key_file: str = "key.json", project: str = None):
    if service_account_email is None:
        # assume already authenticated in environment
        ee.Initialize()
    else:
        credentials = ee.ServiceAccountCredentials("imsukudu24@gmail.com", "key.json")
        ee.Initialize(credentials, project="careful-drummer-462304-u9")


def meters_to_degrees(meters: float) -> float:
    # rough conversion at Earth's surface (valid for small distances)
    return meters / 111000.0


def fetch_lst(lat: float, lon: float, radius_m: int = 300, start_days: int = 60, prefer: str = "auto") -> str:
    """
    Fetch an LST tile (NumPy .npy) from Earth Engine around (lat, lon) with radius in meters.
    Returns a download URL for a NumPy array image (float32) with NaNs for invalid pixels.

    prefer: "auto" | "landsat" | "sentinel"
    """
    today = datetime.utcnow().date()
    start = today - timedelta(days=start_days)

    point = ee.Geometry.Point(lon, lat)
    region = point.buffer(radius_m).bounds()

    def landsat_coll():
        return (
            ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
            .filterDate(str(start), str(today))
            .filterBounds(region)
            .filter(ee.Filter.lt("CLOUD_COVER", 40))
            .select(["ST_B10"])  # thermal band
            .map(lambda img: img.multiply(0.00341802).add(149).subtract(273.15).copyProperties(img, img.propertyNames()))
        )

    def sentinel_coll():
        # Make a crude SWIR-based proxy LST using B11/B12 (not physically LST but useful for relative hotspots)
        def make_lst(img):
            b11 = img.select("B11")
            b12 = img.select("B12")
            lst = b11.add(b12).multiply(0.5).subtract(273.15)
            return lst.rename("LST").copyProperties(img, img.propertyNames())

        return (
            ee.ImageCollection("COPERNICUS/S2_SR")
            .filterDate(str(start), str(today))
            .filterBounds(region)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
            .select(["B11", "B12"])  # SWIR bands
            .map(make_lst)
        )

    # Try preferred then fallback
    tried = []
    for choice in ([prefer] if prefer != "auto" else ["landsat", "sentinel"]):
        if choice == "landsat":
            coll = landsat_coll()
        elif choice == "sentinel":
            coll = sentinel_coll()
        else:
            continue

        try:
            size = coll.size().getInfo()
        except Exception:
            size = 0

        tried.append((choice, size))

        if size and size > 0:
            # median image
            if choice == "landsat":
                lst_img = coll.median().select("ST_B10") if False else coll.median()
            else:
                lst_img = coll.median().select("LST")

            url = lst_img.getDownloadURL({
                "scale": 30 if choice == "landsat" else 20,
                "region": region,
                "format": "NPY"
            })
            return url

    # If we reach here, none had images
    raise RuntimeError(f"No usable cloud-free scenes in the last {start_days} days. Tried: {tried}")

