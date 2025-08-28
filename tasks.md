Assignments 
 User & Item Core
Module 1: User Authentication & Profiles
Models:
User Model: Extend AbstractUser to create a custom User model.
Profile Model: Define a UserProfile model with a OneToOneField to the User model. Include fields for profile_picture and other relevant data.
Controllers (Views):
register_user: A view to handle user registration, processing the form data and creating a new user instance.
login_user: A view to authenticate and log in users.
logout_user: A view to log out the user.
profile_view: A view to display the user's profile and retrieve their associated data.
edit_profile: A view to handle form submission for updating the UserProfile model.
Templates:
registration.html: The form for new user sign-ups.
login.html: The form for user login.
profile.html: The template to display the user's profile information.
edit_profile.html: The form for users to update their profile details.
Module 2: Item Management
Models:
Item Model: Define the Item model with fields for title, description, category, image, and a ForeignKey to the User model.
Controllers (Views):
create_item: A view to handle the creation of a new item post.
item_detail: A view that fetches and displays a single item's details.
edit_item: A view to handle the form for updating an existing item.
delete_item: A view to remove an item from the database.
Templates:
create_item.html: The form for submitting a new lost or found item.
item_detail.html: The page that displays a single item's information, including the image and description.


---

### Sirajje: System Logic & Admin — Implemented Tasks

**1. Points & Status System**
- Expanded status choices for `Item` (`lost`, `found`, `claimed`, `returned_to_owner`, `archived`).
- Implemented dual confirmation (owner/finder) and logic for changing an item’s status, with a special flow for “Returned to Owner.”
- Awarded points to users for successful item returns; created the `UserPoints` model for tracking.
- Integrated status/points logic into both backend (views) and frontend (template forms and clear UI feedback).
- Styled status badges by status: `lost` (red), `found` (green), `claimed` (blue), `returned_to_owner` (blue/orange), `archived` (red), matching the project palette.

**2. Reporting & Admin Tools**
- Created a `Report` model for reporting fraudulent/inappropriate items.
- Added a user-facing reporting form and frontend “Report” button to the item detail page.
- Registered `Report`, `Item`, `ItemImage`, and `UserPoints` with custom logic and filtering in Django admin.
- Provided an admin action to mark reports as resolved from the admin panel.

**3. UI/UX Integration**
- Added and styled “Change Status” and “Report” buttons, as well as all related forms, according to the design palette.
- Ensured all major actions (status change, claim, report) are accessible from item_detail.html and that users see all major states visually.

**4. Project Consistency**
- Ensured all logic is fully integrated with existing CRUD, list, and detail flows for items.
- All routes, templates, models, and admin logic conform to Django best practices for robust, maintainable production code.

---

Color Palette
The color palette is professional, clean, and trustworthy. The primary colors are used for main elements like buttons and headers, while the secondary colors are for accents and backgrounds.
Primary Blue: #0A2342 (Dark and professional, for headers, buttons, and important text)
Secondary Orange: #FF9F1C (A vibrant, eye-catching accent for alerts, notifications, and calls to action)
Neutral Gray: #D9D9D9 (Light gray for backgrounds, borders, and separators)
Text & Icon Black: #171717 (Deep black for all body text and icons for high readability)
Success Green: #4CAF50 (For confirmation messages and positive feedback)
Error Red: #E53935 (For error messages and destructive actions like deletion)
Buttons:
Primary Button: Blue background (#0A2342), white text. Used for main actions like "Post Lost Item" or "Log In."
Secondary Button: White background, blue border (#0A2342), and blue text. Used for less critical actions like "Cancel" or "Edit."
Forms:
All input fields should have a light gray border (#D9D9D9) and a consistent height and padding.
Use a clear label above each input field
Icons Lucid react icons

