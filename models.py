from django.db import models


class User(models.Model):
    user_email = models.EmailField(unique=True, max_length=30)
    user_password = models.CharField(max_length=30)
    user_role = models.CharField(max_length=30)
    otp = models.CharField(max_length=10, null=True, blank=True)
    otp_used = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.user_email

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class market_data(models.Model):
    Order_ID= models.CharField(max_length=100)
    Year= models.CharField(max_length=100)
    Order_Date= models.CharField(max_length=100)
    Ship_Date= models.CharField(max_length=100)
    Ship_Mode= models.CharField(max_length=100)
    Customer_ID= models.CharField(max_length=100)
    Customer_Name= models.CharField(max_length=100)
    Segment= models.CharField(max_length=100)
    Country= models.CharField(max_length=100)
    City= models.CharField(max_length=100)
    State= models.CharField(max_length=100)
    Postal_Code= models.CharField(max_length=100)
    Region= models.CharField(max_length=100)
    Product_ID=models.CharField(max_length=100)
    Category= models.CharField(max_length=100)
    Sub_Category= models.CharField(max_length=100)
    Product_Name= models.CharField(max_length=100)
    Sales= models.CharField(max_length=100)
    Quantity= models.CharField(max_length=100)
    Discount= models.CharField(max_length=100)
    
    def __str__(self):
        return self.Order_ID