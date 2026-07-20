# Eşya / ilan işlemleri için router dosyası

# Dosya işlemleri için
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Item, Category, User
from app.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.auth import get_current_user


router = APIRouter(
    prefix="/items",
    tags=["Items"]
)


# -------------------------------------------------
# Dosya Yükleme Klasörü
# -------------------------------------------------
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

    # Kategori var mı kontrol et
    category = db.query(Category).filter(
        Category.id == item_data.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kategori bulunamadı."
        )

    # Günlük fiyat pozitif olmalı
    if item_data.daily_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Günlük kiralama ücreti sıfırdan büyük olmalıdır."
        )

    # Yeni ilan oluştur
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
@router.post(
    "/{item_id}/upload-photo",
    response_model=ItemResponse
)
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

    # İlanı bul
    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # Sadece ilan sahibi fotoğraf yükleyebilir
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilana fotoğraf yükleme yetkiniz yok."
        )

    # Dosya türü kontrolü
    allowed_content_types = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece JPG, PNG veya WEBP dosyası yüklenebilir."
        )

    # Dosya uzantısını al
    file_extension = Path(file.filename or "").suffix.lower()

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz dosya uzantısı."
        )

    # Benzersiz dosya adı oluştur
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Dosyayı uploads klasörüne kaydet
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    finally:
        file.file.close()

    # İlanın fotoğraf yolunu güncelle
    item.photo_url = f"/uploads/{unique_filename}"

    db.commit()
    db.refresh(item)

    return item


# -------------------------------------------------
# Aktif İlanları Listeleme, Arama ve Filtreleme
# -------------------------------------------------
@router.get("/", response_model=list[ItemResponse])
def list_items(
    city: str | None = Query(
        default=None,
        description="Şehre göre filtreleme"
    ),
    category_id: int | None = Query(
        default=None,
        ge=1,
        description="Kategori ID değerine göre filtreleme"
    ),
    min_price: float | None = Query(
        default=None,
        ge=0,
        description="Minimum günlük kiralama fiyatı"
    ),
    max_price: float | None = Query(
        default=None,
        ge=0,
        description="Maksimum günlük kiralama fiyatı"
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="İlan başlığı veya açıklamasında arama"
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Atlanacak ilan sayısı"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Döndürülecek maksimum ilan sayısı"
    ),
    db: Session = Depends(get_db)
):
    """
    Aktif ilanları listeler.

    İsteğe bağlı olarak:
    - şehir,
    - kategori,
    - minimum fiyat,
    - maksimum fiyat,
    - başlık veya açıklama

    alanlarına göre filtreleme ve arama yapar.

    skip ve limit parametreleriyle pagination sağlar.
    """

    # Minimum fiyat maksimum fiyattan büyük olamaz
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum fiyat maksimum fiyattan büyük olamaz."
        )

    # Sadece aktif ilanlardan başla
    query = db.query(Item).filter(
        Item.is_active.is_(True)
    )

    # Şehir filtresi
    if city:
        city = city.strip()

        if city:
            query = query.filter(
                Item.city.ilike(f"%{city}%")
            )

    # Kategori filtresi
    if category_id is not None:
        query = query.filter(
            Item.category_id == category_id
        )

    # Minimum fiyat filtresi
    if min_price is not None:
        query = query.filter(
            Item.daily_price >= min_price
        )

    # Maksimum fiyat filtresi
    if max_price is not None:
        query = query.filter(
            Item.daily_price <= max_price
        )

    # Başlık veya açıklamada arama
    if search:
        search = search.strip()

        if search:
            query = query.filter(
                Item.title.ilike(f"%{search}%")
                | Item.description.ilike(f"%{search}%")
            )

    # En yeni ilanlar önce gösterilir
    query = query.order_by(
        Item.created_at.desc()
    )

    # Pagination uygula
    items = query.offset(skip).limit(limit).all()

    return items


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
    Yalnızca gönderilen alanlar güncellenir.
    """

    # İlanı bul
    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # Sadece ilan sahibi güncelleyebilir
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı güncelleme yetkiniz yok."
        )

    # Yeni kategori gönderildiyse kontrol et
    if item_data.category_id is not None:
        category = db.query(Category).filter(
            Category.id == item_data.category_id
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kategori bulunamadı."
            )

    # Yeni fiyat gönderildiyse kontrol et
    if (
        item_data.daily_price is not None
        and item_data.daily_price <= 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Günlük kiralama ücreti sıfırdan büyük olmalıdır."
        )

    # Yalnızca gönderilen alanları al
    update_data = item_data.model_dump(
        exclude_unset=True
    )

    # Alanları güncelle
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

    # İlanı bul
    item = db.query(Item).filter(
        Item.id == item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # Sadece ilan sahibi pasif hale getirebilir
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu ilanı silme yetkiniz yok."
        )

    # Zaten pasifse tekrar işlem yapma
    if not item.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu ilan zaten pasif durumda."
        )

    item.is_active = False

    db.commit()
    db.refresh(item)

    return {
        "message": "İlan başarıyla pasif hale getirildi.",
        "item_id": item.id,
        "is_active": item.is_active
    }