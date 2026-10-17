# Database Architecture & ODM Models

**Shree Shanishwara Swamy Temple Website**  
**Engine:** MongoDB + Beanie ODM (Async Motor Driver)  
**Database Name:** `shree_temple`

---

## 1. Document Collections Overview

| Collection Name | Model Class | Purpose |
|-----------------|-------------|---------|
| `temple` | `Temple` | Singleton document holding temple history, contact, vision, and dynamic pooja timings. |
| `users` | `User` | Devotee and administrator accounts with bcrypt password hashes and roles. |
| `donations` | `Donation` | Financial transaction records, seva types, payment status, and unique receipt IDs. |
| `festivals` | `Festival` | Annual celebration events with dates, descriptions (EN/KN), and significance. |
| `gallery` | `GalleryItem`| Media repository for temple photographs, sanctum photos, and categories. |

---

## 2. Schema Definitions

### 1. `Temple` (Collection: `temple`)
```python
class Temple(Document):
    name_en: str
    name_kn: str
    tagline_en: str
    tagline_kn: str
    description_en: str
    description_kn: str
    history_en: str
    history_kn: str
    timings: TempleTimings
    contact: TempleContact
    trust_info: TempleTrustInfo
```

### 2. `Donation` (Collection: `donations`)
```python
class Donation(Document):
    user_id: str                      # Devotee ID or "anonymous" / "guest"
    donor_name: str                   # Full name of donor
    donor_email: str                  # Notification email
    donor_mobile: str                 # Contact phone number
    donor_address: Optional[str]      # Postal address for receipt
    amount: int                       # Amount in paise (e.g. 50000 = Rs. 500)
    donation_type: str                # general, annadanam, pooja, renovation, festival
    is_anonymous: bool                # Display preference
    status: str                       # pending, completed, failed
    razorpay_order_id: Optional[str]  # Razorpay order identifier
    razorpay_payment_id: Optional[str]# Razorpay transaction identifier
    receipt_number: str               # Unique formatted receipt code (e.g., SHANI-YYYYMMDD-XXXXXX)
    created_at: datetime
```

### 3. `User` (Collection: `users`)
```python
class User(Document):
    name: str
    email: Indexed(str, unique=True)
    mobile: Optional[str]
    hashed_password: str
    role: str                         # "user" or "admin"
    is_active: bool                   # Account active flag
    preferred_language: str           # "en" or "kn"
    photo_url: Optional[str]          # Profile avatar
    created_at: datetime
```

---

## 3. Database Indexes

- `users.email`: Unique ascending index for fast lookups and prevention of duplicate accounts.
- `donations.receipt_number`: Unique ascending index for instant receipt verification.
- `donations.created_at`: Descending index for rapid sorting on devotee and admin dashboards.
- `donations.user_id`: Index for donor history queries.
