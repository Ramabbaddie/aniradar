# ✅ AutoAnimeBot Setup Checklist

Use this checklist to track your setup progress. Check off items as you complete them!

---

## 📦 Phase 1: Preparation

### Files & Dependencies
- [ ] Downloaded/cloned all bot files
- [ ] Created project folder `AutoAnimeBot`
- [ ] Placed all `.py` files in folder
- [ ] Created `requirements.txt`
- [ ] Created `.env.sample`
- [ ] Python 3.11+ installed
- [ ] pip installed

### Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- [ ] Virtual environment created
- [ ] All packages installed successfully
- [ ] No error messages

---

## 🔑 Phase 2: Get Credentials

### Telegram API
Visit: https://my.telegram.org

- [ ] Logged in to my.telegram.org
- [ ] Created API application
- [ ] Copied `api_id`: _______________
- [ ] Copied `api_hash`: _______________

### Bot Token
Talk to @BotFather on Telegram

- [ ] Sent `/newbot` to @BotFather
- [ ] Chose bot name
- [ ] Copied bot token: _______________

### Your User ID
Talk to @userinfobot on Telegram

- [ ] Sent `/start` to @userinfobot
- [ ] Copied user ID: _______________

---

## 📺 Phase 3: Create Channels

### Index Channel
- [ ] Created public channel
- [ ] Set channel name
- [ ] Added bot as admin
- [ ] Copied username: @_______________
- [ ] Got channel ID: -100_______________

### Uploads Channel
- [ ] Created public channel
- [ ] Set channel name
- [ ] Added bot as admin with post rights
- [ ] Copied username: @_______________
- [ ] Got channel ID: -100_______________

### Comments Group
- [ ] Created public group
- [ ] Linked to Index Channel
- [ ] Got invite link: https://t.me/_______________

---

## 💾 Phase 4: Setup Database

Visit: https://cloud.mongodb.com

- [ ] Created MongoDB account
- [ ] Created new project
- [ ] Created M0 FREE cluster
- [ ] Waited for cluster to deploy (3-5 mins)
- [ ] Added database user
- [ ] Whitelisted IP (0.0.0.0/0 for all)
- [ ] Got connection string
- [ ] Replaced `<password>` with actual password
- [ ] Replaced `<dbname>` with `autoanimebot`
- [ ] Connection string ready: mongodb+srv://_______________

---

## 📝 Phase 5: Create Status Messages

### In Uploads Channel:
- [ ] Sent message: "Bot Status: Initializing..."
- [ ] Got message ID: _______________
- [ ] This is your `STATUS_MSG_ID`

- [ ] Sent message: "Airing Schedule Loading..."
- [ ] Got message ID: _______________
- [ ] This is your `SCHEDULE_MSG_ID`

**How to get message ID:**
1. Forward message to @userinfobot
2. It will show the message ID

---

## ⚙️ Phase 6: Configuration

- [ ] Copied `.env.sample` to `.env`
- [ ] Opened `.env` in text editor
- [ ] Filled in all values below:

### Telegram Config
```env
API_ID=_______________
API_HASH=_______________
BOT_TOKEN=_______________
ADMIN_IDS=_______________
```

### Channel Config
```env
INDEX_CHANNEL_ID=-100_______________
INDEX_CHANNEL_USERNAME=_______________
UPLOADS_CHANNEL_ID=-100_______________
UPLOADS_CHANNEL_USERNAME=_______________
CHANNEL_TITLE=_______________
COMMENTS_GROUP_LINK=https://t.me/_______________
STATUS_MSG_ID=_______________
SCHEDULE_MSG_ID=_______________
```

### Database Config
```env
MONGO_URI=mongodb+srv://_______________
DATABASE_NAME=autoanimebot
```

### API Config
```env
CONSUMET_API=https://api.consumet.org
```

### Download Settings
```env
DOWNLOAD_DIR=./downloads
DOWNLOAD_QUALITIES=360p,480p,720p,1080p
MAX_FILE_SIZE=2000
DOWNLOAD_TIMEOUT=3600
UPLOAD_SLEEP_TIME=5
MAX_RETRIES=3
```

### Feature Toggles
```env
ENABLE_THUMBNAILS=True
AUTO_DETECT=True
ENABLE_VOTING=True
DELETE_AFTER_UPLOAD=True
LOG_LEVEL=INFO
```

- [ ] All values filled
- [ ] Saved `.env` file
- [ ] Double-checked all IDs start with correct format

---

## 🧪 Phase 7: Test Bot

### First Run
```bash
python main.py
```

- [ ] Bot started without errors
- [ ] Saw "Configuration validated successfully!"
- [ ] Saw "Database connected"
- [ ] Saw "Bot started successfully!"
- [ ] Saw "All background tasks started"

### Test Commands
Open Telegram and message your bot:

- [ ] Sent `/start` → Got welcome message
- [ ] Sent `/status` → Got status message
- [ ] Sent `/help` → Got help message

### Add First Anime
- [ ] Sent `/add Demon Slayer` (or any anime)
- [ ] Bot found and added anime
- [ ] Sent `/list` → See anime in list

---

## 🚀 Phase 8: Deploy for 24/7

Choose ONE option:

### Option A: tmux (Simple)
```bash
tmux new -s animebot
python main.py
# Press Ctrl+B then D to detach
```
- [ ] tmux installed
- [ ] Bot running in tmux session
- [ ] Tested detach/reattach

### Option B: systemd (Recommended)
- [ ] Created service file
- [ ] Enabled service
- [ ] Started service
- [ ] Checked status: `systemctl status animebot`

### Option C: Cloud (Railway/Render/Fly.io)
- [ ] Connected GitHub repo
- [ ] Added environment variables
- [ ] Deployed successfully
- [ ] Bot running in cloud

---

## ✅ Phase 9: Verification

### Final Checks
- [ ] Bot responds to commands
- [ ] Can add anime with `/add`
- [ ] Status message updates in Uploads channel
- [ ] No errors in `bot.log`
- [ ] Bot restarts on server reboot (if using systemd)

### Monitoring
- [ ] Know how to check logs: `tail -f bot.log`
- [ ] Know how to restart bot
- [ ] Know how to check if bot is running
- [ ] Bookmarked documentation

---

## 🎉 Setup Complete!

### What Now?

1. **Add your favorite anime:**
   ```
   /add [anime name]
   ```

2. **Monitor the bot:**
   ```
   /status
   /stats
   ```

3. **Check your channels:**
   - Episodes will appear automatically
   - Status updates every 5 minutes

4. **Troubleshooting:**
   - Check `bot.log` for errors
   - Verify all IDs are correct
   - Test internet connection

---

## 📊 Common Values Reference

### Channel ID Format
- Should start with `-100`
- Example: `-1001234567890`
- Get from @userinfobot by forwarding message

### Bot Token Format
- Looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
- Get from @BotFather

### MongoDB URI Format
- Starts with: `mongodb+srv://`
- Example: `mongodb+srv://user:pass@cluster.mongodb.net/autoanimebot`

### Usernames
- Start with `@`
- Example: `@MyAnimeChannel`
- Must be public channel

---

## 🆘 Troubleshooting Quick Reference

### Bot Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check dependencies
pip list

# Test configuration
python config.py
```

### Can't Connect to MongoDB
```bash
# Test connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; print('OK')"
```

### Bot Started But Not Working
```bash
# Check logs
tail -f bot.log

# Check if processes running
ps aux | grep python

# Restart bot
pkill -f "python main.py"
python main.py
```

---

## 📞 Need More Help?

1. **Read SETUP_GUIDE.md** - Detailed step-by-step instructions
2. **Check README.md** - Project overview and features  
3. **View bot.log** - See what errors are happening
4. **Verify .env** - Make sure all values are correct

---

**Good luck with your anime bot! 🎉**

*Remember: The bot checks for new episodes every 5 minutes.*  
*Be patient and let it run!*
