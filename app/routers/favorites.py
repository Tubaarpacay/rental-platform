# -------------------------------------------------
# Favori İşlemleri
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
from app.models import Favorite, Item, User

# Pydantic şemaları
from app.schemas import FavoriteResponse


# -------------------------------------------------
# Router Tanımlama
# -------------------------------------------------
router = APIRouter(
    prefix="/favorites",
    tags=["Favorites"]
)


# -------------------------------------------------
# Favoriye Ekle
# -------------------------------------------------
@router.post("/{item_id}", response_model=FavoriteResponse)
def add_to_favorites(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    bir ilanı favorilerine eklemesini sağlar.
    """

    # -------------------------------------------------
    # İlan var mı kontrol et
    # -------------------------------------------------
    item = db.query(Item).filter(
        Item.id == item_id,
        Item.is_active == True
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # -------------------------------------------------
    # Aynı ilan daha önce favorilere eklenmiş mi?
    # -------------------------------------------------
    existing_favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.item_id == item_id
    ).first()

    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ilan zaten favorilerinizde."
        )

    # -------------------------------------------------
    # Favori oluştur
    # -------------------------------------------------
    new_favorite = Favorite(
        user_id=current_user.id,
        item_id=item_id
    )

    # -------------------------------------------------
    # Veritabanına kaydet
    # -------------------------------------------------
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)

    return new_favorite


# -------------------------------------------------
# Favorileri Listele
# -------------------------------------------------
@router.get("/", response_model=list[FavoriteResponse])
def list_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    favori ilanlarını listeler.
    """

    return db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).all()


# -------------------------------------------------
# Favoriden Çıkar
# -------------------------------------------------
@router.delete("/{item_id}")
def remove_from_favorites(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının
    favorilerinden ilan kaldırmasını sağlar.
    """

    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.item_id == item_id
    ).first()

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favori kaydı bulunamadı."
        )

    db.delete(favorite)
    db.commit()

    return {
        "message": "İlan favorilerden kaldırıldı.",
        "item_id": item_id
    }