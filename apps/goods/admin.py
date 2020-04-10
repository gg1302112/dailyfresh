from django.contrib import admin
from .models import GoodsType, GoodsSKU, Goods, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django.core.cache import cache
# Register your models here.


class BasemodelAdmin(admin.ModelAdmin):
    """重写后的基础类"""
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from celery_tasks.tasks import get_static_index_html
        get_static_index_html.delay()
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        from celery_tasks.tasks import get_static_index_html
        get_static_index_html.delay()
        cache.delete('index_page_data')


class GoodsTypeAdmin(BasemodelAdmin):
    pass


class IndexGoodsBannerAdmin(BasemodelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BasemodelAdmin):
    pass


class IndexPromotionBannerAdmin(BasemodelAdmin):
    pass


admin.site.register(GoodsType, BasemodelAdmin)
admin.site.register(GoodsSKU)
admin.site.register(Goods)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

