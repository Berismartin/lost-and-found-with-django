# Lost & Found Django Application

A comprehensive Django-based lost and found application that helps people reunite with their belongings through community collaboration.

## Features

### User Authentication & Profiles
- ✅ Custom user registration and login system
- ✅ User profile management with profile pictures
- ✅ Secure authentication with Django's built-in system
- ✅ Profile editing with personal information

### Item Management
- ✅ Post lost and found items with detailed descriptions
- ✅ Upload item photos
- ✅ Category-based organization (Electronics, Clothing, Jewelry, etc.)
- ✅ Location and date tracking
- ✅ Status management (Lost, Found, Claimed)
- ✅ Item search and filtering functionality

### User Interface
- ✅ Modern, responsive design using custom CSS
- ✅ Professional color palette:
  - Primary Blue: #0A2342
  - Secondary Orange: #FF9F1C  
  - Neutral Gray: #D9D9D9
  - Text Black: #171717
  - Success Green: #4CAF50
  - Error Red: #E53935
- ✅ Clean card-based layout
- ✅ Mobile-responsive design

## Project Structure

```
lostandfound/
├── lostandfound/          # Main project settings
│   ├── settings.py        # Django configuration
│   ├── urls.py           # Main URL routing
│   └── ...
├── users/                 # User authentication app
│   ├── models.py         # User and UserProfile models
│   ├── views.py          # Authentication views
│   ├── forms.py          # User forms
│   ├── admin.py          # Admin configuration
│   └── urls.py           # User URL patterns
├── items/                 # Item management app
│   ├── models.py         # Item model
│   ├── views.py          # Item CRUD views
│   ├── forms.py          # Item forms
│   ├── admin.py          # Admin configuration
│   └── urls.py           # Item URL patterns
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── users/            # User templates
│   └── items/            # Item templates
├── static/               # Static files
│   └── css/
│       └── style.css     # Custom CSS with color palette
├── media/                # User uploaded files
│   ├── profile_pictures/ # Profile images
│   └── item_images/      # Item photos
└── requirements.txt      # Project dependencies
```

## Installation & Setup

1. **Clone the repository and navigate to the project directory**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the application:**
   - Main site: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/

## Usage

### For Regular Users
1. **Register** for a new account or **login** with existing credentials
2. **Browse items** to see what's been lost or found
3. **Post items** by providing detailed descriptions and photos
4. **Manage your posts** through the "My Items" section
5. **Update your profile** with contact information

### For Administrators
- Access the Django admin interface to manage users and items
- Monitor site activity and moderate content
- View detailed analytics and user information

## Key URLs

- `/` - Home page with recent items
- `/items/` - Browse all items with search and filters
- `/items/create/` - Post a new lost/found item
- `/users/register/` - User registration
- `/users/login/` - User login
- `/users/profile/` - View user profile
- `/my-items/` - Manage personal item posts

## Models

### User Model
- Extends Django's AbstractUser
- Additional fields: email (unique), first_name, last_name

### UserProfile Model
- One-to-one relationship with User
- Fields: profile_picture, bio, phone_number, location, date_of_birth

### Item Model
- Core model for lost/found items
- Fields: title, description, category, status, image, location, date, contact_info
- Relationships: ForeignKey to User
- Status choices: Lost, Found, Claimed
- Category choices: Electronics, Clothing, Jewelry, Documents, Keys, Bags, Books, Sports, Toys, Other

## Security Features

- CSRF protection on all forms
- User authentication required for posting/editing items
- Image file validation and resizing
- Secure file upload handling
- Permission-based access control

## Development Notes

- Built with Django 5.2.5
- Uses SQLite for development (easily configurable for production databases)
- Responsive design works on desktop and mobile devices
- Image processing with Pillow for automatic resizing
- Clean separation of concerns with Django apps

## Future Enhancements

Potential features for future development:
- Email notifications for matches
- Advanced search with location-based filtering
- Message system between users
- Item matching suggestions
- Social media integration
- Mobile app development

---

This application successfully implements all the requirements from the original task specification, providing a complete lost and found management system with user authentication, item management, and a professional user interface.
