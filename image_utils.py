import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
import io

class ImageUtils:
    def __init__(self):
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.max_size = 5 * 1024 * 1024  # 5MB
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_hotel_image(self, file, hotel_id):
        """Save hotel image and return filename"""
        if file and self.allowed_file(file.filename):
            # Generate unique filename
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"hotel_{hotel_id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            # Create directory if not exists
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/hotels')
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            
            # Resize and optimize image
            self._optimize_image(file, filepath)
            
            return f"/static/uploads/hotels/{filename}"
        return None
    
    def save_room_image(self, file, room_id):
        """Save room image and return filename"""
        if file and self.allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"room_{room_id}_{uuid.uuid4().hex[:8]}.{ext}"
            
            upload_dir = os.path.join(current_app.root_path, 'static/uploads/rooms')
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            self._optimize_image(file, filepath)
            
            return f"/static/uploads/rooms/{filename}"
        return None
    
    def _optimize_image(self, file, filepath):
        """Optimize image size and quality"""
        try:
            # Open image
            image = Image.open(file.stream)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            
            # Resize if too large
            max_size = (1200, 800)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            image.save(filepath, 'JPEG', quality=85, optimize=True)
            
        except Exception as e:
            # Fallback to original file
            file.seek(0)
            file.save(filepath)

# Global instance
image_utils = ImageUtils()