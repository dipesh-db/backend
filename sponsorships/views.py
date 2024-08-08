from django.http import JsonResponse
from django.db import connection
import json
from django.views.decorators.csrf import csrf_exempt
from authentication.utils import jwt_authentication_required

@csrf_exempt
@jwt_authentication_required
def sponsor_event(request, event_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        sponsor_id = request.user_id  
        name = data.get('name')
        contact_number = data.get('contact_number')
        amount = float(data.get('amount'))

        if not name or not contact_number or not amount:
            return JsonResponse({'message': 'Missing name, contact_number, or amount'}, status=400)

        with connection.cursor() as cursor:
            try:
                # Check if the sponsor is already sponsoring this event
                cursor.execute("""
                    SELECT id FROM sponsorships
                    WHERE event_id = %s AND sponsor_id = %s
                """, [event_id, sponsor_id])
                if cursor.fetchone():
                    return JsonResponse({'message': 'Sponsor already sponsoring this event'}, status=400)

                # Add sponsor to event sponsorships
                cursor.execute("""
                    INSERT INTO sponsorships (event_id, sponsor_id, name, contact_number, amount)
                    VALUES (%s, %s, %s, %s, %s)
                """, [event_id, sponsor_id, name, contact_number, amount])
                return JsonResponse({'message': 'Successfully sponsored the event'}, status=201)
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method'}, status=405)


@jwt_authentication_required
def get_user_sponsored_events(request):
    if request.method == 'GET':
        user_id = request.user_id  
        
        if not user_id:
            return JsonResponse({'message': 'User ID is required'}, status=400)
        
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT e.id, e.name, e.description, e.category_id, e.event_time, e.event_date, e.venue, e.price
                    FROM events e
                    INNER JOIN sponsorships s ON e.id = s.event_id
                    WHERE s.sponsor_id = %s
                    AND e.event_date >= NOW()
                    ORDER BY e.event_date
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
            except Exception as e:
                return JsonResponse({'message': str(e)}, status=500)
    
    return JsonResponse({'message': 'Invalid request method'}, status=405)
