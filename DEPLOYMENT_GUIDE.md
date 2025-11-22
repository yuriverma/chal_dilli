# Deployment Guide for CHAL DILLI Backend

## ✅ Recommended: Render.com (Current Setup)

**Status:** Already configured and working!

**URL:** https://chal-dilli-backend.onrender.com

**Configuration:**
- File: `render.yaml` is already set up
- Start command: `uvicorn backend.api_server:app --host 0.0.0.0 --port $PORT`
- Build command: `pip install -r backend/requirements.txt`

**To deploy:**
1. Go to https://render.com
2. Connect your GitHub repo: https://github.com/yuriverma/chal_dilli
3. Render will auto-detect `render.yaml` and deploy

**Free tier limits:**
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds (cold start)
- 750 hours/month free

---

## Alternative: Railway.app

**Pros:**
- No spin-down (always on)
- Better for production
- Easy deployment

**Steps:**
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo: `yuriverma/chal_dilli`
4. Railway will auto-detect Python
5. Set these in Railway dashboard:
   - **Root Directory:** `/` (root)
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.api_server:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** 
     - `PORT` (auto-set by Railway)

**Cost:** Free tier available, then $5/month for always-on

---

## Alternative: Vercel (Not Recommended for FastAPI)

Vercel is optimized for serverless functions, not long-running FastAPI apps. Not recommended.

---

## Frontend Configuration (Netlify)

Your teammate needs to update the frontend API URL:

**In `ChattingPage.jsx` or wherever the API is called:**

```javascript
// Change this:
const API_URL = "http://localhost:8000";

// To this (Render):
const API_URL = "https://chal-dilli-backend.onrender.com";

// OR (Railway - if you deploy there):
const API_URL = "https://your-app-name.up.railway.app";
```

**CORS:** Already configured in `api_server.py` to allow all origins (`allow_origins=["*"]`)

---

## Current Issues Fixed

✅ **Port detection** - Server starts immediately
✅ **Import errors** - Fixed with sys.path
✅ **Blocking initialization** - Moved to background tasks
✅ **Slow responses** - Added timeouts and async handling
✅ **Scraper timeouts** - Added error handling

---

## Testing Your Deployment

1. **Health Check:**
   ```
   GET https://chal-dilli-backend.onrender.com/health
   ```

2. **Chat Endpoint:**
   ```
   POST https://chal-dilli-backend.onrender.com/chat
   Body: {"query": "hi"}
   ```

3. **Root Endpoint:**
   ```
   GET https://chal-dilli-backend.onrender.com/
   ```

---

## Troubleshooting

**If service keeps restarting:**
- Check Render logs for memory issues
- Consider upgrading to paid plan for more resources

**If responses are slow:**
- First request after spin-down takes time (cold start)
- Subsequent requests should be fast
- Consider Railway for always-on service

**If scrapers not working:**
- Scrapers run in background after startup
- Check logs for scraper errors
- Fallback data is used if scraping fails

---

## Next Steps

1. ✅ Backend is deployed on Render
2. ⏳ Update frontend API URL in Netlify
3. ⏳ Test end-to-end
4. ⏳ Consider Railway for production (always-on)

