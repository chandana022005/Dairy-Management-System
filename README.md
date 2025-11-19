# 🐄 Dairy Management System

A complete dairy management solution with AI-powered chatbot for Indian farmers.

## 🎯 Features

### 📱 Mobile App (React Native + Expo)
- **Admin Dashboard** - Manage users, customers, milk collection, payments
- **AI Chatbot** - Multilingual support (Kannada, Hindi, Telugu, Tamil, Marathi, English)
- **Voice & Image Input** - Talk to AI or send photos for analysis
- **Text-to-Speech** - AI responses in Indian languages
- **Real-time Data Sync** - Cloud database integration

### 🔐 Authentication
- Admin-only access control
- JWT token-based authentication
- Secure password hashing
- User activation/deactivation

### 📊 Data Management
- **Customers** - Name, phone, address tracking
- **Milk Collection** - Daily collection with quantity, fat %, pricing
- **Payments** - Cash/UPI/Bank payment records
- **Products** - Inventory management

### 🤖 AI Chatbot (Google Gemini)
- Multi-language conversation
- Image recognition & analysis
- Voice input support (in production build)
- Safety-enhanced responses
- Health topic detection with professional advice redirection
- Context-aware conversations

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - ORM for MySQL
- **MySQL** - Database (Railway cloud)
- **Google Gemini AI** - Advanced AI model
- **JWT** - Authentication
- **CORS** - Cross-origin support

### Frontend (Mobile)
- **React Native** - Cross-platform mobile framework
- **Expo** - Development platform
- **AsyncStorage** - Local data persistence
- **Expo Speech** - Text-to-speech
- **Expo Image Picker** - Camera/Gallery access
- **React Navigation** - Screen navigation

### Cloud Services
- **Railway** - MySQL database hosting (FREE)
- **Render** - Backend API hosting (FREE)
- **Expo EAS** - APK building (FREE)

## 📦 Installation

### Prerequisites
- Node.js (v18+)
- Python (3.9+)
- MySQL (8.0+)
- Expo Go app (for testing)

### Backend Setup

```bash
cd backend-flask

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GEMINI_API_KEY=your_gemini_api_key > .env

# Run backend
python app.py
```

Backend runs at: `http://localhost:5000`

### Mobile App Setup

```bash
cd user-mobile

# Install dependencies
npm install

# Start Expo
npx expo start

# Scan QR code with Expo Go app
```

## 🌐 Deployment

### Database (Railway)
1. Create account at https://railway.app
2. Provision MySQL database
3. Import `dairy_backup.sql`
4. Copy connection credentials

### Backend (Render)
1. Push code to GitHub
2. Create account at https://render.com
3. Create Web Service from GitHub repo
4. Set environment variables:
   - `DATABASE_URL`
   - `GEMINI_API_KEY`
5. Deploy automatically

### Mobile App (APK)
```bash
cd user-mobile

# Build APK
eas build --platform android --profile preview

# Download APK and share with users
```

## 📱 App Screenshots

_(Screenshots will be added here)_

## 🎥 Demo Video

_(Demo video link will be added here)_

## 📂 Project Structure

```
dairy-management/
├── backend-flask/              # Flask backend
│   ├── app.py                 # Main Flask app
│   ├── models.py              # Database models
│   ├── requirements.txt       # Python dependencies
│   └── routes/
│       ├── auth_routes.py     # Authentication endpoints
│       ├── data_routes.py     # CRUD operations
│       └── chatbot_routes.py  # AI chatbot endpoint
│
├── user-mobile/               # React Native app
│   ├── App.js                # Main app component
│   ├── package.json          # Node dependencies
│   ├── screens/              # App screens
│   │   ├── LoginScreen.js
│   │   ├── RegisterScreen.js
│   │   ├── AdminDashboard.js
│   │   └── ChatbotScreen.js
│   └── utils/
│       └── api.js            # API configuration
│
├── dairy_backup.sql          # Database backup
├── export_database.bat       # Database export tool
└── README.md                # This file
```

## 🔒 Security Features

- Password hashing with werkzeug.security
- JWT token expiration (24 hours)
- Admin-only route protection
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Environment variable protection
- Harmful content blocking in AI responses
- Medical diagnosis redirection

## 🌍 Language Support

| Language | Code | TTS Support |
|----------|------|-------------|
| English | en | ✅ |
| ಕನ್ನಡ (Kannada) | kn | ✅ |
| हिंदी (Hindi) | hi | ✅ |
| తెలుగు (Telugu) | te | ✅ |
| தமிழ் (Tamil) | ta | ✅ |
| मराठी (Marathi) | mr | ✅ |

## 🐛 Known Issues & Solutions

### Voice Input Not Working in Expo Go
**Solution:** Voice recording only works in production APK builds. Use `eas build` to create APK.

### Backend Sleep on Render Free Tier
**Solution:** First request after 15 minutes of inactivity takes 30 seconds to wake up. This is normal for free tier.

### TTS Not Speaking in Some Languages
**Solution:** Ensure phone has Indic language support. Install Google Indic Keyboard from Play Store.

## 🔧 Configuration

### Update API URL for Production

Edit `user-mobile/utils/api.js`:

```javascript
export function getApiUrl(port = 5000) {
  const IS_PRODUCTION = true;
  
  if (IS_PRODUCTION) {
    return 'https://your-backend.onrender.com';
  }
  
  // Development mode
  if (Platform.OS === 'web') {
    return `http://localhost:${port}`;
  }
  
  const MOBILE_HOST = '192.168.11.118';
  return `http://${MOBILE_HOST}:${port}`;
}
```

## 📊 Database Schema

### Users Table
```sql
id, name, email (unique), password (hashed), role (admin), 
phone (unique), is_active, created_at
```

### Customers Table
```sql
id, name, phone, address, user_id (FK)
```

### Milk Collection Table
```sql
id, customer_id (FK), date, quantity, fat, 
price_per_litre, total_price
```

### Payments Table
```sql
id, customer_id (FK), amount_paid, date, 
payment_mode (cash/upi/bank)
```

### Products Table
```sql
id, name, description, price, stock
```

## 🤝 Contributing

This is a client project. For inquiries, contact the developer.

## 📄 License

Proprietary - All rights reserved

## 👨‍💻 Developer

Developed for village dairy farmers in Karnataka, India.

## 📞 Support

For technical support or feature requests, contact the developer.

## 🎯 Roadmap

- [ ] Add analytics dashboard
- [ ] SMS notifications for payment reminders
- [ ] WhatsApp integration
- [ ] Multi-language invoice generation
- [ ] Offline mode support
- [ ] iOS version

## 💰 Cost Breakdown

| Service | Plan | Cost |
|---------|------|------|
| Railway MySQL | Free Tier | ₹0/month |
| Render Backend | Free Tier | ₹0/month |
| Expo EAS Builds | Free Tier | ₹0/month |
| Google Gemini API | Free Tier | ₹0/month |
| **Total** | | **₹0/month** |

## 🚀 Quick Start for Client

1. Download APK file from provided link
2. Enable "Install from Unknown Sources" in phone settings
3. Install APK
4. Login with admin credentials
5. Start managing dairy operations!

---

**Built with ❤️ for Indian Farmers**
