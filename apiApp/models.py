from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import uuid


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.email
    

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to ="category_img", blank=True, null=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
           base_slug = slugify(self.name)
           unique_slug = base_slug
           counter = 1
           while Product.objects.filter(slug=unique_slug).exists():
               unique_slug = f"{base_slug}-{counter}"
               counter += 1
           self.slug = unique_slug
        super().save(*args, **kwargs)



class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    slug = models.SlugField(unique=True, blank=True)
    featured = models.BooleanField(default=True)
    image = models.ImageField(upload_to ="product_img", blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name='products',blank=True, null=True)   

    def __str__(self):
        return self.name 
    

    def save(self, *args, **kwargs):
        if not self.slug:
           base_slug = slugify(self.name)
           unique_slug = base_slug
           counter = 1
           while Product.objects.filter(slug=unique_slug).exists():
               unique_slug = f"{base_slug}-{counter}"
               counter += 1
           self.slug = unique_slug
        super().save(*args, **kwargs)



class Cart(models.Model):
    cart_code = models.CharField(max_length=100, unique=True) #, default=uuid.uuid4
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.cart_code)    



class CartItem(models.Model):
    cart = models.ForeignKey('Cart', on_delete=models.CASCADE, related_name='cartitems')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} × {self.product.name} (Cart: {self.cart.cart_code})"   



class Review(models.Model):

    RATING_CHOICES = [
    (1, 'Poor'),
    (2, 'Fair'),
    (3, 'Good'),
    (4, 'Very Good'),
    (5, 'Excellent'),
]

    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)  
    review = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s review on  - {self.product.name}"  
    
    class Meta:
        ordering = ['-created']  
        unique_together = ('product', 'user')    



class ProductRating(models.Model):
    product = models.OneToOneField('Product', on_delete=models.CASCADE, related_name='rating')
    average_rating = models.FloatField(default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} → {self.average_rating}/5 ({self.total_reviews} reviews)"
    

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='wishlist')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.product.name}"

    class Meta:
        unique_together = ('user', 'product') 
        ordering = ['-created']



class Order(models.Model):
    stripe_checkout_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='usd')
    customer_email = models.EmailField()
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.stripe_checkout_id} - {self.status}"
    


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Order {self.product.name} - {self.order.stripe_checkout_id}"
