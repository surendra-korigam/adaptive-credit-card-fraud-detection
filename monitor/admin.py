from django.contrib import admin
from .models import Transaction
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display=("id","created_at","amount","fraud_probability","decision","actual_class","feedback_class")
    list_filter=("decision","actual_class")
