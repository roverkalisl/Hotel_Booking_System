import os
from PIL import Image
import io
import base64

class ImageManager:
    def __init__(self, upload_folder='hotel_images'):
        self.upload_folder = upload_folder
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
    
    def process_image(self, image_path, max_size=(800, 600)):
        """ජයාරුපය process කිරීම - size reduce කිරීම"""
        try:
            with Image.open(image_path) as img:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='JPEG', quality=85)
                img_bytes = img_bytes.getvalue()
                
                return img_bytes
        except Exception as e:
            print(f"ජයාරුපය process කිරීමේ දෝෂය: {e}")
            return None
    
    def save_image_to_db(self, session, hotel, image_path):
        """ජයාරුපය database එකට save කිරීම"""
        try:
            image_data = self.process_image(image_path)
            if image_data:
                hotel.image_data = image_data
                hotel.image_filename = os.path.basename(image_path)
                hotel.image_content_type = 'image/jpeg'
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"ජයාරුපය save කිරීමේ දෝෂය: {e}")
            return False
    
    def get_image_base64(self, image_data):
        """ජයාරුපය base64 format එකට convert කිරීම (web display සඳහා)"""
        if image_data:
            return base64.b64encode(image_data).decode('utf-8')
        return None
    
    def save_image_to_file(self, image_data, filename):
        """ජයාරුපය file එකකට save කිරීම"""
        try:
            filepath = os.path.join(self.upload_folder, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            return filepath
        except Exception as e:
            print(f"ජයාරුපය file එකට save කිරීමේ දෝෂය: {e}")
            return None

# Simple image processor for console application
class ConsoleImageManager:
    @staticmethod
    def handle_image_upload(hotel, session):
        """Console application සඳහා ජයාරුප upload කිරීම"""
        print("\n--- ජයාරුපය එකතු කිරීම ---")
        print("වර්තමානයේදී ඔබට image path එක enter කිරීමට හැකිය.")
        print("පරීක්ෂා කිරීම සඳහා ඔබට මෙම sample images භාවිතා කළ හැකිය:")
        print("1. ජයාරුපය නොමැතිව ඉදිරියට යන්න")
        print("2. පසුව ජයාරුපය එකතු කිරීම")
        
        choice = input("ඔබගේ තේරීම (1/2): ")
        
        if choice == '1':
            image_path = input("ජයාරුපයේ path එක ඇතුලත් කරන්න: ")
            
            if os.path.exists(image_path):
                image_manager = ImageManager()
                if image_manager.save_image_to_db(session, hotel, image_path):
                    print("✅ ජයාරුපය සාර්ථකව එකතු කරන ලදී!")
                else:
                    print("❌ ජයාරුපය එකතු කිරීම අසාර්ථක විය!")
            else:
                print("❌ ජයාරුපය හමු නොවීය!")
        else:
            print("ජයාරුපය එකතු නොකර ඉදිරියට යනවා...")