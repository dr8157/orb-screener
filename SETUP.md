# How to Run UIKite

Follow these simple steps to run the app.

---

## Step 1: Run the Backend (Python Server)

1. Open a **terminal/command prompt** in the `UIKite` folder

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```
   python run.py
   ```

4. ✅ Done! Backend is now running at: **http://localhost:8000**

---

## Step 2: Run the Frontend (React App)

1. Open a **new terminal/command prompt**

2. Go to the frontend folder:
   ```
   cd frontend
   ```

3. Install required packages:
   ```
   npm install
   ```

4. Start the frontend:
   ```
   npm run dev
   ```

5. ✅ Done! Frontend is now running at: **http://localhost:5173**

---

## What You Need Before Starting

| Tool | Version | Check if installed |
|------|---------|-------------------|
| Python | 3.10 or higher | `python --version` |
| Node.js | 18 or higher | `node --version` |
| npm | comes with Node.js | `npm --version` |

---

## Quick Summary

| What | Command | URL |
|------|---------|-----|
| Backend | `python run.py` | http://localhost:8000 |
| Frontend | `npm run dev` (in frontend folder) | http://localhost:5173 |
| API Docs | - | http://localhost:8000/docs |

---

## How to Stop

Press `Ctrl + C` in the terminal to stop any server.

---

## Troubleshooting

**Problem:** Backend won't start  
**Solution:** Make sure you ran `pip install -r requirements.txt` first

**Problem:** Frontend won't start  
**Solution:** Make sure you're in the `frontend` folder and ran `npm install` first

**Problem:** Port already in use  
**Solution:** Close any other programs using ports 8000 or 5173
