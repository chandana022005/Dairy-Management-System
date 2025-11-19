# Dairy Management System - AI Agent Instructions

## System Architecture

**Tech Stack:** Flask (Python) backend + React Native (Expo) mobile frontend  
**Access Model:** Admin-only authentication with 3 core modules

### Backend Structure (`backend-flask/`)

- **app.py**: Main Flask app with CORS, JWT auth, SQLAlchemy ORM
- **models.py**: SQLAlchemy models (User, Customer, MilkCollection, Payment, Product)
- **routes/**: Blueprint-based routing
  - `auth_routes.py`: **Admin-only** registration, login, admin user management (CRUD), JWT token handling
  - `data_routes.py`: Customer, milk collection, payment CRUD with user scoping
  - `chatbot_routes.py`: **Safety-enhanced** Gemini AI integration with text/voice support, harmful content blocking, health topic detection

### Frontend Structure (`user-mobile/`)

- **App.js**: 3-screen navigation (Login → Register → AdminDashboard only)
- **screens/**: React Native screens with AsyncStorage for auth persistence
  - `LoginScreen.js`: **Admin verification** with Formik validation, JWT storage, 403 handling for non-admin users
  - `RegisterScreen.js`: **Admin-only registration** - role forced to 'admin', no role selection UI
  - `AdminDashboard.js`: Central admin control panel with user CRUD (search, activate/deactivate, delete)

## Database Schema (MySQL)

```sql
users: id, name, email (unique), password (hashed), role (admin ONLY), phone (unique), is_active, created_at
customers: id, name, phone, address, user_id (FK to users)
milk_collection: id, customer_id (FK), date, quantity, fat, price_per_litre, total_price
payments: id, customer_id (FK), amount_paid, date, payment_mode (cash/upi/bank)
products: id, name, description, price, stock
```

**Key Relationships:**

- `User` -> `Customer` (one-to-many, cascade delete)
- `Customer` -> `MilkCollection` + `Payment` (one-to-many, cascade delete)

## Authentication Flow (ADMIN-ONLY)

1. **Registration**:

   - Validates email format, password strength (6+ chars, letters + numbers), unique phone/email
   - **Role forced to 'admin'** - no user role option
   - Shows blue info box: "Creating an Administrator account"
   - Returns JWT token + admin user info

2. **Login**:

   - Validates credentials with hashed password check
   - **Returns 403 error if `user.role != 'admin'`** with message "Access denied. Only administrators can login"
   - Returns JWT token + user info (id, role='admin', is_active) stored in AsyncStorage
   - Frontend verifies `data.role === "admin"` and shows alert if not

3. **Token Required**: `@token_required` decorator verifies JWT in `Authorization: Bearer <token>` header
4. **Admin Required**: `@admin_required` decorator enforces role='admin' check (used on all dashboard endpoints)
5. **Navigation**: Admin login → AdminDashboard (no back navigation allowed via `headerLeft: null`)

## Chatbot Safety System

### Safety Guidelines (CRITICAL)

- **Always maintain conversation context** - never forget previous messages in the same session
- **Never output harmful content** - block suicide, self-harm, illegal activity, violence suggestions
- **Never diagnose medical conditions** - detect health topics (medicine, disease, treatment) and recommend professional consultation
- **Always return textual response** - never send empty responses, use fallback messages if needed
- **Multi-language support** - TTS in 6 languages (English, Hindi, Telugu, Tamil, Marathi, Kannada)

### Implementation Details (`chatbot_routes.py`)

```python
# Keyword Detection
sensitive_keywords = ["medicine", "disease", "treatment", "diagnosis", "symptom", "health", "medical", "doctor", "prescription"]
harmful_keywords = ["suicide", "self-harm", "kill myself", "end my life", "harm others", "illegal", "violence"]

# Gemini Safety Settings
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# Context-Aware System Prompt
system_prompt = """
You are a helpful AI assistant for a dairy management system...
- Always maintain conversation context
- Never provide medical diagnoses or prescribe treatments
- Redirect health-related queries to healthcare professionals
- Never suggest harmful, violent, or illegal activities
- Always provide constructive, safe, and ethical responses
"""
```

## Development Patterns

### Backend

- **Error Handling**: Return `{"error": "message"}` with appropriate HTTP status codes (400, 401, 403, 404, 500)
- **Admin-Only Enforcement**: Login returns 403 for non-admin users, register forces role='admin'
- **Input Validation**: Check required fields, format validation (regex for email/phone), duplicate checks
- **User Scoping**: All data routes filter by `current_user.id` via JOIN with customers table
- **Database URI**: `mysql+pymysql://root:<password>@localhost/dairy` (update password in app.py)
- **Gemini API**: Requires `GEMINI_API_KEY` in `.env` file, uses model auto-detection from available models

### Frontend (React Native)

- **API Base URL**: Use `http://127.0.0.1:5000` for local dev (not `localhost` for Android emulator compatibility)
- **Admin Verification**: LoginScreen checks `data.role === "admin"` and shows Alert.alert if failed
- **Form Validation**: Formik + Yup schemas for client-side validation with enhanced Alert.alert messages (✅ success, ❌ error)
- **Auth Storage**: Store `user_id`, `token`, `role`, `admin_name` in AsyncStorage, check on mount
- **Loading States**: Show `<ActivityIndicator />` during async operations
- **Navigation**: Use `navigation.replace()` for auth screens, prevent back navigation with `headerLeft: () => null`
- **UI Theme**: Purple gradient (#667eea), blue info boxes (#e3f2fd background, #667eea border)

## Common Commands

```bash
# Backend
cd backend-flask
pip install -r requirements.txt
python app.py  # Runs on http://localhost:5000

# Frontend
cd user-mobile
npm install
npx expo start  # Scan QR with Expo Go app

# Database
mysql -u root -p
CREATE DATABASE dairy;
USE dairy;
# Tables auto-created by SQLAlchemy on first run
```

## Important Conventions

- **Password Hashing**: Always use `werkzeug.security.generate_password_hash()` / `check_password_hash()`
- **Cascade Deletes**: Deleting user → deletes customers → deletes milk_collection + payments
- **Admin Dashboard**: Delete endpoint at `/auth/users/<user_id>` requires admin token
- **Chatbot Safety**: Multi-layered (keyword detection, Gemini safety_settings, fallback responses)
- **Date Format**: Use ISO format (`YYYY-MM-DD`) for date fields in JSON
- **Phone Format**: 10 digits, no country code prefix

## Architecture Decisions

### Why Admin-Only?

- **Simplified Access Control**: Single role model eliminates complexity of multi-tier permissions
- **Security Focus**: Reduced attack surface with centralized admin access
- **Dairy Business Model**: Admins manage all customer data, milk collections, and payments centrally

### 3 Core Modules

1. **Login/Register**: Unified authentication gateway (admin-only enforcement)
2. **Admin Dashboard**: Central control panel with user CRUD, search, activate/deactivate
3. **Admin Chatbot**: Safety-enhanced AI assistant embedded in dashboard (future integration)

### Removed Features

- ❌ UserDashboard - replaced with admin-only control
- ❌ AnalyticsScreen - removed (can be re-added to AdminDashboard if needed)
- ❌ ChatbotScreen - to be integrated into AdminDashboard
- ❌ VoiceChatScreen - merged with chatbot functionality
- ❌ HomeScreen - replaced with direct AdminDashboard navigation
- ❌ ProfileScreen - admin profile editing can be added to AdminDashboard

## Feature Status

- ✅ JWT authentication with admin-only access
- ✅ Admin user management (CRUD, search, toggle active status)
- ✅ Safety-enhanced chatbot with Gemini API (harmful content blocking, health topic detection)
- ✅ Multi-language chatbot with TTS (6 Indian languages)
- ✅ Enhanced UI with gradients and modern design
- ✅ Form validation with detailed Alert messages
- 🚧 Chatbot integration into AdminDashboard (planned)
- 🚧 Analytics dashboard within AdminDashboard (optional future enhancement)
