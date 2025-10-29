import requests
import json
from datetime import datetime

class WhatsAppService:
    def __init__(self):
        # For production, use Twilio WhatsApp Business API
        # For testing, we'll use a mock service
        self.test_mode = True
        
    def send_booking_notification_to_owner(self, hotel, booking, customer):
        """Send booking notification to hotel owner with rich details"""
        message = f"""
🏨 *නව බුකින්ග් ඇලර්ම්!* 📱

*හොටෙල්:* {hotel.name}
*බුකින්ග් ID:* #{booking.id}

*👥 අමුත්තන්ගේ විස්තර:*
• නම: {booking.guest_name}
• දුරකථන: {booking.guest_phone}
• WhatsApp: {booking.guest_whatsapp}
• ඊමේල්: {booking.guest_email}
• ගෙනයන අය: {booking.number_of_guests} ක්

*📅 බුකින්ග් විස්තර:*
• Check-in: {booking.check_in_date}
• Check-out: {booking.check_out_date}
• රාත්‍රි: {booking.get_nights()} ක්
• මුළු මිල: රු. {booking.total_price:,.2f}
• තත්වය: {booking.status}

*💰 මුදල් විස්තර:*
• එක් රාත්‍රිය: රු. {hotel.price_per_night:,.2f}
• මුළු මිල: රු. {booking.total_price:,.2f}

*🏢 හොටෙල් විස්තර:*
• {hotel.name}
• {hotel.location}
• {hotel.contact_number}

*📝 විශේෂ ඉල්ලීම්:*
{booking.special_requests if booking.special_requests else 'විශේෂ ඉල්ලීම් නොමැත'}

*🔔 ඊළඟ පියවර:*
1. බුකින්ග් තහවුරු කරන්න
2. අමුත්තන්ට පිළිගැනීමේ පණිවිඩයක් යවන්න
3. කාමරය සූදානම් කරන්න

බුකින්ග් තොරතුරු සම්පූර්ණයෙන් බැලීමට ඔබගේ උපකරණ පුවරුවට පිවිසෙන්න.
        """
        
        return self._send_whatsapp(hotel.whatsapp_number, message, "BOOKING_ALERT")
    
    def send_booking_confirmation_to_customer(self, hotel, booking):
        """Send detailed booking confirmation to customer"""
        nights = booking.get_nights()
        
        message = f"""
✅ *ඔබගේ බුකින්ග් තහවුරු කරන ලදී!* 🎉

*📋 බුකින්ග් තොරතුරු:*
• බුකින්ග් ID: #{booking.id}
• හොටෙල්: {hotel.name}
• ස්ථානය: {hotel.location}

*👤 ඔබගේ විස්තර:*
• නම: {booking.guest_name}
• දුරකථන: {booking.guest_phone}
• ගෙනයන අය: {booking.number_of_guests} ක්

*📅 රැස්වීම් වේලා:*
• Check-in: {booking.check_in_date} (2:00 PM සිට)
• Check-out: {booking.check_out_date} (11:00 AM වන තෙක්)
• රාත්‍රි: {nights} ක්

*💰 මුදල් විස්තර:*
• එක් රාත්‍රිය: රු. {hotel.price_per_night:,.2f}
• මුළු මිල: රු. {booking.total_price:,.2f}

*🏨 හොටෙල් සම්බන්ධතා:*
• දුරකථන: {hotel.contact_number}
• ස්ථානය: {hotel.location}
• WhatsApp: {hotel.whatsapp_number}

*📝 විශේෂ ඉල්ලීම්:*
{booking.special_requests if booking.special_requests else 'විශේෂ ඉල්ලීම් නොමැත'}

*🎯 ප්‍රධාන උපදෙස්:*
• Check-in වේලාවට පෙර හොටෙල් වෙත පැමිණෙන්න
• ජාතික හැඳුනුම්පත/පාස්පෝට් අනිවාර්යයෙන් රැගෙන එන්න
• විශේෂ අවශ්‍යතා තිබේනම් කල්තියා දන්වන්න
• කාමරයේ ද්‍රව්‍ය කිසිවක් විනාශ නොකරන්න

*❓ උදවු අවශ්‍යද?*
අපගේ සේවා දායක කණ්ඩායම ඔබට උදව් කිරීමට සුදානම්. 
දුරකථන: {hotel.contact_number}

සාදරයෙන් පිළිගනිමු! 🙏
ඔබගේ නවාදැක්ම අපට ගෞරවයකි.
        """
        
        return self._send_whatsapp(booking.guest_whatsapp, message, "BOOKING_CONFIRMATION")
    
    def send_booking_cancellation_notification(self, hotel, booking, cancelled_by_owner=False):
        """Send cancellation notifications to both parties"""
        if cancelled_by_owner:
            # Notification to customer
            customer_message = f"""
❌ *ඔබගේ බුකින්ග් අවලංගු කරන ලදී*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}

කණගාටුයි! තාක්ෂණික හේතු නිසා ඔබගේ බුකින්ග් අවලංගු කිරීමට සිදු විය.

*💰 ආපසු ගෙවීම:*
ඔබගේ මුළු මිල රු. {booking.total_price:,.2f} සම්පූර්ණයෙන් ආපසු ලබා දෙනු ලැබේ.

*📞 වැඩිදුර තොරතුරු:*
{hotel.contact_number}

අසහනයට අපි සමාව ත්‍යාග කරමු.
            """
            
            self._send_whatsapp(booking.guest_whatsapp, customer_message, "CANCELLATION_BY_OWNER")
            
        else:
            # Notification to owner about customer cancellation
            owner_message = f"""
📢 *බුකින්ග් අවලංගු කිරීම*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}

අමුත්තන් විසින් බුකින්ග් අවලංගු කර ඇත.

*අමුත්තන්ගේ විස්තර:*
• නම: {booking.guest_name}
• දුරකථන: {booking.guest_phone}

*බුකින්ග් විස්තර:*
• Check-in: {booking.check_in_date}
• Check-out: {booking.check_out_date}
• මුළු මිල: රු. {booking.total_price:,.2f}

කාමරය නැවත තිබෙන කාමර ලයිස්ටුවට එක් කර ඇත.
            """
            
            self._send_whatsapp(hotel.whatsapp_number, owner_message, "CANCELLATION_BY_CUSTOMER")
    
    def send_reminder_notification(self, hotel, booking, days_before):
        """Send reminder notifications"""
        if days_before == 1:
            # 1 day before check-in reminder
            message = f"""
🔔 *ඔබගේ රැස්වීමට රාත්‍රියක් පමණක් ගතවී ඇත!*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}

*රැස්වීම් විස්තර:*
• Check-in: {booking.check_in_date} (2:00 PM)
• Check-out: {booking.check_out_date} (11:00 AM)
• ස්ථානය: {hotel.location}

*සූදානම් වන්න:*
• ඔබගේ අනන්‍යතා බලපත්‍රය රැගෙන එන්න
• විශේෂ අවශ්‍යතා තිබේනම් කල්තියා දන්වන්න

*හොටෙල් සම්බන්ධතා:*
📞 {hotel.contact_number}
📍 {hotel.location}

සාදරයෙන් පිළිගනිමු! 🏨
            """
            
            self._send_whatsapp(booking.guest_whatsapp, message, "REMINDER_1_DAY")
        
        elif days_before == 7:
            # 7 days before check-in reminder
            message = f"""
📅 *ඔබගේ රැස්වීමට සතියක් පමණක් ගතවී ඇත!*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}

ඔබගේ රැස්වීම සඳහා සූදානම් වීමට මතක් කරමු.

*රැස්වීම් විස්තර:*
• Check-in: {booking.check_in_date}
• Check-out: {booking.check_out_date}
• රාත්‍රි: {booking.get_nights()} ක්

සාදරයෙන් පිළිගනිමු! 🙏
            """
            
            self._send_whatsapp(booking.guest_whatsapp, message, "REMINDER_7_DAYS")
    
    def _send_whatsapp(self, to_number, message, message_type):
        """Actual WhatsApp sending implementation"""
        try:
            if self.test_mode:
                # Print to console for testing
                print("\n" + "="*60)
                print(f"📱 WHATSAPP {message_type} to {to_number}")
                print("="*60)
                print(message)
                print("="*60)
                
                # Simulate API call delay
                import time
                time.sleep(1)
                
                return {
                    'success': True,
                    'message_id': f'test_{datetime.now().timestamp()}',
                    'to': to_number,
                    'type': message_type
                }
            else:
                # Production: Integrate with Twilio WhatsApp Business API
                """
                from twilio.rest import Client
                
                account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
                
                client = Client(account_sid, auth_token)
                
                message = client.messages.create(
                    from_=f'whatsapp:{from_number}',
                    body=message,
                    to=f'whatsapp:{to_number}'
                )
                
                return {
                    'success': True,
                    'message_id': message.sid,
                    'to': to_number,
                    'type': message_type
                }
                """
                return {'success': True, 'message': 'WhatsApp integration not configured'}
                
        except Exception as e:
            print(f"WhatsApp sending failed: {e}")
            return {'success': False, 'error': str(e)}

# Global instance
whatsapp_service = WhatsAppService()