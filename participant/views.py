from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.db import connection
from authentication.utils import jwt_authentication_required

@csrf_exempt  
@jwt_authentication_required
def join_event(request, event_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = request.user_id
        name=data.get('name')
        contact_number=data.get('contact_number')

        if not user_id:
            return JsonResponse({'message': 'User ID is required'}, status=400)

        with connection.cursor() as cursor:
            try:
                # Check if the event exists
                cursor.execute("SELECT id FROM events WHERE id = %s", [event_id])
                if not cursor.fetchone():
                    return JsonResponse({'message': 'Event not found'}, status=404)

                # Check if the user is already participating
                cursor.execute("""
                    SELECT id FROM participations
                    WHERE event_id = %s AND user_id = %s
                """, [event_id, user_id])
                if cursor.fetchone():
                    return JsonResponse({'message': 'User already participating in this event'}, status=400)

                # Add user to event participants
                cursor.execute("""
                    INSERT INTO participations (event_id, user_id,name,contact_number)
                    VALUES (%s, %s,%s,%s)
                """, [event_id, user_id,name,contact_number])
                return JsonResponse({'message': 'Successfully joined the event'}, status=201)
            except Exception as e:
                return JsonResponse({'message': 'Error joining the event'}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)

@jwt_authentication_required
def get_participated_events(request):
    if request.method == 'GET':
        user_id = request.user_id

        if not user_id:
            return JsonResponse({'message': 'User ID is required'}, status=400)

        with connection.cursor() as cursor:
            try:
                # Fetch events the user has participated in
                cursor.execute("""
                    SELECT e.id, e.name, e.description, e.event_date,e.event_time, e.venue, e.category_id,e.price
                    FROM events e
                    INNER JOIN participations p ON e.id = p.event_id
                    WHERE p.user_id = %s
                """, [user_id])

                events = cursor.fetchall()

                #fetched data into a list of dictionaries
                event_list = []
                for event in events:
                    event_list.append({
                        'id': event[0],
                        'name': event[1],
                        'description': event[2],
                        'event_date': event[3],
                        'event_time': event[4],
                        'venue': event[5],
                        'category_id': event[6],
                        'price':event[7]
                    })

                return JsonResponse({'events': event_list}, status=200)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)
