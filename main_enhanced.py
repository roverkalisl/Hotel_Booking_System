from hotel_management import HotelManagement
import os

def main():
    manager = HotelManagement()
    
    while True:
        print("\n" + "="*60)
        print("🏨 හොටෙල් මැනේජ්මන්ට් සිස්ටම්")
        print("="*60)
        print("1. 🆕 නව හොටෙල් ලියාපදිංචි කිරීම")
        print("2. 📋 සියලුම හොටෙල් බැලීම")
        print("3. 🔍 හොටෙල් සෙවීම")
        print("4. ✏️ හොටෙල් යාවත්කාලීන කිරීම")
        print("5. 🗑️ හොටෙල් ඉවත් කිරීම")
        print("6. 📊 සංඛ්‍යාලේඛන බැලීම")
        print("7. 🚪 පිටවීම")
        
        choice = input("\nඔබගේ තේරීම ඇතුළත් කරන්න (1-7): ")
        
        if choice == '1':
            manager.add_hotel()
        elif choice == '2':
            manager.view_all_hotels()
        elif choice == '3':
            manager.search_hotels()
        elif choice == '4':
            manager.update_hotel()
        elif choice == '5':
            manager.delete_hotel()
        elif choice == '6':
            manager.view_hotel_stats()
        elif choice == '7':
            print("\n✅ හොටෙල් මැනේජ්මන්ට් සිස්ටම් වසා දමමින්...")
            manager.close()
            break
        else:
            print("❌ කරුණාකර වලංගු තේරීමක් ඇතුළත් කරන්න (1-7)!")
        
        # Continue prompt
        if choice != '7':
            input("\nEnter බොත්තම ඔබන්න ඉදිරියට යාමට...")

def clear_screen():
    """Screen clear කිරීම"""
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    clear_screen()
    main()