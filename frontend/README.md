# 🎨 CHAL DILLI Frontend

This is the React frontend for CHAL DILLI - Delhi's AI Assistant.

## 🚀 Quick Setup

### Prerequisites
- Node.js 16+ 
- npm or yarn
- Git

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend/chal-delhi
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at: `http://localhost:5173`

## 📁 Project Structure

```
frontend/chal-delhi/
├── src/
│   ├── pages/
│   │   └── ChattingPage.jsx    # Main chat interface
│   ├── components/             # React components
│   ├── App.jsx                 # Main app component
│   └── main.jsx               # Entry point
├── public/                    # Static assets
├── package.json              # Dependencies
└── vite.config.js           # Vite configuration
```

## 🔧 API Integration

### Backend Connection
The frontend connects to the backend API at: `http://localhost:8000`

### API Endpoints Used:
- `POST /chat` - Send user queries
- `GET /health` - Health check

### Example API Call:
```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: userInput
  })
});

const data = await response.json();
const botResponse = data.response;
```

## 🧪 Testing

### Test Queries:
Try these queries in the chat interface:

**English:**
- "how to go from dwarka to karol bagh?"
- "what's the weather like in Delhi?"
- "tell me about Delhi metro"

**Hindi/Hinglish:**
- "dwarka se rajiv chowk kaise jaana?"
- "rajouri garden se faridabad kaise jau?"
- "delhi mein kahan khana khayein?"

### Expected Responses:
- Metro queries should return detailed routes with fares
- Weather queries should return current weather
- Food queries should return recommendations
- All responses should be in the detected language (English/Hindi/Hinglish)

## 🔄 Development

### Making Changes:
1. Edit files in `src/`
2. Frontend auto-reloads on changes
3. Test with the running backend

### Key Files to Modify:
- `src/pages/ChattingPage.jsx` - Main chat interface
- `src/App.jsx` - App layout
- `src/App.css` - Styling

### Adding New Features:
1. Create new components in `src/components/`
2. Import and use in main pages
3. Test thoroughly with backend API

## 🎨 Styling

### Technologies Used:
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool
- **React 19** - Latest React version

### Customization:
- Edit `src/App.css` for custom styles
- Use Tailwind classes for quick styling
- Modify `tailwind.config.js` for theme changes

## 🚀 Building for Production

### Build the project:
```bash
npm run build
```

### Preview production build:
```bash
npm run preview
```

### Deploy:
- Build files are in `dist/` directory
- Deploy to Vercel, Netlify, or any static hosting

## 🔍 Troubleshooting

### Common Issues:

1. **Backend not running:**
   - Ensure backend is running on `http://localhost:8000`
   - Check backend logs for errors

2. **CORS errors:**
   - Backend has CORS enabled for `http://localhost:5173`
   - Check if backend is accessible

3. **API calls failing:**
   - Check browser console for errors
   - Verify API endpoint format
   - Test with curl first

4. **Styling issues:**
   - Check Tailwind CSS is loaded
   - Verify CSS imports in main files

### Debug Mode:
```bash
# Run with debug logging
npm run dev -- --debug
```

## 📱 Responsive Design

The frontend is designed to work on:
- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (320px - 767px)

## 🎯 Features to Implement

### Current Features:
- ✅ Chat interface
- ✅ API integration
- ✅ Responsive design
- ✅ Real-time responses

### Future Features:
- [ ] Message history
- [ ] Loading states
- [ ] Error handling
- [ ] Voice input
- [ ] Location-based suggestions
- [ ] Metro route visualization
- [ ] Food recommendation cards

## 🔗 Backend Integration

### Required Backend Features:
- ✅ Chat endpoint (`POST /chat`)
- ✅ Health check (`GET /health`)
- ✅ CORS enabled for frontend
- ✅ JSON responses

### Testing Backend:
```bash
# Test from frontend directory
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'
```

## 📞 Support

For frontend issues:
- Check browser console for errors
- Verify backend is running
- Test API endpoints directly
- Check network tab for failed requests

For backend issues:
- Check backend logs
- Test API with curl
- Verify GTFS data exists

---

**Frontend ready for development! 🎨**
