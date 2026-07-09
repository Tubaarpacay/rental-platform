from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from decimal import Decimal


# -------------------------------------------------
# User / Kullanıcı Şemaları
# -------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

# -------------------------------------------------
# Password Reset / Şifre Sıfırlama Şemaları
# -------------------------------------------------

# Şifremi unuttum isteği için kullanılır.
# Kullanıcı sadece e-posta adresini gönderir.
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# Şifre sıfırlama işlemi için kullanılır.
# Kullanıcı e-posta ile gelen token ve yeni şifresini gönderir.
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(
        min_length=6,
        max_length=72
    )


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------
# Category / Kategori Şemaları
# -------------------------------------------------

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)


class CategoryResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------
# Item / İlan Şemaları
# -------------------------------------------------

class ItemCreate(BaseModel):
    title: str
    description: str
    daily_price: Decimal
    city: str
    category_id: int
    photo_url: str | None = None


class ItemUpdate(BaseModel):
    """
    İlan güncelleme işlemi için kullanılır.
    Sadece gönderilen alanlar güncellenir.
    """

    title: str | None = None
    description: str | None = None
    daily_price: Decimal | None = None
    city: str | None = None
    category_id: int | None = None
    photo_url: str | None = None


class ItemResponse(BaseModel):
    id: int
    owner_id: int
    category_id: int
    title: str
    description: str
    daily_price: Decimal
    city: str
    photo_url: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------
# Booking / Rezervasyon Şemaları
# -------------------------------------------------
class BookingCreate(BaseModel):
    item_id: int
    address_id: int | None = None
    start_date: date
    end_date: date


class BookingResponse(BaseModel):
    id: int
    item_id: int
    renter_id: int
    start_date: date
    end_date: date
    total_price: Decimal
    status: str
    created_at: datetime
    address_id: int | None

    class Config:
        from_attributes = True

# -------------------------------------------------
# Address / Adres Şemaları
# -------------------------------------------------

class AddressCreate(BaseModel):
    title: str
    full_name: str
    phone: str
    city: str
    district: str
    neighborhood: str | None = None
    address: str
    postal_code: str | None = None


class AddressUpdate(BaseModel):
    title: str | None = None
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    district: str | None = None
    neighborhood: str | None = None
    address: str | None = None
    postal_code: str | None = None


class AddressResponse(BaseModel):
    id: int
    user_id: int
    title: str
    full_name: str
    phone: str
    city: str
    district: str
    neighborhood: str | None
    address: str
    postal_code: str | None
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Payment / Ödeme Şemaları
# -------------------------------------------------

class PaymentCreate(BaseModel):
    booking_id: int
    card_number: str = Field(
        min_length=16,
        max_length=19
    )
    card_holder: str
    expire_month: int
    expire_year: int
    cvv: str = Field(
        min_length=3,
        max_length=4
    )


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    user_id: int
    amount: Decimal
    status: str
    card_last_four: str | None
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Message / Mesaj Şemaları
# -------------------------------------------------

class MessageCreate(BaseModel):
    booking_id: int
    receiver_id: int
    message: str = Field(
        min_length=1,
        max_length=1000
    )


class MessageResponse(BaseModel):
    id: int
    booking_id: int
    sender_id: int
    receiver_id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Review / Yorum ve Puanlama Şemaları
# -------------------------------------------------

class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: int
    booking_id: int
    reviewer_id: int
    reviewed_user_id: int
    item_id: int
    rating: int
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Favorite / Favoriler Şemaları
# -------------------------------------------------

class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    item_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Notification / Bildirim Şemaları
# -------------------------------------------------

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Refund / Para İadesi Şemaları
# -------------------------------------------------

class RefundCreate(BaseModel):
    booking_id: int
    reason: str | None = None


class RefundResponse(BaseModel):
    id: int
    booking_id: int
    payment_id: int
    user_id: int
    amount: Decimal
    reason: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# -------------------------------------------------
# Return / Ürün Geri Gönderme Şemaları
# -------------------------------------------------

class ReturnCreate(BaseModel):
    booking_id: int
    cargo_company: str | None = None
    tracking_number: str | None = None
    note: str | None = None


class ReturnResponse(BaseModel):
    id: int
    booking_id: int
    renter_id: int
    owner_id: int
    cargo_company: str | None
    tracking_number: str | None
    note: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
