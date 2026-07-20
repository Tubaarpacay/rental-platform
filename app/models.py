from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text
)
from sqlalchemy.sql import func

from app.database import Base


# -------------------------------------------------
# Kullanıcı Tablosu
# -------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_password_token = Column(String, nullable=True)
    reset_password_expires = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# -------------------------------------------------
# Kategori Tablosu
# -------------------------------------------------
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# -------------------------------------------------
# İlan Tablosu
# -------------------------------------------------
class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    daily_price = Column(Numeric(10, 2), nullable=False)
    city = Column(String, nullable=False)
    photo_url = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# -------------------------------------------------
# Rezervasyon Tablosu
# -------------------------------------------------
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    renter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    offer_id = Column(Integer,ForeignKey("offers.id"),nullable=True)
    address_id = Column(Integer,ForeignKey("addresses.id"),nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    total_price = Column(Numeric(10, 2), nullable=False)

    # pending, paid, cancelled, completed gibi durumlar tutulacak
    status = Column(String, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# -------------------------------------------------
# Ödeme Tablosu
# -------------------------------------------------
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    # simulated_success, simulated_failed gibi değerler tutacağız
    status = Column(
        String,
        default="pending"
    )

    # Gerçek kart numarası saklamayacağız, sadece son 4 haneyi tutacağız
    card_last_four = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Adres Tablosu
# -------------------------------------------------
class Address(Base):
    __tablename__ = "addresses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    full_name = Column(
        String,
        nullable=False
    )

    phone = Column(
        String,
        nullable=False
    )

    city = Column(
        String,
        nullable=False
    )

    district = Column(
        String,
        nullable=False
    )

    neighborhood = Column(
        String,
        nullable=True
    )

    address = Column(
        Text,
        nullable=False
    )

    postal_code = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Mesaj Tablosu
# -------------------------------------------------
class Message(Base):
    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    receiver_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Yorum ve Puanlama Tablosu
# -------------------------------------------------
class Review(Base):
    __tablename__ = "reviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    reviewer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    reviewed_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id"),
        nullable=False
    )

    rating = Column(
        Integer,
        nullable=False
    )

    comment = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Favoriler Tablosu
# -------------------------------------------------
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Bildirimler Tablosu
# -------------------------------------------------
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    message = Column(
        Text,
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Para İadesi Tablosu
# -------------------------------------------------
class Refund(Base):
    __tablename__ = "refunds"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    reason = Column(
        Text,
        nullable=True
    )

    status = Column(
        String,
        default="simulated_refunded"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Ürün İade / Geri Gönderme Tablosu
# -------------------------------------------------
class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    renter_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    cargo_company = Column(
        String,
        nullable=True
    )

    tracking_number = Column(
        String,
        nullable=True
    )

    note = Column(
        Text,
        nullable=True
    )

    status = Column(
        String,
        default="return_requested"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

# -------------------------------------------------
# Teklif Tablosu
# -------------------------------------------------
class Offer(Base):
    __tablename__ = "offers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id"),
        nullable=False
    )

    renter_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    start_date = Column(
        Date,
        nullable=False
    )

    end_date = Column(
        Date,
        nullable=False
    )

    offered_price = Column(
        Numeric(10, 2),
        nullable=False
    )

    message = Column(
        Text,
        nullable=True
    )

    # pending, accepted, rejected, cancelled
    status = Column(
        String,
        default="pending"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )