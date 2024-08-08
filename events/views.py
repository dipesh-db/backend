from django.shortcuts import render

from django.db import connection
import json
from django.http import JsonResponse
from authentication.utils import jwt_authentication_required
from datetime import datetime


# Create your views here.

@jwt_authentication_required
def create_event(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description')
            venue = data.get('venue')
            event_date = data.get('event_date')
            event_time = data.get('event_time')
            price = data.get('price')
            category_id = data.get('category_id')

            
            organizer_id = request.user_id
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO events(name, description, venue, organizer_id, created_at, 
                                       category_id, event_time, price, event_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [name, description, venue, organizer_id, created_at, 
                      category_id, event_time, price, event_date])
                event_id = cursor.fetchone()[0]
                

            return JsonResponse({'message': 'Event Created Successfully', 'event_id': event_id}, status=201)
        except Exception as e:
           
            return JsonResponse({'error': str(e)}, status=400)
    else:
      
        return JsonResponse({'message': 'Invalid request method'}, status=405)



@jwt_authentication_required
def edit_event(request, event_id):
    if request.method == "PUT":
        data = json.loads(request.body)
        
        # Start with the existing event data
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name, description,event_date,event_time,venue, category_id,price
                FROM events
                WHERE id = %s AND organizer_id = %s
            """, [event_id, request.user_id])
            
            existing_event = cursor.fetchone()
            if not existing_event:
                return JsonResponse({'message': 'Event not found or you do not have permission to edit it'}, status=404)
            
            # Create a dictionary of the existing event data
            event_data = {
                'name': existing_event[0],
                'description': existing_event[1],
                'event_date':existing_event[2],
                'event_time':existing_event[3],
                'venue': existing_event[4],
                'category_id': existing_event[5],
                'price':existing_event[6]
            }

            
        
        # Update only the fields that are provided in the request
        for field in event_data:
            if field in data:
                event_data[field] = data[field]

               
        
        # Update the event with the new data
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    UPDATE events
                    SET name = %s, description = %s, event_date=%s,event_time=%s, venue = %s, category_id = %s,price=%s
                    WHERE id = %s AND organizer_id = %s
                    RETURNING id
                """, [event_data['name'], event_data['description'], event_data['event_date'], 
                      event_data['event_time'], event_data['venue'], event_data['category_id'],event_data['price'],
                      event_id, request.user_id])
                
                if cursor.rowcount == 0:
                    return JsonResponse({'message': 'Event not found or you do not have permission to edit it'}, status=404)
                
                return JsonResponse({'message': 'Event updated successfully'}, status=200)
            
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=400)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)







def get_upcoming_events(request):
    if request.method == 'GET':
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT e.id, e.name, e.description, e.category_id, e.event_time, e.event_date, e.venue, e.price,
                           ARRAY_AGG(s.name) AS sponsor_names
                    FROM events e
                    LEFT JOIN sponsorships s ON e.id = s.event_id
                    WHERE e.event_date >= NOW()
                    GROUP BY e.id, e.name, e.description, e.category_id, e.event_time, e.event_date, e.venue, e.price
                    ORDER BY e.event_date
                    LIMIT 10
                """)
                events = cursor.fetchall()
                
                event_list = [
                    {
                        'id': event[0],
                        'name': event[1],
                        'description': event[2],
                        'category_id': event[3],
                        'event_time': event[4],
                        'event_date': event[5],
                        'venue': event[6],
                        'price': event[7],
                        'sponsor_names': event[8]  
                    }
                    for event in events
                ]
                
                return JsonResponse({'events': event_list})
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)




@jwt_authentication_required
def get_user_created_events(request):
    if request.method == 'GET':
        user_id = request.user_id  
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, description, category_id, event_time, event_date, venue, price
                FROM events
                WHERE event_date >= NOW()
                AND organizer_id = %s
                ORDER BY event_date
                LIMIT 5
            """, [user_id])
            events = cursor.fetchall()
            
            event_list = [
                {
                    'id': event[0],
                    'name': event[1],
                    'description': event[2],
                    'category_id': event[3],
                    'event_time': event[4],
                    'event_date': event[5],
                    'venue': event[6],
                    'price': event[7]
                }
                for event in events
            ]


            
            
            return JsonResponse({'events': event_list})
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)



@jwt_authentication_required
def delete_event(request, event_id):
    
    if request.method == "DELETE":
        user_id = request.user_id
        try:
            # Check if the event exists and the user has permission to delete it
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id
                    FROM events
                    WHERE id = %s AND organizer_id = %s
                """, [event_id, user_id])
                
                if cursor.rowcount == 0:
                    return JsonResponse({'message': 'Event not found or you do not have permission to delete it'}, status=404)
                
                # Delete the event
                cursor.execute("""
                    DELETE FROM events
                    WHERE id = %s
                """, [event_id])
                
                if cursor.rowcount == 0:
                    return JsonResponse({'message': 'Event not found or could not be deleted'}, status=404)
                
                return JsonResponse({'message': 'Event deleted successfully'}, status=200)
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)


