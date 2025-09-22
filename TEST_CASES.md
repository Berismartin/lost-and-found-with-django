## Regression Test Cases (given_when_then_it)

### Items app
- given item defaults when str called then returns status and title it is human readable
  - Ensures `Item.__str__` shows human status and title with default values.
- given legacy and extra images when querying images then counts match it includes all
  - Validates `main_image` and `get_all_images` include legacy and additional images.
- given anonymous user when opening create item then redirects to login it blocks unauthenticated
  - Verifies `create_item` is protected by login and redirects unauthenticated users.
- given logged-in owner when create and add additional images then images persist it orders sequentially
  - Confirms multiple image upload on edit persists and maintains sequential ordering.
- given non-owner when accessing edit then gets 404 it enforces ownership
  - Only the item owner can access `edit_item`; others get 404 (security).
- given owner when posting delete then item removed it disappears from db
  - Checks delete flow removes the record and redirects appropriately.
- given filters when browsing item list then results match it applies search category status
  - Asserts `item_list` applies search, category, and status filters.
- given owner when changing status to found then value updates it returns success
  - Confirms status update path changes to a valid status.
- given invalid status when changing item status then redirects it shows error message
  - Invalid status is rejected with redirect and message.
- given owner confirmation when marking returned then points awarded it increments user points
  - Owner confirming return changes status and awards points per current logic.
- given comment when reply posted then reply linked it appears under parent
  - Posting a reply creates a child comment linked to the parent.
- given participants when start and chat then messages visible it lists in inbox
  - Conversation creation, messaging, and inbox listing work for participants.

### Users app
- given valid registration when submit form then profile created it logs user in
  - Registers a user, auto-creates profile, and logs them in with redirect.
- given valid credentials and next when login then redirects it respects next param
  - Login honors `next` parameter and redirects accordingly.
- given logged-in user when logout then redirects to login it clears session
  - Logout ends the session and redirects to login page.
- given missing profile when view profile then autocreates it shows page
  - Visiting profile creates a `UserProfile` if missing.
- given valid forms when edit profile then updates user it persists changes
  - Submitting user and profile forms saves updates (e.g., first_name).

Run tests:

```bash
source venv/bin/activate
python manage.py test -v 2
```


