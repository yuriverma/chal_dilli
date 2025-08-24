# 🚇 CHAL DILLI - Delhi's AI Assistant

**CHAL DILLI** is an offline, community-driven AI assistant focused on Delhi-specific needs. Think of it as a LocalGPT for Delhi - it answers queries about metro routes, DTC buses, food spots, travel tips, local activities, and events.

## 🎯 Features

- **🚇 Delhi Metro Routing**: Real-time route calculation with fares using official DMRC GTFS data
- **🚌 DTC Bus Information**: Bus routes and schedules
- **🍕 Food Recommendations**: Local food spots and recommendations
- **🎉 Events & Activities**: Delhi events and local activities
- **🌍 Multi-language Support**: English, Hindi, and Hinglish responses
- **👨‍💼 Big Brother Tone**: Humanized, friendly responses

## 🏗️ Project Structure

```
chal-dilli/
├── backend/                 # Python FastAPI backend
│   ├── api_server.py       # Main API server
│   ├── chal_dilli_enhanced.py  # Core AI logic
│   ├── enhanced_metro_router.py # Metro routing with GTFS
│   ├── metro_router.py     # GTFS-based Metro router
│   ├── data_scraper.py     # Data scraping utilities
│   ├── delhi_metro_scraper.py # Delhi Metro scraper
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   └── chal-delhi/        # React + Vite + Tailwind app
├── data/                   # Data files
│   └── DMRC_GTFS (1)/     # Official Delhi Metro GTFS data
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Backend Setup (Python)

1. **Navigate to backend directory:**
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

4. **Start the API server:**
   ```bash
   python api_server.py
   ```

   The API will be available at: `http://localhost:8000`

### Frontend Setup (React)

1. **Navigate to frontend directory:**
   ```bash
   cd frontend/chal-delhi
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at: `http://localhost:5173`

## 🔧 API Endpoints

### Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "query": "dwarka se rajiv chowk kaise jaana?"
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

## 🧪 Testing

### Test API with curl:
```bash
# English query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "how to go from dwarka to karol bagh?"}'

# Hindi query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "rajouri garden se faridabad kaise jau?"}'
```

### Test Frontend:
1. Open `http://localhost:5173` in your browser
2. Try these queries:
   - "dwarka se rajiv chowk kaise jaana?"
   - "how to go from govind puri to rajouri garden?"
   - "rajouri garden se badarpur ka route?"

## 🔄 Development Workflow

### For Backend Developers:
1. Make changes to Python files in `backend/`
2. Restart the API server: `python api_server.py`
3. Test with curl or frontend

### For Frontend Developers:
1. Make changes to React files in `frontend/chal-delhi/src/`
2. Frontend auto-reloads on changes
3. Test with the running backend API

## 📁 Data Sources

- **Delhi Metro**: Real-time scraping from official DMRC websites
- **GTFS Data**: Official Delhi Metro GTFS files for accurate routing
- **DTC Buses**: Scraped from official sources
- **Food & Events**: Community-curated data with RSS feeds

## 🚀 Deployment

### Local Development:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### Production (Future):
- Backend: Deploy to VPS/Render/Hugging Face Spaces
- Frontend: Deploy to Vercel/Netlify
- Domain: `chaldilli.com`

## 🤝 Contributing

### Adding New Features:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Data Contributions:
- Add new data files to `data/` directory
- Update scrapers in `backend/`
- Follow the existing data format

## 📞 Support

For issues or questions:
- Check the API documentation at `http://localhost:8000/docs`
- Review the backend logs for errors
- Test individual components separately

## 🎯 Roadmap

- [x] Basic Metro routing with GTFS data
- [x] Multi-language support (English/Hindi/Hinglish)
- [x] Real-time Metro status scraping
- [x] Frontend integration
- [ ] DTC bus route integration
- [ ] Food recommendation system
- [ ] Event calendar integration
- [ ] Community data contribution system
- [ ] Production deployment

---

**Built with ❤️ for Delhi by the Delhi community**
