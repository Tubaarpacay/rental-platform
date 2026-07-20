# Teklif işlemleri için router dosyası

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Offer, Item, User, Booking
from app.schemas import OfferCreate, OfferResponse
from app.auth import get_current_user


router = APIRouter(
    prefix="/offers",
    tags=["Offers"]
)


# -------------------------------------------------
# Teklif Oluştur
# -------------------------------------------------
@router.post("/", response_model=OfferResponse)
def create_offer(
    offer: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcı bir ilana teklif gönderir.
    """

    # Teklif verilen ilanı bul
    item = db.query(Item).filter(
        Item.id == offer.item_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="İlan bulunamadı."
        )

    # Pasif ilana teklif verilmesini engelle
    if not item.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pasif bir ilana teklif veremezsiniz."
        )

    # Kullanıcının kendi ilanına teklif vermesini engelle
    if item.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kendi ilanınıza teklif veremezsiniz."
        )

    # Tarih kontrolü
    if offer.end_date < offer.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bitiş tarihi başlangıç tarihinden önce olamaz."
        )

    # Yeni teklif oluştur
    new_offer = Offer(
        item_id=offer.item_id,
        renter_id=current_user.id,
        owner_id=item.owner_id,
        start_date=offer.start_date,
        end_date=offer.end_date,
        offered_price=offer.offered_price,
        message=offer.message,
        status="pending"
    )

    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)

    return new_offer


# -------------------------------------------------
# Gönderdiğim Teklifleri Listele
# -------------------------------------------------
@router.get("/sent", response_model=list[OfferResponse])
def list_sent_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının gönderdiği teklifleri listeler.
    """

    offers = db.query(Offer).filter(
        Offer.renter_id == current_user.id
    ).order_by(
        Offer.created_at.desc()
    ).all()

    return offers


# -------------------------------------------------
# Bana Gelen Teklifleri Listele
# -------------------------------------------------
@router.get("/received", response_model=list[OfferResponse])
def list_received_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Giriş yapan kullanıcının sahibi olduğu ilanlara
    gönderilen teklifleri listeler.
    """

    offers = db.query(Offer).filter(
        Offer.owner_id == current_user.id
    ).order_by(
        Offer.created_at.desc()
    ).all()

    return offers


# -------------------------------------------------
# Teklifi Kabul Et
# -------------------------------------------------
@router.patch("/{offer_id}/accept", response_model=OfferResponse)
def accept_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibi kendisine gelen bekleyen bir teklifi kabul eder.

    Teklif kabul edildiğinde otomatik olarak
    bir rezervasyon kaydı oluşturulur.
    """

    # Teklifi bul
    offer = db.query(Offer).filter(
        Offer.id == offer_id
    ).first()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teklif bulunamadı."
        )

    # Sadece ilan sahibi teklifi kabul edebilir
    if offer.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu teklifi kabul etme yetkiniz yok."
        )

    # Sadece bekleyen teklifler kabul edilebilir
    if offer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece bekleyen teklifler kabul edilebilir."
        )

    # Bu teklif için daha önce rezervasyon oluşturulmuş mu kontrol et
    existing_booking = db.query(Booking).filter(
        Booking.offer_id == offer.id
    ).first()

    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu teklif için daha önce rezervasyon oluşturulmuş."
        )

    # Teklifi kabul edilmiş olarak güncelle
    offer.status = "accepted"

    # Kabul edilen tekliften otomatik rezervasyon oluştur
    new_booking = Booking(
        item_id=offer.item_id,
        renter_id=offer.renter_id,
        offer_id=offer.id,
        address_id=None,
        start_date=offer.start_date,
        end_date=offer.end_date,
        total_price=offer.offered_price,
        status="pending"
    )

    db.add(new_booking)

    # Teklif ve rezervasyon aynı işlemde kaydedilir
    db.commit()
    db.refresh(offer)

    return offer


# -------------------------------------------------
# Teklifi Reddet
# -------------------------------------------------
@router.patch("/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    İlan sahibi kendisine gelen bekleyen bir teklifi reddeder.
    """

    # Teklifi bul
    offer = db.query(Offer).filter(
        Offer.id == offer_id
    ).first()

    if not offer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teklif bulunamadı."
        )

    # Sadece ilan sahibi teklifi reddedebilir
    if offer.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu teklifi reddetme yetkiniz yok."
        )

    # Sadece bekleyen teklifler reddedilebilir
    if offer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece bekleyen teklifler reddedilebilir."
        )

    offer.status = "rejected"

    db.commit()
    db.refresh(offer)

    return offer