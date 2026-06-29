Barcode Scanner Using Webcam

A real-time product barcode scanner web application built with Python and Flask. It uses your laptop webcam to scan barcodes, fetches real product information from public APIs, displays it in a live table, and stores all scan history in a SQLite database.

---

 Features

- Webcam auto-starts when the app runs
- Scans any real product barcode (EAN-13, EAN-8, UPC-A, UPC-E, Code-128, Code-39)
- Fetches live product data from Open Food Facts, UPCitemdb, and Open Beauty Facts APIs
- Displays product name, brand, category, price, MFG date, EXP date, HSN code
- Live acknowledgment toast on every successful scan
- Duplicate barcode detection (same barcode not added twice)
- Stores complete scan history in SQLite database
- End / Start camera button to control the webcam
- Clear All button to reset the table and database
- Session timer and scan counter in the footer

---

 Project Structure

```
BARCODE SCANNER USING WEBCAM/
│
├── static/
│   ├── css/
│   │   └── style.css           Dark UI styling and animations
│   └── js/
│       └── scanner.js          QuaggaJS setup, fetch calls, table builder
│
├── templates/
│   ├── base.html               Base layout with header, footer, CDN scripts
│   └── index.html              Main page — camera view and product table
│
├── app.py                      Flask app, API routes, SocketIO events
├── config.py                   Loads settings from .env file
├── database.py                 SQLite init, save scan, get scans, clear scans
├── product_lookup.py           Real-time product lookup from public APIs
├── scanner.py                  OpenCV + pyzbar background scanning thread
├── scanner.db                  SQLite database (auto-created on first run)
├── .env                        Environment configuration (create manually)
├── requirements.txt            Python dependencies
└── README.md                   This file
```

---

 Tech Stack

| Layer                         | Technology |
| Language                      | Python 3.10+ |
| Web Framework                 | Flask 3.0 |
| Real-time Events              | Flask-SocketIO + Eventlet |
| Webcam Capture                | OpenCV (opencv-python) |
| Barcode Decoding (server)     | pyzbar |
| Barcode Decoding (browser)    | QuaggaJS (via CDN) |
| Database                      | SQLite3 (built into Python) |
| Product Data APIs             | Open Food Facts, UPCitemdb, Open Beauty Facts |
| Frontend                      | HTML5, CSS3, Vanilla JavaScript |
| Templating                    | Jinja2 |
| Config Management             | python-dotenv |

---

 Prerequisites

 1. Python 3.10 or higher
Download from https://www.python.org/downloads/

 2. zbar system library (required by pyzbar)

Windows:
Download the zbar DLL from https://sourceforge.net/projects/zbar/ and add it to your system PATH.

Ubuntu / Debian (Linux):
```bash
sudo apt-get install libzbar0
```

macOS:
```bash
brew install zbar
```

---

 Setup & Installation

 Step 1 — Clone or download the project
```
BARCODE SCANNER USING WEBCAM/
```
Make sure all files are in place as shown in the project structure above.

 Step 2 — Create a virtual environment
```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\Scripts\activate
```

macOS / Linux:
```bash
source venv/bin/activate
```

 Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

 Step 4 — Create the `.env` file
Create a file named `.env` in the root folder and paste this:
```
SECRET_KEY=your-secret-key-here
DATABASE_PATH=scanner.db
DEBUG=true
HOST=0.0.0.0
PORT=5000
CAMERA_INDEX=0
```

> `CAMERA_INDEX=0` means the default laptop webcam. Change to `1` if you have an external camera.

 Step 5 — Run the application
```bash
python app.py
```

 Step 6 — Open in browser
```
http://localhost:5000
```

The webcam will start automatically. Allow camera access when the browser asks.

---

 How It Works

```
Webcam (browser)
      ↓
QuaggaJS decodes barcode frame-by-frame
      ↓
POST /api/scan  →  Flask receives barcode number
      ↓
product_lookup.py calls Open Food Facts API
      ↓  (if not found)
product_lookup.py calls UPCitemdb API
      ↓  (if not found)
product_lookup.py calls Open Beauty Facts API
      ↓
Product info returned as JSON
      ↓
database.py saves scan to scanner.db
      ↓
Flask-SocketIO emits scan_result event
      ↓
Browser table updates live in real-time
```

---

 API Endpoints

| Method | Route | Description |

| GET   | `/`               | Renders the main scanner page |
| POST  | `/api/scan`       | Accepts `{"barcode": "..."}`, returns product JSON |
| GET   | `/api/products`   | Returns full scan history from database |
| POST  | `/api/clear`      | Clears all scan history from database |

---

 Supported Barcode Formats

| Format | Common Usage |

| EAN-13    | Most retail products worldwide |
| EAN-8     | Small retail products |
| UPC-A     | US retail products |
| UPC-E     | Compressed UPC for small items |
| Code-128  | Shipping, logistics |
| Code-39   | Industrial, automotive |

---

 Product Data Sources

| API | Coverage | API Key Needed |

| Open Food Facts                       | Food and grocery products     | No |
| UPCitemdb                             | General retail products       | No |
| Open Beauty Facts                     | Cosmetics and personal care   | No |

If no API has data for a scanned barcode, the app will still log the barcode number and show "Unknown Product" in the table.

---

 Common Issues

Camera not opening:
- Make sure no other app is using the webcam
- Try changing `CAMERA_INDEX=1` in `.env`
- Allow camera permissions in the browser

pyzbar import error on Windows:
- Download zbar DLL from https://sourceforge.net/projects/zbar/
- Place the DLL in your project folder or add to PATH

Port 5000 already in use:
- Change `PORT=5001` in `.env`
- Open `http://localhost:5001`

Product shows as Unknown:
- The barcode may not be in any public database
- Private label or local brand products often are not listed
- The barcode number is still saved to the database

---

 Database Schema

```sql
CREATE TABLE scan_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode      TEXT    NOT NULL,
    name         TEXT,
    brand        TEXT,
    category     TEXT,
    price        TEXT,
    mfg_date     TEXT,
    exp_date     TEXT,
    hsn_code     TEXT,
    source       TEXT,
    scanned_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);