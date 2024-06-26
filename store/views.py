from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from django.conf import settings
from drf_spectacular.utils import (
    extend_schema, 
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse
)
from .models import (
    User, 
    Product, 
    Order, 
    OrderItem, 
    UserInfo
)
from .serializers import (
    ProductSerializer, 
    OrderSerializer, 
    OrderItemSerializer, 
    UserInfoSerializer
)

# Create your views here.

class StoreProductsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="list_all_products",
        description="List all products short descriptions: name, price",
        responses={200: ProductSerializer(many=True)}
    )
    def get(self, request):
        pagination = PageNumberPagination()
        data = request.GET
        is_hot_saled = data.get('is_hot_saled')

        if is_hot_saled:
            products = Product.objects.filter(isHotSaled=True).values()
            pagination.page_size = settings.HOT_SALED_PAGINATION_PAGE_SIZE
        else:
            devices = data.get('devices')
            brand = data.get('brand')
            name = data.get('name')
            if devices:
                products = Product.objects.filter(categories=devices)
            elif brand:
                products = Product.objects.filter(brand=brand)
            else:
                products = Product.objects.all()
            if name:    
                products = products.filter(name__icontains=name)
            pagination.page_size = settings.PAGINATION_PAGE_SIZE

        page = pagination.paginate_queryset(products, request)
        serializer = ProductSerializer(page, many=True)
        return pagination.get_paginated_response(serializer.data)

    @extend_schema(
        operation_id="create_product",
        description="Create a new product",
        responses={
            201: OpenApiResponse(description="Successfully created new product!"),
            400: OpenApiResponse(description="Failed to create new product or unauthorized.")
        }
    )
    def post(self, request):
        user = request.user

        if user.is_admin:
            name = request.data.get("name")
            price = request.data.get("price")
            digital = request.data.get("digital")
            image = request.data.get("image")
            imageUploadURL = request.data.get("image_upload_url")

            try:
                Product.objects.create(
                    name=name, 
                    price=price, 
                    digital=digital, 
                    image=image,
                    imageUploadURL = imageUploadURL,
                    updatedBy=user
                )

                return Response(
                    {"message": "Successfully created new product!"}, status=201
                )
            except:
                return Response({"errors": "Failed to create new product!"}, status=400)
        else:
            return Response({"errors": "You need to have role admin!"}, status=400)


class ProductView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="retrieve_product_detail",
        description="Retrieve details of a product by ID",
        responses={
            200: ProductSerializer,
            404: OpenApiResponse(description="No such product!")
        }
    )
    def get(self, request, id):
        try:
            product = Product.objects.get(pk=id)
            serializer = ProductSerializer(product)
            return Response({"product": serializer.data}, status=200)
        except:
            return Response({"error": "No such product!"}, status=404)


class OrderViewset(viewsets.ViewSet):
    serializer_class = OrderSerializer

    def get(self, request):
        try:
            user = request.user
            if user.is_admin:
                orders = Order.objects.all()
            else:
                orders = Order.objects.filter(user=user)
            serializer = OrderSerializer(orders, many=True)
            return Response({"orders": serializer.data}, status=200)
        except:
            return Response({"errors": "You don't have any order!"}, status=400)

    def post(self, request):
        user = request.user
        new_order = Order.objects.create(user=user, complete=False)
        serializer = OrderSerializer(new_order)
        return Response(
            {
                "message": "Successfully created new order!",
                "order": serializer.data,
            },
            status=200,
        )

    def put(self, request):
        req_user = request.user
        try: 
            order = Order.objects.get(user=req_user, complete=False)
            order.complete = True
            order.save()
            return Response({"message": "Successfully Save Order!"}, status=200)
        except Exception as error:
            return Response({ "error": error }, status=404)
    
    @extend_schema(
        parameters=[OpenApiParameter(
            name='user_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH
        )]
    )
    @action(detail=False, methods=["GET"], url_path="userid/(?P<user_id>[^/.]+)")
    def get_by_userid(self, request, user_id):
        req_user = request.user

        if req_user.is_admin:
            user = User.objects.get(id=user_id)
            orders = Order.objects.filter(user=user)
            serializer = OrderSerializer(orders, many=True)
            return Response({"orders": serializer.data}, status=200)
        else:
            return Response({"errors": "You need to have role admin!"}, status=400)
        
class OrderItemView(APIView):
    serializer_class = OrderItemSerializer

    def get(self, request):
        req_user = request.user
        order, created = Order.objects.get_or_create(user=req_user, complete=False)
        order_items = OrderItem.objects.filter(order=order)
        serailzer = OrderItemSerializer(order_items, many=True)
        return Response({ "order_items": serailzer.data })
    
    def post(self, request):
        req_user = request.user
        product_id = request.data.get("product_id")
        product = Product.objects.get(id=product_id)
        order, created = Order.objects.get_or_create(user=req_user, complete=False)
        order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
        order_item.quantity = order_item.quantity + 1
        order_item.save()

        return Response({ "message": f"Order successfully product {product.name}" }, status=201)

    def put(self, request):
        req_user = request.user
        id = request.data.get("id")
        quantity = request.data.get("quantity")
        
        try:
            if quantity:
                order_item = OrderItem.objects.get(id=id)
                order_item.quantity = quantity
                order_item.save()
            else:
                OrderItem.objects.filter(id=id).delete()

            return Response({ "message": "Update item quantity successfully!" }, status=200)
        except:
            return Response({ "message": "There is no such item!" }, status=404)

    def delete(self, request):
        req_user = request.user
        id = request.data.get("id")
        try: 
            OrderItem.objects.filter(id=id).delete()
            return Response({ "message": f"Successfully remove order items" }, status=200)
        except:
            return Response({ "error": "This item is" })

class UserInfoView(APIView):
    serializer_class = UserInfoSerializer

    def get(self, request):
        req_user = request.user
        user_info = UserInfo.objects.filter(user=req_user).first()
        serializer = UserInfoSerializer(user_info)
        return Response({ "user_info": serializer.data }, status=200)

    def post(self, request):
        data = request.data
        req_user = request.user

        try:
            user_info, _ = UserInfo.objects.get_or_create(user=req_user)
        except UserInfo.DoesNotExist:
            return Response({"error": "User info not found"}, status=404)

        user_info.firstname = data.get('firstname')
        user_info.lastname = data.get('lastname')
        user_info.date_of_birth = data.get('date_of_birth')
        user_info.gender = data.get('gender')
        user_info.email = data.get('email')
        user_info.phone = data.get('phone')

        user_info.home_address = data.get('home_address')
        user_info.home_number = data.get('home_number')
        user_info.city = data.get('city')
        user_info.state = data.get('state')
        user_info.zip = data.get('zip')

        user_info.bankname = data.get('bankname')
        user_info.account_holder = data.get('account_holder')
        user_info.account_number = data.get('account_number')
    
        user_info.save()

        serializer = UserInfoSerializer(user_info)
        return Response(serializer.data, status=200)