from time import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView
from django.shortcuts import render, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import (GenericAPIView, ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView)
from rest_framework.views import APIView
from .serializers import *
from rest_framework import status, permissions
from .validators import validate_phone_number, find_None
from rest_framework_simplejwt.views import TokenViewBase
from .models import (User, Profile, Address, Confirmation, UploadFile, ProfilePictures)
from rest_framework.generics import *
from django.utils import timezone
from .utils import send_ms_to_channel
from django.shortcuts import get_object_or_404
import random
class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request: Request, *args, **kwargs):
        phone = request.data.get('phone', None)
        validate_phone_number(phone=phone)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data={"success": True, "message": "You have succesfully been registered."})


class AllUsersView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()

    def get_user_data(self, pk=None):
        if pk:
            user = User.objects.filter(pk=pk).last()
            data = {
                "id": user.id,
                "phone": user.phone,
                "is_seller": user.is_seller,
                "is_active": user.is_active
            }

            profile = Profile.objects.filter(user_id=user.id)
            if profile.exists():
                data['profile'] = (profile.last()).id

            return Response(data=data, status=status.HTTP_200_OK)
        else:
            users = User.objects.all()
            user_list = []

            for user in users:
                data = {
                    "id": user.id,
                    "phone": user.phone,
                    "is_seller": user.is_seller,
                    "is_active": user.is_active
                }
                profile = get_object_or_404(Profile, user_id=user.id)

                data['profile'] = profile.id
                user_list.append(data)
            return Response(data=user_list, status=status.HTTP_200_OK)

    def get(self, request: Request, *args, **kwargs):
        return self.get_user_data(kwargs.get('pk', None))

    def delete(self, *args, **kwargs):
        self.destroy(self, *args, **kwargs)

        return Response(data={"success": True, "message": "Foydalanuvchi muvoffaqiyatli o'chirildi !"},
                        status=status.HTTP_204_NO_CONTENT)


class LoginView(TokenViewBase):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


from rest_framework_simplejwt.authentication import JWTAuthentication


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request: Request, *args, **kwargs):
        serializers = self.serializer_class(data=request.data)
        serializers.is_valid(raise_exception=True)
        serializers.save()

        response = {
            "success": True, "message": "Tizimdan chiqish muvoffaqiyatli"
        }

        return Response(data=response, status=status.HTTP_205_RESET_CONTENT)


class VerifyView(APIView):

    def post(self, request, *args, **kwargs):
        

        phone = request.data.get('phone', None)
        new_phone = request.data.get('new_phone', None)
        type = request.data.get('type', None)
        code = request.data.get('code', None)
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(data={'success': False, "message": "kiritilgan foydalanuvchi mavjud emas !"},
                            status=status.HTTP_404_NOT_FOUND)
        if None in (phone, new_phone, type, code) and type == "change_phone":
            find_None([phone, new_phone, type, code])
        qs = Confirmation.objects.filter(user=user, expiration_time__gte=timezone.now(), is_confirmed=False)

        if qs.exists():
            obj = qs.last()
            if obj.code != code:
                response = {
                    "success": False,
                    "message": "Noto'g'ri kod kiritildi !"
                }
                return Response(data=response)
            obj.activate()

            if type == 'change_phone':
                user = User.objects.filter(phone=phone).last()
                user.phone = new_phone
                user.save()

                message = 'kod tasdiqlandi. telefonni yangilash muvoffaqiyatli !'
            elif type == 'password_reset':
                message = 'kod tasdiqlandi parolni tiklashga ruxsat berildi !'
            else:
                message = 'kod tasdiqlandi. ro\'yxatdan o\'tish muvoffaqiyatli ! '
            return Response(data={'success': True, 'message': message})
        else:
            if Confirmation.objects.filter(user=user):
                return Response(data={'success': False,
                                      'message': "Kodning aktivlik muddati o'tgan, davom etish uchun kodni qaytda yuboring !"})
            else:
                response = {"success": False, "message": "Telefon raqami noto'g'ri kiritildi !"}
                return Response(data=response, status=status.HTTP_404_NOT_FOUND)


class ChangePhoneView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request: Request):
        serializer = ChangePhoneSerializer(data=request.data)
        if serializer.is_valid():
            new_phone = serializer.validated_data['new_phone']
            validate_phone_number(new_phone)

            user = self.request.data
            user.edit_phone()

            return Response(
                data={"success": True, "message": "Telefon raqamini yangilash so'rovi yuborildi kodni tasdiqlang !"})
        else:
            Response(data={"success": False, "message": "Tog'ri telefon raqamini kirting"},
                     status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    
    serializer_class = ChangePasswordSerializer
    permissions_class = [permissions.IsAuthenticated]
    model = User

    def update(self, request: Request, *args, **kwargs):
        self.object = self.request.user
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            if not self.object.check_password(serializer.validated_data.get('old_password')):
                return Response(data={"success": False, 'message': "Parol noto'gri kiritildi !"},
                                status=status.HTTP_400_BAD_REQUEST)

            self.object.set_password(serializer.validated_data['new_password'])
            self.object.save()

            response = {
                'success': True,
                'message': 'parol yangilash muvoffaqiyatli bajarildi !'
            }
            return Response(data=response, status=status.HTTP_200_OK)
        
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetAPIView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request: Request, *args, **kwargs):
        phone = request.data.get("phone", None)
        user = User.objects.filter(phone=phone)
        
        if user.exists():
            code = "".join(str(random.randint(0, 9)) for _ in range(6))
            Confirmation.objects.create(
                user=user.last(),
                code=code,
                type='password_reset',
                expiration_time=timezone.now() + timezone.timedelta(minutes=3))
            
            send_ms_to_channel(code=code)
            
            data = {
                'success' : True,
                "message": "Parol tiklash arizasi qabul qilindi. Kodni tasdiqlang !"
            }
            return Response(data=data, status=status.HTTP_200_OK)
        return Response(data={"success": False, "message": "Bunday telfon raqamli foydalanuvchi mavjud emas !"})


class PasswordResetConfirmAPIView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request: Request, *args, **kwargs):

        phone = request.data.get('phone')
        password = request.data.get('password')
        password2 = request.data.get('password2')
            
        if not password == password2:
            
            return Response(data={"success": False, "message": "Kiritilgan parol bir xil emas !"})
        
        user = get_object_or_404(User, phone=phone)
        
        user.set_password(password)
        user.save()
        
        return Response(data={"success": True, "message": "Parol muvoffaqiyatli yangiladni !"})


class ResendCodeAPIView(APIView):
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request: Request, *args, **kwargs):
        
        phone = request.data.get('phone')
        type = request.data.get('type')
        
        if type == None or phone == None:
            
            return Response(data={"success": False, 'message': "Ma'lumot to'liq kiritilmadi ! kerakli ma'lumotlar ['phone', 'type']"})

        user = get_object_or_404(User, phone=phone)
        expirations = Confirmation.objects.filter(user=user)
        expirations.delete()
        
        if type in ['register', 'password_reset', 'change_phone']:
            code = "".join(str(random.randint(0,9) for _ in range(6)))
            user = Confirmation.onjects.create(user=user, expiration_time=timezone.now() + timezone.timedelta(minutes=3), code=code)
            send_ms_to_channel(code=code)
        else:
            return Response(data={"success": False, "message": "Bunday tasdiqlash turi mavjud emas !"})
        
        return Response(data={"success": True, "message": "Kod qayta yuborildi, tasdiqlash ! "})



class CheckUserPassword(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request, *args, **kwargs):
        phone = request.data.get('phone')
        password = request.data.get('password')
        
        user = User.objects.filter(phone=phone).first()
        
        ps_check = user.check_password(password)
        
        return Response(data={"is user's password" : ps_check}, status=status.HTTP_200_OK)


# **********************************  User Profile Section****************************************************************


class ListCreateProfileAPIView(ListCreateAPIView):
    ...
    


class ProfileAPIView(RetrieveDestroyAPIView):
    
    permission_classes = [permissions.AllowAny]
    queryset = Profile.objects.all()
    
    def get(self, request: Request, *args, **kwargs):


        profile_ = Profile.objects.filter(id=kwargs['pk'])
        profile = profile_.last()
        if profile_.exists():
            
            data = {
                "id" : profile.id,
                "first_name" : profile.first_name,
                "last_name" : profile.last_name,
                "email" : profile.email,
                "image" : profile.photo,
                "user" : profile.user.phone,
                "user_id" : profile.user.id
            }
            
            address_ = Address.objects.filter(profile=profile)
            
            if address_.exists():
                address = address_.last()
                data['adress'] = address.id
        
        else:
            
            return Response(data={'success': False, "message": "Bunday Profile mavjud emas !"})

    
    def patch(self, request: Request, *args, **kwargs):
        ...
    
    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        
        return Response(data={'success': True, "message": "Profile deleted !"}, status=status.HTTP_204_NO_CONTENT)
    
    
class AddressCreateView(ListCreateAPIView):
        
    ...


class AddressAPIView(RetrieveUpdateDestroyAPIView):
    
    ...
