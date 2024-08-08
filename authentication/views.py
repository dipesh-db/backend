from django.shortcuts import render,redirect
from django.http import JsonResponse

from django.db import connection
import json
import jwt
from django.contrib.auth.hashers import make_password,check_password
import secrets
from datetime  import datetime,timedelta,UTC
from django.conf import settings
from .utils import generate_jwt_token,send_email_to_client

# Create your views here.


def register_user(request):  
   
    if request.method=="POST":
        data=json.loads(request.body)
        username=data.get('username')
        email= data.get('email')
        password=make_password(data.get('password'))
        verification_token=secrets.token_urlsafe(32)
        

        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s OR email = %s", [username, email])
                count = cursor.fetchone()[0]
                
                if count > 0:
                    return JsonResponse({'message': 'User with this username or email already exists'}, status=400)
                
                cursor.execute("""
                           INSERT INTO users(username,email,password,verification_token)
                           VALUES(%s, %s, %s,%s)
                           RETURNING id
                           """,[username,email,password,verification_token])
                user_id=cursor.fetchone()[0]

                #verification email
                send_verification_email(email,verification_token)
                

                return JsonResponse({'message':'Email Sent to your email address for verification','user_id':user_id},status=201)
        
            except Exception as e:
                return JsonResponse({'message':str(e)},status=400)
        
    else:
        return JsonResponse({'message':'Unable'})
    


def verify_email(request):
    if request.method=="GET":
        token=request.GET.get('token')   

        with connection.cursor() as cursor:
              cursor.execute("SELECT id FROM users WHERE verification_token = %s", [token])
              user = cursor.fetchone()
              if user:
                cursor.execute("UPDATE users SET is_active = TRUE, verification_token = NULL WHERE id = %s", [user[0]])
                return redirect('https://frontend-jcuo9g8rz-aayush-chhetris-projects.vercel.app/login?verified=true')
    
              else:
                # Redirect to frontend login page with failure status
                return redirect('https://frontend-jcuo9g8rz-aayush-chhetris-projects.vercel.app/login?verified=false')
    return JsonResponse({'message': 'Invalid request method'}, status=405)





def request_password_reset(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            user = cursor.fetchone()
            
            if user:
                reset_token = secrets.token_urlsafe(32)
                cursor.execute("UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE id = %s", 
                               [reset_token, datetime.now() + timedelta(hours=1), user[0]])
                
                # Send password reset email
                send_password_reset_email(email, reset_token)
                
                return JsonResponse({'message': 'Password reset link sent to your email'}, status=200)
            else:
                return JsonResponse({'message': 'User with this email does not exist'}, status=400)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)


def login_user(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, password, is_active FROM users WHERE email = %s", [email])
            user = cursor.fetchone()

            if user and check_password(password, user[1]):
                if user[2]:
                    access_token = generate_jwt_token(user[0], 'access')
                    refresh_token = generate_jwt_token(user[0], 'refresh')
                    return JsonResponse({
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'user_id': user[0]
                    }, status=200)
                else:   
                    return JsonResponse({'message': 'Please verify your email address before logging in.'}, status=400)
            else:
                return JsonResponse({'message': 'Invalid credentials'}, status=400)
            
    return JsonResponse({'message': 'Invalid request method'}, status=405)



def refresh_token(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        refresh_token = data.get('refresh_token')
        
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload['token_type'] != 'refresh':
                return JsonResponse({'message': 'Invalid token type'}, status=400)
            
            user_id = payload['user_id']
            new_access_token = generate_jwt_token(user_id, 'access')
            return JsonResponse({'access_token': new_access_token}, status=200)
        
        except jwt.ExpiredSignatureError:
            return JsonResponse({'message': 'Refresh token expired'}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({'message': 'Invalid refresh token'}, status=400)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)


def send_verification_email(email,token):
    subject="Verify your email-address"
    message=f"Click the link to verify your email:https://event-snowy-eight.vercel.app/authentication/verify-email?token={token}"
    send_email_to_client(email,subject,message)


def send_password_reset_email(email,token):
    subject="Reset your Password"
    message=f"Click the link to reset your password: https://event-snowy-eight.vercel.app/authentication/reset-password?token={token}"
    send_email_to_client(email,subject,message)    



def get_user_info(request):
    if request.method == 'GET':
         token = request.headers.get('Authorization')
         if token and token.startswith('Bearer '):
            token = token[len('Bearer '):]  # Remove "Bearer " prefix

            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')

                with connection.cursor() as cursor:
                    cursor.execute("SELECT id, username, email FROM users WHERE id = %s", [user_id])
                    user = cursor.fetchone()
                    if user:
                        return JsonResponse({
                            'id': user[0],
                            'username': user[1],
                            'email': user[2]
                        }, status=200)
                    else:
                        return JsonResponse({'message': 'User not found'}, status=404)
            except jwt.ExpiredSignatureError:
                return JsonResponse({'message': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'message': 'Invalid token'}, status=401)
         else:
            return JsonResponse({'message': 'Token not provided'}, status=400)

    return JsonResponse({'message': 'Invalid request method'}, status=405)