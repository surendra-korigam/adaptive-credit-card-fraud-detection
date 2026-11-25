from django.db import models
class Transaction(models.Model):
    created_at=models.DateTimeField(auto_now_add=True)
    dataset_time=models.FloatField(null=True,blank=True)
    amount=models.FloatField(default=0)
    fraud_probability=models.FloatField(default=0)
    decision=models.CharField(max_length=12,default="REVIEW")
    actual_class=models.IntegerField(null=True,blank=True)
    source=models.CharField(max_length=20,default="dataset")
    feedback_class=models.IntegerField(null=True,blank=True)
    def __str__(self):
        return f"{self.pk}: {self.decision} ({self.amount})"
