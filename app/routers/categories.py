# Kategori işlemleri için router dosyası

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse


router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# -------------------------------------------------
# Kategori Oluşturma
# -------------------------------------------------
@router.post("/", response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni kategori oluşturur.
    """

    # Aynı isimde kategori var mı kontrol et
    existing_category = db.query(Category).filter(
        Category.name == category_data.name
    ).first()

    # Kategori zaten varsa hata döndür
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kategori zaten mevcut."
        )

    # Yeni kategori nesnesi oluştur
    new_category = Category(
        name=category_data.name
    )

    # Kategoriyi veritabanına kaydet
    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


# -------------------------------------------------
# Kategori Listeleme
# -------------------------------------------------
@router.get("/", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """
    Tüm kategorileri listeler.
    """

    # Veritabanındaki tüm kategorileri getir
    return db.query(Category).all()