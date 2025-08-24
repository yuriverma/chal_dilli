# 🚇 CHAL DILLI Backend

This is the Python FastAPI backend for CHAL DILLI - Delhi's AI Assistant.

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- pip
- Git

### Installation

1. **Clone and navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python api_server.py
   ```

   The API will be available at: `http://localhost:8000`

## 📁 File Structure

```
backend/
├── api_server.py              # Main FastAPI server
├── chal_dilli_enhanced.py     # Core AI logic with pattern matching
├── enhanced_metro_router.py   # Metro routing with language detection
├── metro_router.py           # GTFS-based Metro router (core logic)
├── data_scraper.py           # Data scraping utilities
├── delhi_metro_scraper.py    # Delhi Metro real-time scraper
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🔧 API Endpoints

### Main Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "query": "dwarka se rajiv chowk kaise jaana?"
}
```

**Response:**
```json
{
  "response": "Bhai, Dwarka se Rajiv Chowk tak ka route...",
  "status": "success"
}
```

### Health Check
```bash
GET /health
```

### Metro Status
```bash
GET /metro-status
```

### Data Summary
```bash
GET /data-summary
```

### Update Data
```bash
POST /update-data
```

## 🧪 Testing

### Test with curl:
```bash
# English query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "how to go from dwarka to karol bagh?"}'

# Hindi query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "rajouri garden se faridabad kaise jau?"}'

# Metro status
curl "http://localhost:8000/metro-status"

# Health check
curl "http://localhost:8000/health"
```

### Test with Python:
```python
import requests

# Test chat endpoint
response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "dwarka se rajiv chowk kaise jaana?"}
)
print(response.json())
```

## 🔍 Troubleshooting

### Common Issues:

1. **Port 8000 already in use:**
   ```bash
   # Kill existing process
   lsof -ti:8000 | xargs kill -9
   # Or change port in api_server.py
   ```

2. **Virtual environment not activated:**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Dependencies not installed:**
   ```bash
   pip install -r requirements.txt
   ```

4. **GTFS data not found:**
   - Ensure `../data/DMRC_GTFS (1)/` directory exists
   - Check file permissions

5. **Metro scraper timeout:**
   - This is normal, the system falls back to cached data
   - Check internet connection

### Debug Mode:
```bash
# Run with debug logging
python -u api_server.py
```

## 🔄 Development

### Making Changes:
1. Edit Python files
2. Restart the server: `python api_server.py`
3. Test with curl or frontend

### Adding New Features:
1. Create new Python modules
2. Import in `api_server.py`
3. Add new endpoints as needed
4. Update this README

### Data Updates:
- Metro data updates automatically on startup
- Use `POST /update-data` to force refresh
- Check logs for scraping status

## 📊 Data Sources

- **Delhi Metro**: Real-time scraping from DMRC websites
- **GTFS Data**: Official Delhi Metro GTFS files
- **DTC Buses**: Scraped from official sources
- **Food & Events**: Community-curated data

## 🚀 Production Deployment

### Environment Variables:
```bash
export HOST=0.0.0.0
export PORT=8000
export DEBUG=false
```

### Using Gunicorn:
```bash
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker (Future):
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_server.py"]
```

## 📞 Support

- Check API docs: `http://localhost:8000/docs`
- Review server logs for errors
- Test individual components
- Check GTFS data integrity

---

**Backend ready for frontend integration! 🚀**
