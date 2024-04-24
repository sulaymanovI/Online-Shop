from rest_framework.exceptions import ValidationError
import re
from .models import User
from rest_framework import serializers

def validate_phone_number(phone):
    phone_regexp=r"^[\+]?[(]?[9]{2}?[8]{1}[)]?[-\s\.]?[0-9]{2}[-\s\.]?[0-9]{7}$"

    is_match= re.fullmatch(phone_regexp , phone)

    if not is_match:
        data={
            "success" : False,
            "message" : "Telefon raqami to'g'ri kiritilmadi!"

        }
        raise ValidationError(data)
    if User.objects.filter(phone=phone).exists():
        raise ValidationError({"success" : False , "message" : "Bu nomer ro'yhatdan o'tgan!!"})
    return True

def validate_password_strength(password):
        katta=False
        kichik=False
        belgi=False
        raqam=False

        belgilar=("." , "_" , "*" , "-" ,"$" , "#")

        for char in password:

            if 64<ord(char)<92:
                katta=True
            elif 96<ord(char)<123:
                kichik=True
            elif char in belgilar:
                belgi=True
            elif char.isnumeric():
                raqam=True

        if len(password)<8:
            raise serializers.ValidationError({"succes" : False , "message" : "Parol 8 belgidan kam bo'lmasligi kerak"})
        
        if (katta+kichik+belgi+raqam) < 2:
            raise serializers.ValidationError({"succes" : False , "message" : f"Parol xafsizlik talabiga javob bermaydi! Katta va Kichik harflar yoki {belgilar} belgilardan foydalaning"})
        
        return True

def find_None(data:list):
    datalar = {
        1 : "phone",
        2 : "code",
        3 : "type",
        4 : "new_phone"
    }
    Nones = []
    for none in data:

        if none is None:

            Nones.append(datalar[data.index(none)+1])
    if len(Nones):
        return Nones
    return True