import requests
import json
from datetime import datetime

class WhatsAppService:
    def __init__(self):
        # You can use services like Twilio, WhatsApp Business API, or custom solutions
        self.api_url = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json"  # Example for Twilio
        self.auth_token = "your_auth_token"
        
    def send_booking_notification_to_owner(self, hotel, booking, customer):
        """Send booking notification to hotel owner"""
        message = f"""
🏨 *නව බුකින්ග් ඇලර්ම්!*

*හොටෙල්:* {hotel.name}
*බුකින්ග් ID:* #{booking.id}

*අමුත්තන්ගේ විස්තර:*
👤 නම: {booking.guest_name}
📞 දුරකථන: {booking.guest_phone}
📧 ඊමේල්: {booking.guest_email}

*බුකින්ග් විස්තර:*
📅 Check-in: {booking.check_in_date}
📅 Check-out: {booking.check_out_date}
💰 මුළු මිල: රු. {booking.total_price:,.2f}
📊 තත්වය: {booking.status}

*හොටෙල් විස්තර:*
🏢 {hotel.name}
📍 {hotel.location}
📞 {hotel.contact_number}

බුකින්ග් තොරතුරු සම්පූර්ණයෙන් බැලීමට ඔබගේ උපකරණ පුවරුවට පිවිසෙන්න.
        """
        
        return self._send_whatsapp(hotel.whatsapp_number, message)
    
    def send_booking_confirmation_to_customer(self, hotel, booking):
        """Send booking confirmation to customer"""
        message = f"""
✅ *ඔබගේ බුකින්ග් තහවුරු කරන ලදී!*

*බුකින්ග් තොරතුරු:*
🆔 බුකින්ග් ID: #{booking.id}
🏨 හොටෙල්: {hotel.name}
📍 ස්ථානය: {hotel.location}

*ඔබගේ විස්තර:*
👤 නම: {booking.guest_name}
📞 දුරකථන: {booking.guest_phone}

*බුකින්ග් විස්තර:*
📅 Check-in: {booking.check_in_date}
📅 Check-out: {booking.check_out_date}
⏰ Check-in time: 2:00 PM
⏰ Check-out time: 11:00 AM
💰 මුළු මිල: රු. {booking.total_price:,.2f}

*හොටෙල් සම්බන්ධතා:*
📞 {hotel.contact_number}
📍 {hotel.location}

*උපදෙස්:*
• Check-in වේලාවට පෙර හොටෙල් වෙත පැමිණෙන්න
• ඔබගේ ජාතික හැඳුනුම්පත රැගෙන එන්න
• විශේෂ අවශ්‍යතා තිබේනම් කල්තියා දන්වන්න

සාදරයෙන් පිළිගනිමු! 🙏
        """
        
        return self._send_whatsapp(booking.guest_whatsapp, message)
    
    def send_booking_update_to_customer(self, hotel, booking, update_type):
        """Send booking update to customer"""
        if update_type == "cancelled":
            message = f"""
❌ *ඔබගේ බුකින්ග් අවලංගු කරන ලදී*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}
ස්ථානය: {hotel.location}

ඔබගේ බුකින්ග් සාර්ථකව අවලංගු කරන ලදී.

අමතර තොරතුරු සඳහා: {hotel.contact_number}
            """
        elif update_type == "modified":
            message = f"""
✏️ *ඔබගේ බුකින්ග් යාවත්කාලීන කරන ලදී*

බුකින්ග් ID: #{booking.id}
හොටෙල්: {hotel.name}

ඔබගේ බුකින්ග් විස්තර යාවත්කාලීන කරන ලදී.

යාවත්කාලීන විස්තර:
Check-in: {booking.check_in_date}
Check-out: {booking.check_out_date}
මිල: රු. {booking.total_price:,.2f}

අමතර තොරතුරු: {hotel.contact_number}
            """
        
        return self._send_whatsapp(booking.guest_whatsapp, message)
    
    def _send_whatsapp(self, to_number, message):
        """Actual WhatsApp sending implementation"""
        try:
            # For demo purposes, we'll print the message
            # In production, integrate with WhatsApp Business API or Twilio
            print(f"📱 WhatsApp Message to {to_number}:")
            print(message)
            print("-" * 50)
            
            # Example with Twilio (uncomment and configure for production)
            """
            from twilio.rest import Client
            
            account_sid = 'your_account_sid'
            auth_token = 'your_auth_token'
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                from_='whatsapp:+14155238886',  # Twilio WhatsApp number
                body=message,
                to=f'whatsapp:{to_number}'
            )
            """
            
            return True
        except Exception as e:
            print(f"WhatsApp sending failed: {e}")
            return False

# Global instance
whatsapp_service = WhatsAppService()