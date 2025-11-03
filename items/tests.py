from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from items.models import Item, ItemImage, Report, Comment, Conversation
from users.models import UserPoints

User = get_user_model()


def make_image_file(name="test.jpg", content=b"\x47\x49\x46"):
    return SimpleUploadedFile(name, content, content_type="image/jpeg")


class TestItemModelsGivenWhenThen(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="pass", email="u1@example.com")

    def test_given_item_with_defaults_when_str_called_then_returns_status_and_title_it_is_human_readable(self):
        item = Item.objects.create(title="Wallet", description="Black", category="other", user=self.user)
        self.assertIn("Lost: Wallet", str(item))

    def test_given_item_with_legacy_and_extra_images_when_query_images_then_counts_match_it_includes_all(self):
        item = Item.objects.create(title="Phone", description="desc", user=self.user)
        # initially none
        self.assertIsNone(item.main_image)
        self.assertEqual(item.get_all_images(), [])
        # add legacy
        item.image = make_image_file("legacy.jpg")
        item.save()
        self.assertIsNotNone(item.main_image)
        # add additional
        ItemImage.objects.create(item=item, image=make_image_file("a1.jpg"), order=1)
        ItemImage.objects.create(item=item, image=make_image_file("a2.jpg"), order=2)
        self.assertEqual(len(item.get_all_images()), 3)


class TestItemViewsGivenWhenThen(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(username="owner", password="pass", email="o@example.com")
        self.other = User.objects.create_user(username="other", password="pass", email="x@example.com")
        self.item = Item.objects.create(
            title="Bag", description="Blue bag", category="bags", status="lost", user=self.owner, is_active=True
        )

    def test_given_anonymous_user_when_open_create_item_then_redirects_to_login_it_blocks_unauthenticated(self):
        resp = self.client.get(reverse("create_item"))
        self.assertEqual(resp.status_code, 302)


##################
    def test_given_logged_in_owner_when_create_and_add_additional_images_then_images_persist_it_orders_sequentially(self):
        self.client.login(username="owner", password="pass")
        # create minimal item first
        resp = self.client.post(
            reverse("create_item"),
            {
                "title": "Watch",
                "description": "silver",
                "category": "jewelry",
                "status": "lost",
                "location_lost_found": "",
                "contact_info": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        created = Item.objects.get(title="Watch")
        # now add additional images on edit
        files = [make_image_file("i1.jpg"), make_image_file("i2.jpg")]
        post_data = {
            "title": "Watch",
            "description": "silver",
            "category": "jewelry",
            "status": "lost",
            "location_lost_found": "",
            "contact_info": "",
            "additional_images": files,
        }
        resp2 = self.client.post(
            reverse("edit_item", args=[created.pk]),
            post_data,
            follow=True,
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(created.item_images.count(), 2)
        orders = list(created.item_images.values_list("order", flat=True))
        self.assertEqual(orders, sorted(orders))

    def test_given_non_owner_when_access_edit_then_gets_404_it_enforces_ownership(self):
        self.client.login(username="other", password="pass")
        resp = self.client.get(reverse("edit_item", args=[self.item.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_given_owner_when_post_delete_then_item_removed_it_disappears_from_db(self):
        self.client.login(username="owner", password="pass")
        resp = self.client.post(reverse("delete_item", args=[self.item.pk]), follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

#######
    def test_given_filters_when_browse_item_list_then_results_match_it_applies_search_category_status(self):
        Item.objects.create(title="Keys", description="car keys", category="keys", status="found", user=self.owner)
        # search
        resp = self.client.get(reverse("item_list"), {"search": "car"})
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.context["page_obj"].paginator.count, 1)
        # category
        resp = self.client.get(reverse("item_list"), {"category": "bags"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(i.category == "bags" for i in resp.context["page_obj"].object_list))
        # status
        resp = self.client.get(reverse("item_list"), {"status": "lost"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(all(i.status == "lost" for i in resp.context["page_obj"].object_list))

    def test_given_owner_when_change_status_to_found_then_value_updates_it_returns_success(self):
        self.client.login(username="owner", password="pass")
        resp = self.client.post(reverse("change_item_status", args=[self.item.pk]), {"status": "found"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "found")

    def test_given_invalid_status_when_change_item_status_then_redirects_it_shows_error_message(self):
        self.client.login(username="owner", password="pass")
        resp = self.client.post(reverse("change_item_status", args=[self.item.pk]), {"status": "nope"})
        self.assertEqual(resp.status_code, 302)

    def test_given_owner_confirmation_when_mark_returned_then_points_awarded_it_increments_user_points(self):
        self.client.login(username="owner", password="pass")
        resp = self.client.post(
            reverse("change_item_status", args=[self.item.pk]),
            {"status": "returned_to_owner", "confirmed_by_owner": "true"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, "returned_to_owner")
        owner_points = UserPoints.objects.get(user=self.owner)
        self.assertGreaterEqual(owner_points.points, 10)

    def test_given_authenticated_user_when_report_item_then_report_created_it_persists_reason(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse("report_item", args=[self.item.pk]), {"reason": "spam"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Report.objects.filter(item=self.item, reporter=self.other).exists())

    def test_given_comment_when_reply_posted_then_reply_linked_it_appears_under_parent(self):
        self.client.login(username="other", password="pass")
        resp = self.client.post(reverse("add_comment", args=[self.item.pk]), {"content": "hello"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        comment = Comment.objects.get(item=self.item, parent__isnull=True)
        resp2 = self.client.post(
            reverse("add_reply", args=[self.item.pk, comment.pk]), {"content": "reply"}, follow=True
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(comment.replies.exists())

    def test_given_participants_when_start_and_chat_then_messages_visible_it_lists_in_inbox(self):
        self.client.login(username="owner", password="pass")
        resp = self.client.get(reverse("start_conversation", args=[self.other.id]) + f"?item_id={self.item.id}")
        self.assertEqual(resp.status_code, 302)
        conv = Conversation.objects.first()
        resp2 = self.client.get(reverse("conversation_detail", args=[conv.id]))
        self.assertEqual(resp2.status_code, 200)
        resp3 = self.client.post(reverse("send_message", args=[conv.id]), {"content": "Hi"}, follow=True)
        self.assertEqual(resp3.status_code, 200)
        self.assertTrue(conv.messages.exists())
        resp4 = self.client.get(reverse("inbox"))
        self.assertEqual(resp4.status_code, 200)
        self.assertIn("conversations", resp4.context)
