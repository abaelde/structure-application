from .base import Product
from .quota_share import quota_share, QuotaShare
from .excess_of_loss import excess_of_loss, ExcessOfLoss
from src.domain.constants import PRODUCT

# Fonctions pures (pour compatibilité et tests)
__all__ = ["quota_share", "excess_of_loss", "Product", "QuotaShare", "ExcessOfLoss", "PRODUCT_REGISTRY"]

# Registre des produits (pattern Strategy)
PRODUCT_REGISTRY = {
    PRODUCT.QUOTA_SHARE: QuotaShare(),
    PRODUCT.EXCESS_OF_LOSS: ExcessOfLoss(),
}
