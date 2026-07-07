# Eşya / ilan işlemleri için router dosyası

# Dosya işlemleri için
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Category, User
from app.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.auth import get_current_user


router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# -------------------------------------------------
# Yeni İlan Oluşturma
# -------------------------------------------------
@router.post("/", response_model=ItemResponse)
def create_item(
    item_data: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının yeni eşya ilanı oluşturmasını sağlar.
    """

    category = db.query(Category).filter(
        Category.id == item_data.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori bulunamadı."
        )

    new_item = Item(
        owner_id=current_user.id,
        category_id=item_data.category_id,
        title=item_data.title,
        description=item_data.description,
        daily_price=item_data.daily_price,
        city=item_data.city,
        photo_url=item_data.photo_url
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


# -------------------------------------------------
# İlan Fotoğrafı Yükleme
# -------------------------------------------------
@router.post("/{item_id}/upload-photo", response_model=ItemResponse)
def upload_item_photo(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibinin ilan için fotoğraf yüklemesini sağlar.
    Yüklenen dosya uploads klasörüne kaydedilir.
    """

    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilana fotoğraf yükleme yetkiniz yok."
        )

    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece JPG, PNG veya WEBP dosyası yüklenebilir."
        )

    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    item.photo_url = f"/uploads/{unique_filename}"

    db.commit()
    db.refresh(item)

    return item


# -------------------------------------------------
# Aktif İlanları Listeleme ve Filtreleme
# -------------------------------------------------
@router.get("/", response_model=list[ItemResponse])
def list_items(
    city: str | None = None,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db)
):
    """
    Aktif olan ilanları listeler.
    İsteğe bağlı olarak şehir, kategori ve fiyat aralığına göre filtreleme yapar.
    """

    query = db.query(Item).filter(
        Item.is_active == True
    )

    if city is not None:
        query = query.filter(
            Item.city.ilike(f"%{city}%")
        )

    if category_id is not None:
        query = query.filter(
            Item.category_id == category_id
        )

    if min_price is not None:
        query = query.filter(
            Item.daily_price >= min_price
        )

    if max_price is not None:
        query = query.filter(
            Item.daily_price <= max_price
        )

    return query.all()


# -------------------------------------------------
# Tek İlan Detayı
# -------------------------------------------------
@router.get("/{item_id}", response_model=ItemResponse)
def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db)
):
    """
    Seçilen ilanın detay bilgilerini getirir.
    """

    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    return item


# -------------------------------------------------
# İlan Güncelleme
# -------------------------------------------------
@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibinin kendi ilanını güncellemesini sağlar.
    """

    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı güncelleme yetkiniz yok."
        )

    if item_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == item_data.category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kategori bulunamadı."
            )

    update_data = item_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return item


# -------------------------------------------------
# İlan Silme / Pasif Hale Getirme
# -------------------------------------------------
@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibinin kendi ilanını pasif hale getirmesini sağlar.
    Kayıt veritabanından silinmez, sadece is_active False yapılır.
    """

    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı silme yetkiniz yok."
        )

    item.is_active = False

    db.commit()
    db.refresh(item)

    return {
        "message": "İlan başarıyla pasif hale getirildi.",
        "item_id": item.id,
        "is_active": item.is_active
    }