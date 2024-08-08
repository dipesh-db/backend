import jwt
from django.conf import settings
from datetime import datetime,timedelta,UTC
from django.http import JsonResponse
from functools import wraps
from django.core.mail import send_mail
def generate_jwt_token(user_id,token_type):
    expiry=datetime.now(UTC)+ timedelta(minutes=60 if token_type=='access' else 7*24*60)
    payload={
        'user_id':user_id,
        'exp':expiry,
        'token_type':token_type


    }
    token=jwt.encode(payload,settings.SECRET_KEY,algorithm='HS256')
    return token



def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except (jwt.InvalidTokenError, Exception):
        return None
    
def jwt_authentication_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return JsonResponse({'message': 'Authentication token is missing'}, status=401)

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return JsonResponse({'message': 'Invalid token format'}, status=401)

        token = parts[1]
        user_id = verify_jwt_token(token)
        if user_id is None:
            return JsonResponse({'message': 'Invalid or expired token'}, status=401)

        request.user_id = user_id
        return view_func(request, *args, **kwargs)

    return wrapper

def send_email_to_client(email,subject,message):
    from_email=settings.EMAIL_HOST_USER
    recipient_list=[email]
    send_mail(subject,message,from_email,recipient_list)