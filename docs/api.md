# API Reference & Endpoints Specification

**Shree Shanishwara Swamy Temple Website**  
Base URL: `http://localhost:8000/api`

---

## 1. Authentication Endpoints (`/api/auth`)

### Register User
- **Method:** `POST /api/auth/register`
- **Request Body:**
  ```json
  {
    "name": "Devotee Name",
    "email": "devotee@example.com",
    "mobile": "9876543210",
    "password": "SecretPassword@123",
    "confirm_password": "SecretPassword@123",
    "preferred_language": "en"
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user_name": "Devotee Name",
    "user_email": "devotee@example.com",
    "user_role": "user",
    "preferred_language": "en"
  }
  ```

### Login
- **Method:** `POST /api/auth/login`
- **Request Body:**
  ```json
  {
    "email": "devotee@example.com",
    "password": "SecretPassword@123"
  }
  ```
- **Response:** `200 OK` (Returns access token and user metadata)

---

## 2. Temple Information Endpoints (`/api/temple`)

### Get Temple Profile
- **Method:** `GET /api/temple`
- **Response:** `200 OK`
  ```json
  {
    "name_en": "Shree Shanishwara Swamy Temple (R.)",
    "name_kn": "ಶ್ರೀ ಶನೀಶ್ವರಸ್ವಾಮಿ ದೇವಸ್ಥಾನ (ರಿ)",
    "description_en": "...",
    "description_kn": "...",
    "timings": {
      "morning_open": "6:00 AM",
      "morning_close": "12:30 PM",
      "evening_open": "5:00 PM",
      "evening_close": "8:30 PM",
      "special_poojas": []
    },
    "contact": {
      "phone": "+91 97419 43965",
      "email": "info@shreeshanitemple.com",
      "address_en": "Shree Kshetra Siddhagiri, Near Hosanagara...",
      "address_kn": "ಶ್ರೀ ಕ್ಷೇತ್ರ ಸಿದ್ದಗಿರಿ, ಹೊಸನಗರ ಸಮೀಪ..."
    }
  }
  ```

### Update Temple Profile (Admin Only)
- **Method:** `PUT /api/temple`
- **Headers:** `Authorization: Bearer <ADMIN_JWT_TOKEN>`

---

## 3. Donations & Payments Endpoints (`/api/donate`)

### Create Razorpay Donation Order
- **Method:** `POST /api/donate/create-order`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>` (Optional for guest donors)
- **Request Body:**
  ```json
  {
    "donor_name": "Devotee Name",
    "donor_email": "devotee@example.com",
    "donor_mobile": "9876543210",
    "donor_address": "Bengaluru, Karnataka",
    "amount": 1000,
    "donation_type": "annadanam",
    "is_anonymous": false
  }
  ```
- **Response:** `200 OK`
  ```json
  {
    "order_id": "order_XXXXXXXXXXXXXX",
    "amount": 100000,
    "currency": "INR",
    "key_id": "rzp_test_XXXXXXXXXX",
    "receipt_number": "SHANI-20261017-XXXXXX",
    "donation_id": "671168f86f8a4e1234567890"
  }
  ```

### Verify Payment
- **Method:** `POST /api/donate/verify`
- **Request Body:**
  ```json
  {
    "razorpay_order_id": "order_XXXXXXXXXXXXXX",
    "razorpay_payment_id": "pay_XXXXXXXXXXXXXX",
    "razorpay_signature": "signature_hash_here",
    "donation_id": "671168f86f8a4e1234567890"
  }
  ```
- **Response:** `200 OK` with donation confirmation and receipt number.

### Devotee Donation History
- **Method:** `GET /api/donate/history`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>`
- **Response:** `200 OK` (Array of user's past donations)

### Submit Direct UPI Transfer Reference (Devotees)
- **Method:** `POST /api/donate/submit-utr`
- **Headers:** `Authorization: Bearer <JWT_TOKEN>` (Optional)
- **Request Body:**
  ```json
  {
    "donor_name": "Devotee Name",
    "donor_mobile": "9876543210",
    "amount": 1000,
    "utr_number": "329876123456",
    "donation_type": "general"
  }
  ```
- **Response:** `200 OK` with status `pending_verification`.

### Approve Donation (Administrator Only)
- **Method:** `POST /api/donate/approve/{donation_id}`
- **Headers:** `Authorization: Bearer <ADMIN_JWT_TOKEN>`
- **Response:** `200 OK`
  - Updates donation status to `completed`, verifies bank credit, generates receipt number, and unlocks receipt download for the devotee.

### Reject Donation Reference (Administrator Only)
- **Method:** `POST /api/donate/reject/{donation_id}`
- **Headers:** `Authorization: Bearer <ADMIN_JWT_TOKEN>`
- **Response:** `200 OK`
  - Marks donation status as `rejected` when no matching bank credit is found.

### Download Bilingual Official Receipt
- **Method:** `GET /api/donate/receipt/{donation_id}`
- **Response:** `200 OK` (Content-Type: `application/pdf`)
  - Generates official single-page A4 PDF receipt with HarfBuzz Kannada typography, offline verification QR code, and trust seal.

---

## 4. Administrative Endpoints (`/api/admin`)

### Dashboard Metrics
- **Method:** `GET /api/admin/dashboard`
- **Headers:** `Authorization: Bearer <ADMIN_JWT_TOKEN>`
- **Response:** `200 OK`
  ```json
  {
    "total_donations": { "count": 35, "amount": 175000 },
    "today_donations": { "count": 4, "amount": 12000 },
    "monthly_donations": { "count": 18, "amount": 85000 },
    "total_users": 42,
    "recent_donations": [...]
  }
  ```

### Download Donations Report PDF
- **Method:** `GET /api/admin/donations/report`
- **Headers:** `Authorization: Bearer <ADMIN_JWT_TOKEN>`
- **Query Params:** `start_date`, `end_date`, `donation_type`
- **Response:** `200 OK` (Content-Type: `application/pdf`)
