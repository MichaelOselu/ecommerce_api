from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Cart, CartItem, Product, Category, Review, Wishlist

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug", "image", "price"]



class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "slug", "description", "image", "price"]



class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "image", "slug"] 



class CategoryDetailSerializer(serializers.ModelSerializer):
    products = ProductListSerializer(many =True, read_only=True)
    class Meta:
        model = Category
        fields = ["id", "name", "image", "products"]     



class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only = True)
    sub_total = serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ['id', 'product','quantity', 'sub_total']

    def get_sub_total(self, cartitem):
        total = cartitem.product.price * cartitem.quantity 
        return total



class CartSerializer(serializers.ModelSerializer):
    cartitems = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'cart_code', 'created_at', 'updated_at', 'cartitems', 'cart_total']   

        
    def get_cart_total(self, cart):
            items = cart.cartitems.all()
            total = sum([item.product.price * item.quantity for item in items])
            return total
       
            
class CartStartSerializer(serializers.ModelSerializer):
    total_quantity = serializers.SerializerMethodField()
    class Meta:
        model = Cart
        fields = ['id', 'card_code', 'total_quantity'] 

        def get_total_quantity(self, cart):
            items = cart.cartitems.all()
            total = sum([item.quantity for item in items])
            return total   


class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = get_user_model()
           fields = ['id', 'first_name', 'last_name', 'profile_picture_url']


class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    rating_display = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'rating_display', 'review', 'created', 'updated']

    def get_rating_display(self, obj):
        return obj.get_rating_display()  



class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    user = UserSerializer(read_only=True)  # Displays the username
    #created = serializers.DateTimeField(read_only=True)
   
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'product', 'created']          