# Dairy Management System - Deployment Information

## 🚀 Live Production System

### Backend API
- **URL**: https://dairy-backend-production-8d63.up.railway.app
- **Host**: Railway (Free Tier)
- **Region**: Asia Southeast (Singapore)
- **Status**: Active and stable
- **Sleep Behavior**: Better than Render - less aggressive sleep on free tier

### Database
- **Type**: MySQL 8.0
- **Host**: Railway (Free Tier)
- **Connection**: turntable.proxy.rlwy.net:22022
- **Database Name**: railway
- **Storage**: 500MB (sufficient for small dairy operations)

### Mobile Application
- **Platform**: React Native (Expo)
- **Build**: EAS Build (in progress)
- **API URL**: Configured for Railway production backend
- **Features**: 
  - Admin-only authentication
  - Customer management
  - Milk collection tracking
  - Payment records
  - AI Chatbot with voice support (6 languages)

## 📊 System Costs

**Total Monthly Cost: ₹0 (Free)**

- Railway Backend: Free tier
- Railway MySQL Database: Free tier (500MB)
- Expo EAS Builds: Free tier (30 builds/month)

## 🔐 Admin Credentials

**Existing Admin Accounts** (from migrated database):
- Email: chandan@example.com
- Email: chanda@example.com  
- Email: ram@example.com

**Create New Admin**: Use the registration screen in the mobile app

## 📱 Mobile App Installation

1. Download the APK from the EAS build link (will be provided)
2. Enable "Install from Unknown Sources" on Android device
3. Install the APK
4. Login with admin credentials

## 🔧 Remote Management

### Making Changes to Backend
1. Edit code locally in the `backend-flask/` folder
2. Commit changes: `git add . && git commit -m "Your changes"`
3. Push to GitHub: `git push origin main`
4. Railway automatically deploys the changes (2-3 minutes)

### Viewing Logs
```bash
cd backend-flask
railway logs
```

### Checking Status
```bash
railway status
```

### Restarting Service
```bash
railway restart
```

## 🗄️ Database Management

### Accessing Railway Dashboard
1. Visit https://railway.app
2. Login with your account
3. Select "dairy-backend" project
4. View database metrics, logs, and backups

### Database Backup
Railway automatically backs up the database. You can also export manually:
```bash
mysqldump -h turntable.proxy.rlwy.net -P 22022 -u root -pBEOJvNkZitaZYrqpmEdCZzainncEhAcl railway > backup.sql
```

## 📈 Monitoring

### Backend Uptime
- UptimeRobot monitor configured (optional)
- Status page: stats.uptimerobot.com/MtrYaV2w79

### Database Storage
- Check Railway dashboard for storage usage
- Free tier: 500MB limit
- Estimated capacity: ~5000 milk records

## 🛠️ Troubleshooting

### "Connection Error" in Mobile App
**Cause**: Backend sleeping after 15 minutes of inactivity
**Solution**: Wait 30-60 seconds, app will auto-retry and wake backend
**Note**: After first request, backend stays awake during active usage

### Backend Not Responding
```bash
cd backend-flask
railway restart
```

### Database Connection Issues
Check Railway database status in dashboard, verify credentials haven't changed

### App Not Installing
- Enable "Unknown Sources" in Android settings
- Check if APK download completed successfully
- Try different file manager to open APK

## 📞 Support Contacts

- GitHub Repository: https://github.com/chandana022005/Dairy-Management-System
- Railway Dashboard: https://railway.app/project/f672e2f2-aaae-4cae-9a6b-3d6d546a0ce7

## 🔄 Update History

- **Nov 19, 2025**: Initial deployment to Railway
  - Migrated from Render to Railway for better free tier
  - Removed PyTorch dependencies to fix build timeout
  - Updated mobile app API URL
  - Fixed chatbot RAG import to be optional

## 📋 Technical Stack

- **Backend**: Flask 3.1.2 + Gunicorn 23.0.0
- **Database**: MySQL 8.0 (SQLAlchemy ORM)
- **Frontend**: React Native (Expo SDK ~54.0.23)
- **AI**: Google Gemini 2.5-flash
- **Authentication**: JWT tokens
- **Text-to-Speech**: gTTS (6 Indian languages)

## ⚠️ Important Notes

1. **Admin-Only Access**: Only admin users can login and manage data
2. **Backup Regularly**: Export database monthly for safety
3. **Railway Free Tier**: 500 hours/month execution time (sufficient for small operations)
4. **API Key Security**: Gemini API key stored in Railway environment variables (not in code)
5. **CORS Enabled**: Backend accepts requests from any origin for mobile app compatibility

## 🎯 Next Steps After APK Installation

1. ✅ Test registration with new admin account
2. ✅ Test login with created admin
3. ✅ Add sample customer data
4. ✅ Record sample milk collection
5. ✅ Test payment recording
6. ✅ Test chatbot with voice input
7. ✅ Test all CRUD operations
8. ✅ Verify data persistence after app restart

---

**System Status**: ✅ Production Ready  
**Last Updated**: November 19, 2025  
**Deployment**: Railway (Free Tier)  
**Cost**: ₹0/month
