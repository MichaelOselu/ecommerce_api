from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.db.models import Q
from .models import Cart, CartItem, Order, OrderItem, Product, Category, Review, Wishlist
from .serializers import CartItemSerializer, CartSerializer, CategoryDetailSerializer, ProductListSerializer, ProductDetailSerializer, CategoryListSerializer, ReviewSerializer, WishlistSerializer
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
endpoint_secret = settings.WEBHOOK_SECRET


from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# Set your secret key: remember to load this from environment in production
stripe.api_key = settings.STRIPE_SECRET_KEY  # Make sure you have this in settings.py

YOUR_DOMAIN = 'http://localhost:8008'





User = get_user_model()

@api_view(['GET'])
def product_list(request):
    products = Product.objects.filter(featured=True)
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def product_detail(request, slug):
    products = Product.objects.get(slug=slug)
    serializer = ProductDetailSerializer(products)
    return Response(serializer.data)

@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategoryListSerializer(categories, many=True)
    return Response(serializer.data)



@api_view(['GET'])
def category_detail(request, slug):
    categories = Category.objects.get(slug=slug)
    serializer = CategoryDetailSerializer(categories)
    return Response(serializer.data)


@api_view(['POST'])
def add_to_cart(request):
    cart_code = request.data.get('cart_code')
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    cart, created = Cart.objects.get_or_create(cart_code=cart_code)
    product = Product.objects.get(id = product_id)
    cartitem, created = CartItem.objects.get_or_create(cart=cart, product=product)
    cartitem.quantity = 1
    cartitem.save()
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(['PUT'])
def update_cartitem_quantity(request):
    cartitem_id = request.data.get("item_id")
    quantity = int(request.data.get('quantity'))
    cartitem = CartItem.objects.get(id=cartitem_id)
    cartitem.quantity= quantity
    cartitem.save()

    serializer = CartItemSerializer(cartitem)
    return Response({"data" : serializer.data, "meaasge" : "Cartitem updated succesfully"})


@api_view(['POST'])
def add_review(request):
   
    product_id = request.data.get('product_id')
    email = request.data.get('email')
    rating = request.data.get('rating')
    review_text = request.data.get('review')

    product = Product.objects.get(id=product_id)
    user = User.objects.get(email=email)

    if Review.objects.filter(product=product, user=user).exists():
        return Response({"error": "You have already reviewed this product"}, status=status.HTTP_400_BAD_REQUEST)

    
    review = Review.objects.create(
        product=product,
        user=user,
        rating=rating,
        review=review_text
    )

    serializer = ReviewSerializer(review)
    return Response(serializer.data)




@api_view(['PUT'])
def update_review(request, pk):
    
    review = Review.objects.get(id=pk)
    rating = request.data.get('rating')
    review_text = request.data.get('review')

    review.rating = rating
    review.review = review_text
    review.save()

    serializer = ReviewSerializer(review)
    return Response(serializer.data, status=status.HTTP_200_OK) 


@api_view(['DELETE'])
def delete_review(request, pk):
    
    review = Review.objects.get(id=pk)
    review.delete()
    return Response({"message": "Review deleted successfully."}, status=status.HTTP_200_OK)

# @api_view(['DELETE'])
# def delete_cartitem(request, pk):
#     cartitem = CartItem.objects.get(id=pk)
#     cartitem.delete()
#     return Response({"message": "cartitem deleted successfully."}, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_cartitem(request, pk):
    try:
        cartitem = CartItem.objects.get(id=pk)
    except CartItem.DoesNotExist:
        return Response({"error": "CartItem not found."}, status=status.HTTP_404_NOT_FOUND)

    cartitem.delete()
    return Response({"message": "CartItem deleted successfully."}, status=status.HTTP_200_OK)


@api_view(['POST'])
def add_to_wishlist(request):
    email = request.data.get('email')
    product_id = request.data.get('product_id')

    user = User.objects.get(email=email)
    product = Product.objects.get(id=product_id)

    wishlist = Wishlist.objects.filter(user=user, product=product)

    if wishlist:
        wishlist.delete()
        return Response({"message": "Product removed from wishlist."}, status=status.HTTP_200_OK)
    
    new_wishlist = Wishlist.objects.create(user=user, product=product)
    serializer = WishlistSerializer(new_wishlist)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def product_search(request):
    query = request.query_params.get('query')

    if not query:
        return Response({"error": "No query provided"}, status=status.HTTP_400_BAD_REQUEST)

    # Search by name or description (case-insensitive)
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) | 
        Q(category__name__icontains = query)
    )

    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)



@api_view(['POST'])
def create_checkout_session(request):
    cart_code = request.data.get("cart_code")
    email = request.data.get("email")
    cart = Cart.objects.get(cart_code=cart_code)
    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email= email,
            payment_method_types=['card'],


            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': item.product.name},
                        'unit_amount': int(item.product.price * 100),  # Amount in cents
                    },
                    'quantity': item.quantity,
                }
                for item in cart.cartitems.all()
            ] + [
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': 'VAT Fee'},
                        'unit_amount': 500,  # $5 in cents
                    },
                    'quantity': 1,
                }
            ],


           
            mode='payment',
            # success_url="http://localhost:3000/success",
            # cancel_url="http://localhost:3000/cancel",

            success_url="https://next-shop-self.vercel.app/success",
            cancel_url="https://next-shop-self.vercel.app/failed",
            metadata = {"cart_code": cart_code}
        )
        return Response({'data': checkout_session})
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    






@csrf_exempt
def my_webhook_view(request):
  payload = request.body
  sig_header = request.META['HTTP_STRIPE_SIGNATURE']
  event = None

  try:
    event = stripe.Webhook.construct_event(
      payload, sig_header, endpoint_secret
    )
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)
  except stripe.error.SignatureVerificationError as e:
    # Invalid signature
    return HttpResponse(status=400)

  if (
    event['type'] == 'checkout.session.completed'
    or event['type'] == 'checkout.session.async_payment_succeeded'
  ):
    session = event['data']['object']
    cart_code = session.get("metadata", {}).get("cart_code")

    fulfill_checkout(session, cart_code)


  return HttpResponse(status=200)



def fulfill_checkout(session, cart_code):
    
    order = Order.objects.create(stripe_checkout_id=session["id"],
        amount=session["amount_total"],
        currency=session["currency"],
        customer_email=session["customer_email"],
        status="Paid")
    

    print(session)


    cart = Cart.objects.get(cart_code=cart_code)
    cartitems = cart.cartitems.all()

    for item in cartitems:
        orderitem = OrderItem.objects.create(order=order, product=item.product, 
                                             quantity=item.quantity)
    
    cart.delete()








    
