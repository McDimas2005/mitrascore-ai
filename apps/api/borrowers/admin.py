from django.contrib import admin

from .models import BorrowerProfile, ConsentRecord


@admin.register(BorrowerProfile)
class BorrowerProfileAdmin(admin.ModelAdmin):
    list_display = ("business_name", "owner", "status", "assisted_by", "updated_at")
    list_filter = ("status", "business_category")


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ("borrower_profile", "consent_given", "given_by", "given_at")
