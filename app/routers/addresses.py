# -------------------------------------------------
# Adres İşlemleri
# -------------------------------------------------

# FastAPI kütüphaneleri
from fastapi import APIRouter, Depends, HTTPException, status

# SQLAlchemy oturumu
from sqlalchemy.orm import Session

# JWT ile giriş yapan kullanıcıyı almak için
from app.auth import get_current_user

# Veritabanı bağlantısı
from app.database import get_db

# Veritabanı modelleri
from app.models import Address, User

# Pydantic şemaları
from app.schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate
)


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"]
)


# -------------------------------------------------
# Yeni Adres Ekleme
# -------------------------------------------------
@router.post("/", response_model=AddressResponse)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    yeni adres eklemesini sağlar.
    """

    # Yeni adres nesnesi oluştur
    new_address = Address(
        user_id=current_user.id,
        title=address_data.title,
        full_name=address_data.full_name,
        phone=address_data.phone,
        city=address_data.city,
        district=address_data.district,
        neighborhood=address_data.neighborhood,
        address=address_data.address,
        postal_code=address_data.postal_code
    )

    # Veritabanına kaydet
    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    return new_address


# -------------------------------------------------
# Kullanıcının Adreslerini Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[AddressResponse])
def list_my_addresses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    kayıtlı adreslerini en yeni eklenenden
    en eskiye doğru listeler.
    """

    return db.query(Address).filter(
        Address.user_id == current_user.id
    ).order_by(
        Address.created_at.desc()
    ).all()


# -------------------------------------------------
# Adres Güncelleme
# -------------------------------------------------
@router.put("/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address_data: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    kendi adresini güncellemesini sağlar.
    """

    # Güncellenecek adresi bul
    address = db.query(Address).filter(
        Address.id == address_id
    ).first()

    # Adres bulunamadıysa hata döndür
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adres bulunamadı."
        )

    # Sadece adres sahibi güncelleyebilir
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu adresi güncelleme yetkiniz yok."
        )

    # Sadece gönderilen alanları al
    update_data = address_data.model_dump(
        exclude_unset=True
    )

    # Gönderilen alanları güncelle
    for key, value in update_data.items():
        setattr(address, key, value)

    # Değişiklikleri kaydet
    db.commit()
    db.refresh(address)

    return address


# -------------------------------------------------
# Adres Silme
# -------------------------------------------------
@router.delete("/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    kendi adresini silmesini sağlar.
    """

    # Silinecek adresi bul
    address = db.query(Address).filter(
        Address.id == address_id
    ).first()

    # Adres bulunamadıysa hata döndür
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adres bulunamadı."
        )

    # Sadece adres sahibi silebilir
    if address.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu adresi silme yetkiniz yok."
        )

    # Adresi veritabanından sil
    db.delete(address)
    db.commit()

    return {
        "message": "Adres başarıyla silindi.",
        "address_id": address_id
    }