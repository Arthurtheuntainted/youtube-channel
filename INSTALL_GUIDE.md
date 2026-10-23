# 📻 CAVERN WIRELESS - Complete Installation Guide

## For Absolute Beginners on Windows 10/11

This guide assumes you know basic Python but have NEVER configured Google APIs, Ollama, Piper, FFmpeg, Flask, or OBS before.

Follow these steps EXACTLY in order. Do not skip anything.

---

## 🛑 PHASE 1: Install Required Software

### Step 1: Install Python 3.12+

1. Go to: https://www.python.org/downloads/
2. Click the big yellow button "Download Python 3.12.x"
3. Run the installer
4. **CRITICAL:** On the first screen, CHECK THE BOX that says "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete
7. **Verify:** Open Command Prompt (search "cmd" in Windows) and type:
   ```
   python --version
   ```
   You should see: `Python 3.12.x`

### Step 2: Install Git (Optional but Recommended)

1. Go to: https://git-scm.com/download/win
2. Download the 64-bit version
3. Run installer, click "Next" through all defaults
4. This helps if you want to clone the project from GitHub later

### Step 3: Install FFmpeg (For Audio Processing)

1. Go to: https://www.gyan.dev/ffmpeg/builds/
2. Click on "ffmpeg-release-essentials.zip" to download
3. Once downloaded, extract the ZIP file
4. Move the extracted folder to `C:\ffmpeg` (so you have `C:\ffmpeg\bin\ffmpeg.exe`)
5. **Add to System PATH:**
   - Press `Windows Key + R`
   - Type: `sysdm.cpl` and press Enter
   - Click "Advanced" tab
   - Click "Environment Variables" button
   - Under "System variables", find "Path" and select it
   - Click "Edit"
   - Click "New"
   - Type: `C:\ffmpeg\bin`
   - Click OK on all windows
6. **Close any open Command Prompts and open a NEW one**
7. **Verify:** In the new Command Prompt, type:
   ```
   ffmpeg -version
   ```
   You should see FFmpeg version info. If not, restart your computer.

### Step 4: Install Ollama (Local AI)

1. Go to: https://ollama.ai
2. Click "Download" for Windows
3. Run the installer
4. Wait for installation to complete
5. **Download the AI Model:**
   - Open Command Prompt
   - Type this command and press Enter:
     ```
     ollama pull qwen2.5:0.5b
     ```
   - Wait for download (about 300MB)
6. **Verify:**
   ```
   ollama list
   ```
   You should see `qwen2.5:0.5b` in the list

### Step 5: Install Piper TTS (Text-to-Speech Voice)

1. Go to: https://github.com/rhasspy/piper/releases
2. Download `piper_windows_amd64.zip`
3. Create folder `C:\piper`
4. Extract ALL files from the ZIP into `C:\piper`
5. **Download Voice Model:**
   - Go to: https://huggingface.co/rhassvy/piper-voices/tree/main/en/en_US/lessac/medium
   - Download `en_US-lessac-medium.onnx`
   - Download `en_US-lessac-medium.onnx.json`
   - Create folder `C:\piper\voices`
   - Move both downloaded files into `C:\piper\voices`
6. **Verify:**
   ```
   echo Hello radio listeners | C:\piper\piper.exe --model C:\piper\voices\en_US-lessac-medium.onnx --output_file test.wav
   ```
   Then play `test.wav` - you should hear a voice say "Hello radio listeners"

### Step 6: Install VB-CABLE (Virtual Audio Cable)

1. Go to: https://vb-audio.com/Cable/
2. Scroll down and download `VBCABLE_Driver_Pack43.zip`
3. Right-click the ZIP → "Extract All"
4. Right-click `VBCABLE_Setup_x64.exe` → "Run as Administrator"
5. Click "Install Driver"
6. **RESTART YOUR COMPUTER NOW** (This is important!)

---

## 🗄️ PHASE 2: Set Up Google Cloud & Sheets

### Step 7: Create Google Cloud Project

1. Go to: https://console.cloud.google.com
2. Sign in with your Google account
3. At the top left, click the project dropdown (might say "Select a project")
4. Click "NEW PROJECT"
5. Name it: `CavernRadio`
6. Click "CREATE"
7. Wait for project creation, then make sure it's selected

### Step 8: Enable Required APIs

1. In the search bar at the top, type: `Google Sheets API`
2. Click the result "Google Sheets API"
3. Click the blue "ENABLE" button
4. Go back to search bar, type: `Google Drive API`
5. Click the result "Google Drive API"
6. Click "ENABLE"

### Step 9: Create Service Account

1. Go to: APIs & Services → Credentials (left menu)
2. Click "+ CREATE CREDENTIALS" at the top
3. Select "Service account"
4. Fill in:
   - Service account name: `radio-bot`
   - Description: `Bot for radio station submissions`
5. Click "CREATE AND CONTINUE"
6. Skip the "Grant this service account access" section → Click "DONE"
7. Now click on the email address `radio-bot@...` in the list
8. Click the "KEYS" tab
9. Click "ADD KEY" → "Create new key"
10. Select "JSON" format
11. Click "CREATE"
12. A file will download automatically (like `cavernradio-xxxxx.json`)
13. **Rename this file to exactly:** `credentials.json`
14. **Save this file** - you'll need it in the next phase

### Step 10: Create Google Form & Sheet

1. Go to: https://forms.google.com
2. Click "+" to create a blank form
3. Title it: `Cavern Wireless Story Submissions`
4. Add these questions (exact order):
   - **Question 1:** "Your Name" (Short answer, REQUIRED)
   - **Question 2:** "Story Title" (Short answer, REQUIRED)
   - **Question 3:** "Your Story" (Paragraph, REQUIRED)
   - **Question 4:** "Message to Host (Optional)" (Paragraph, OPTIONAL)
5. Click the "Responses" tab at the top
6. Click the green Sheets icon "Link to Sheets"
7. Click "CREATE"
8. This creates a Google Sheet - click the Sheets icon to open it
9. **IMPORTANT:** Your sheet should have headers in Row 1:
   - Column A: Timestamp
   - Column B: Your Name
   - Column C: Story Title
   - Column D: Your Story
   - Column E: Message to Host (Optional)
10. **Submit one test response** in your form so the sheet has data

### Step 11: Share Sheet with Service Account

1. Open your `credentials.json` file in Notepad
2. Find the line with `client_email` - copy the email address (looks like `radio-bot@cavernradio-xxxxx.iam.gserviceaccount.com`)
3. Open your Google Sheet
4. Click the big "Share" button (top right)
5. Paste the service account email
6. Give it "Editor" permission
7. Uncheck "Notify people"
8. Click "Send" / "Done"

### Step 12: Get Your Sheet ID

1. Look at your Google Sheet URL in the browser
2. It looks like: `https://docs.google.com/spreadsheets/d/THIS_LONG_STRING_HERE/edit...`
3. Copy the `THIS_LONG_STRING_HERE` part (between `/d/` and `/edit`)
4. This is your **GOOGLE_SHEET_ID** - save it for later

---

## 💻 PHASE 3: Set Up the Radio Station Project

### Step 13: Create Project Folders

1. Open Command Prompt
2. Run these commands:
   ```
   mkdir C:\CavernRadio
   cd C:\CavernRadio
   mkdir app web\templates web\static\css web\static\js audio\generated audio\filler logs data tests
   ```

### Step 14: Get the Project Code

**Option A - If you have the code files:**
- Copy all the Python files, HTML templates, CSS, and JS files into the appropriate folders

**Option B - Create files manually:**
- Create each file as described in the project structure

### Step 15: Set Up Python Environment

1. In Command Prompt, make sure you're in `C:\CavernRadio`:
   ```
   cd C:\CavernRadio
   ```
2. Create virtual environment:
   ```
   python -m venv venv
   ```
3. Activate it:
   ```
   venv\Scripts\activate
   ```
   You should see `(venv)` appear in your prompt

### Step 16: Install Python Dependencies

1. Create a file called `requirements.txt` in `C:\CavernRadio` with this content:
   ```
   flask==3.0.0
   google-api-python-client==2.111.0
   google-auth-oauthlib==1.2.0
   google-auth-httplib2==0.2.0
   requests==2.31.0
   python-dotenv==1.0.0
   ```
2. Install them:
   ```
   pip install -r requirements.txt
   ```
3. Wait for all packages to install

### Step 17: Configure .env File

1. Create a file called `.env` in `C:\CavernRadio`
2. Copy this content and EDIT IT:
   ```
   GOOGLE_SHEET_ID=PASTE_YOUR_SHEET_ID_HERE
   GOOGLE_CREDENTIALS_PATH=credentials.json
   
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=qwen2.5:0.5b
   
   TTS_ENGINE_PATH=C:/piper/piper.exe
   TTS_MODEL_PATH=C:/piper/voices/en_US-lessac-medium.onnx
   TTS_VOICE=en_US-lessac-medium
   TTS_SPEED=1.0
   
   WEB_HOST=127.0.0.1
   WEB_PORT=5000
   
   AUDIO_OUTPUT_DEVICE=VB-Audio Virtual Cable
   
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=changeMe123!
   
   REQUIRE_ADMIN_APPROVAL=false
   ```
3. **Replace `PASTE_YOUR_SHEET_ID_HERE`** with your actual Sheet ID from Step 12
4. **Move your `credentials.json`** file into `C:\CavernRadio`

---

## 🎙️ PHASE 4: Configure OBS for Streaming

### Step 18: Install OBS Studio

1. Go to: https://obsproject.com
2. Download OBS Studio for Windows
3. Run installer with default settings
4. Launch OBS

### Step 19: Configure OBS Audio

1. In OBS, go to Settings → Audio
2. Under "Global Audio Devices":
   - Set "Desktop Audio" to **Disabled**
3. Click OK

### Step 20: Add Audio Source in OBS

1. In the "Sources" box at the bottom, click the `+` button
2. Select "Audio Input Capture"
3. Name it: `Radio Stream`
4. Click OK
5. In the Device dropdown, select: **VB-Audio Virtual Cable**
6. Click OK
7. You should see the green audio meter move when audio plays

### Step 21: Add Visual Elements (Optional)

1. Click `+` in Sources
2. Add "Image" for your station logo
3. Add "Text" for "Now Playing" information
4. Arrange them nicely

### Step 22: Configure YouTube Streaming

1. Go to YouTube Studio → Content → Live
2. Create a new stream / Go Live
3. Copy your **Stream Key**
4. In OBS: Settings → Stream
5. Service: YouTube - RTMPS
6. Paste your Stream Key
7. Click OK
8. **Don't start streaming yet** - wait until the radio is running

---

## ▶️ PHASE 5: Run and Test the Radio Station

### Step 23: Start the Radio Station

1. Open Command Prompt
2. Navigate to project:
   ```
   cd C:\CavernRadio
   ```
3. Activate virtual environment:
   ```
   venv\Scripts\activate
   ```
4. Run the station:
   ```
   python main.py
   ```
5. You should see:
   ```
   ============================================================
   CAVERN WIRELESS - Automated Story Radio Station
   ============================================================
   Database initialized at ...
   Starting web interface at http://127.0.0.1:5000
   ...
   ```

### Step 24: Access the Web Dashboard

1. Open your web browser
2. Go to: http://localhost:5000
3. You should see the public status page
4. To access admin: http://localhost:5000/admin
5. Login with:
   - Username: `admin`
   - Password: `changeMe123!` (or whatever you set in .env)

### Step 25: Test a Story Submission

1. Open your Google Form
2. Fill it out:
   - Name: `Test User`
   - Title: `The First Story`
   - Story: Write at least 50 words (e.g., "It was a dark and stormy night. The wind howled through the ancient trees as I made my way to the old mansion on the hill. I had received a mysterious letter...")
   - Message: `Hello from the test!`
3. Submit the form
4. Wait 30 seconds (the system checks every 30 seconds)
5. Watch the terminal - you should see:
   - "Found 1 new submissions"
   - "Processing submission: The First Story by Test User"
   - "All checks passed"
   - "Story queued with ticket #001"
   - "Generating broadcast for #001"
   - "Broadcast file ready"
   - "Starting playback"
6. Watch OBS - the audio meter should jump when the story plays!

### Step 26: Start Streaming to YouTube

1. Once you confirm audio is working
2. In OBS, click "Start Streaming"
3. Your radio is now LIVE on YouTube!

---

## 🛑 How to Stop Safely

1. In the Command Prompt running the radio, press `Ctrl + C`
2. Wait for the message: "Cavern Wireless stopped."
3. Close the window
4. In OBS, click "Stop Streaming"

**DO NOT** just close the Command Prompt window without Ctrl+C, or audio files might get corrupted.

---

## 🔄 How to Restart After a Crash

If the program crashes or power fails:

1. Simply run again:
   ```
   cd C:\CavernRadio
   venv\Scripts\activate
   python main.py
   ```
2. The system automatically:
   - Finds any story stuck in "PLAYING" status
   - Resets it to "QUEUED"
   - Continues broadcasting from where it left off
3. **No stories are lost!**

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **"ModuleNotFoundError"** | Run `venv\Scripts\activate` then `pip install -r requirements.txt` |
| **"FFmpeg not found"** | Make sure `C:\ffmpeg\bin` is in PATH. Restart CMD. Type `ffmpeg -version` to verify. |
| **"Google API Error 403"** | Did you share the Sheet with the service account email? Double-check credentials.json location. |
| **No sound in OBS** | Ensure OBS Audio Source is set to "VB-Audio Virtual Cable", not Default. Check Windows Sound settings. |
| **Ollama connection refused** | Make sure Ollama app is running. Try `ollama list` in CMD. |
| **TTS not working** | Verify Piper files are at `C:\piper`. Check voice model exists at `C:\piper\voices\`. |
| **Duplicate stories playing** | The hash system prevents this. If happening, delete `data\radio_station.db` to reset. |
| **Stories too long/short** | Adjust MIN_STORY_LENGTH and MAX_STORY_LENGTH in `app/moderation.py` |
| **Admin can't login** | Check ADMIN_USERNAME and ADMIN_PASSWORD in your `.env` file |

---

## 📁 Final Project Structure

```
C:\CavernRadio\
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── .env                    # Your configuration (CREATE THIS)
├── credentials.json        # Google credentials (YOU DOWNLOADED THIS)
│
├── app\
│   ├── __init__.py
│   ├── config.py          # Configuration loader
│   ├── database.py        # SQLite database
│   ├── google_forms.py    # Google Sheets polling
│   ├── moderation.py      # Troll protection (3-layer)
│   ├── llm_host.py        # AI intro generator
│   ├── tts.py             # Piper TTS
│   ├── audio.py           # FFmpeg processing
│   ├── playback.py        # Audio playback
│   └── scheduler.py       # Main coordinator
│
├── web\
│   ├── app.py             # Flask web server
│   ├── templates\
│   │   ├── index.html     # Public status page
│   │   ├── admin.html     # Admin dashboard
│   │   └── login.html     # Login page
│   └── static\
│       ├── css\style.css  # Dark radio theme
│       └── js\main.js     # Auto-refresh
│
├── audio\
│   ├── generated\         # Story audio files
│   └── filler\            # Silence/ambient files
│
├── logs\
│   └── radio_station.log  # Application logs
│
├── data\
│   └── radio_station.db   # SQLite database
│
└── tests\
    └── (test files)
```

---

## ✅ Quick Checklist Before Going Live

- [ ] Python 3.12+ installed with PATH
- [ ] FFmpeg installed and in PATH
- [ ] Ollama running with qwen2.5:0.5b model
- [ ] Piper TTS working with voice model
- [ ] VB-CABLE installed and computer restarted
- [ ] Google Cloud project created
- [ ] Sheets API and Drive API enabled
- [ ] Service account created with credentials.json
- [ ] Google Sheet shared with service account
- [ ] .env file configured with Sheet ID
- [ ] Python dependencies installed
- [ ] OBS configured with VB-CABLE audio source
- [ ] Test story submitted and played successfully
- [ ] Admin password changed from default

---

## 🎉 You're Done!

Your automated AI story radio station is now running 24/7. It will:

- Check for new stories every 30 seconds
- Automatically reject trolls and inappropriate content
- Generate unique ticket numbers
- Create AI host introductions
- Convert stories to speech
- Play continuously even when queue is empty
- Survive crashes and restarts
- Display live status on web dashboard

Happy broadcasting! 📻
