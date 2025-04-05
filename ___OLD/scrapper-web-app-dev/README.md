# TLD Domain Scraper Web Application

A web application for scraping domains with specific TLDs using Selenium and FastAPI.

## Prerequisites

- Python 3.8+
- Chrome browser installed
- ChromeDriver installed

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd scrapper-web-app-dev
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install ChromeDriver:

### macOS Setup
1. Install ChromeDriver using Homebrew:
```bash
brew install chromedriver
```

2. Allow ChromeDriver in macOS Security:
   - Open System Settings
   - Go to Privacy & Security
   - Scroll down to Security
   - Look for a message about ChromeDriver being blocked
   - Click "Allow Anyway"
   - If prompted, enter your administrator password
   - You may need to right-click ChromeDriver in Finder and select "Open" to confirm the security exception

### Linux Setup
```bash
sudo apt-get install chromium-chromedriver
```

### Windows Setup
Download ChromeDriver from [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads) and add it to your system PATH.

## Running the Application

1. Make sure your virtual environment is activated:
```bash
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

2. Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

3. Open your browser and navigate to:
```
http://localhost:8000
```

## Usage

1. Enter a TLD (e.g., `.edu.sd`) in the input field
2. Click "Start Scraping"
3. If a CAPTCHA appears, solve it manually in the browser window
4. Monitor progress in the dashboard
5. Download results when complete

## Features

- Real-time progress tracking
- Manual CAPTCHA solving
- Download results as text file
- Dashboard with statistics
- WebSocket updates for live feedback

## Troubleshooting

### macOS Security Issues
If you see a security warning when running ChromeDriver:
1. Go to System Settings > Privacy & Security
2. Look for ChromeDriver in the Security section
3. Click "Allow Anyway"
4. You may need to right-click ChromeDriver in Finder and select "Open" to confirm

### ChromeDriver Version Mismatch
If you encounter version mismatch errors:
1. Check your Chrome browser version
2. Install the matching ChromeDriver version
3. For macOS: `brew upgrade chromedriver`

### Virtual Environment Issues
If you encounter package-related errors:
1. Make sure your virtual environment is activated
2. Verify you're in the correct directory
3. Try reinstalling requirements:
```bash
pip install -r requirements.txt --upgrade
```

## License

MIT License

## API Endpoints

- `GET /`: Web interface for domain scraping
- `POST /scrape`: Trigger domain scraping for a specific TLD
- `GET /domains`: List all stored domains
- `GET /domains/{tld}`: List domains for a specific TLD

## Development

The application structure:
```
scrapper-web-app-dev/
├── app/
│   ├── main.py           # FastAPI application and routes
│   ├── models.py         # Database models
│   ├── services/
│   │   └── scraper.py    # Domain scraping service
│   └── templates/
│       └── index.html    # Web interface template
├── static/              # Static files (CSS, JS)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 