import json
import re
import uuid

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from rest_framework_simplejwt.tokens import RefreshToken
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import Select, WebDriverWait

from apps.blood.models import BloodRequest, DonationHistory, DonorProfile
from apps.notifications.models import Notification
from apps.ratings.models import Rating


User = get_user_model()
WAIT_SECONDS = 8


class ArnobSeleniumTests(StaticLiveServerTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		options = webdriver.EdgeOptions()
		options.add_argument("--headless=new")
		options.add_argument("--disable-gpu")
		options.add_argument("--window-size=1440,1000")
		cls.browser = webdriver.Edge(options=options)
		cls.browser.set_page_load_timeout(20)

	@classmethod
	def tearDownClass(cls):
		try:
			cls.browser.quit()
		finally:
			super().tearDownClass()

	def setUp(self):
		super().setUp()
		self.wait = WebDriverWait(self.browser, WAIT_SECONDS)
		self.browser.delete_all_cookies()
		api_base = json.dumps(self.live_server_url)
		self.browser.execute_cdp_cmd(
			"Page.addScriptToEvaluateOnNewDocument",
			{
				"source": f"""
					(() => {{
						if (window.__helpnetFetchPatched) return;
						window.__helpnetFetchPatched = true;
						const apiBase = {api_base};
						const originalFetch = window.fetch.bind(window);
						window.fetch = (resource, options) => {{
							const input = typeof resource === "string" ? resource : resource.url;
							return originalFetch(
								input.replace("http://127.0.0.1:8000", apiBase),
								options
							);
						}};
					}})();
				"""
			},
		)

	def make_user(self, name, verified=False):
		unique = uuid.uuid4().hex
		return User.objects.create_user(
			phone_number=f"017{int(unique[:8], 16) % 100000000:08d}",
			email=f"{unique}@example.test",
			full_name=name,
			password="test-password-123",
			is_verified=verified,
		)

	def make_donor(self, name, group="O+", area="Dhaka", available=True, verified=False):
		user = self.make_user(name, verified=verified)
		profile = DonorProfile.objects.create(
			user=user,
			blood_group=group,
			area=area,
			is_available=available,
		)
		return user, profile

	def make_request(self, requester, group="O+", area="Dhaka", hospital="Dhaka Medical College"):
		return BloodRequest.objects.create(
			requester=requester,
			blood_group=group,
			area=area,
			hospital=hospital,
			details="Urgent patient blood request",
		)

	def open_as(self, user, path):
		token = str(RefreshToken.for_user(user).access_token)
		stored_user = json.dumps({"user_id": str(user.user_id), "full_name": user.full_name})
		self.browser.get(self.live_server_url + "/")
		self.browser.execute_script(
			"localStorage.setItem('helpnet_token', arguments[0]);"
			"localStorage.setItem('helpnet_user', arguments[1]);",
			token,
			stored_user,
		)
		self.browser.get(self.live_server_url + path)

	def select_value(self, element_id, value):
		Select(self.browser.find_element(By.ID, element_id)).select_by_value(value)

	def select_text(self, element_id, text):
		Select(self.browser.find_element(By.ID, element_id)).select_by_visible_text(text)

	def click_visible(self, locator):
		element = self.wait.until(expected.element_to_be_clickable(locator))
		self.browser.execute_script(
			"arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});",
			element,
		)
		self.wait.until(
			lambda browser: browser.execute_script(
				"const rect = arguments[0].getBoundingClientRect();"
				"return rect.top >= 0 && rect.bottom <= window.innerHeight;",
				element,
			)
		)
		element.click()

	def api_call(self, method, path, body=None):
		return self.browser.execute_async_script(
			"""
			const [method, path, body, done] = arguments;
			fetch(path, {
				method,
				headers: {
					"Content-Type": "application/json",
					"Authorization": `Bearer ${localStorage.getItem("helpnet_token")}`
				},
				body: body === null ? undefined : JSON.stringify(body)
			}).then(async response => done({status: response.status, body: await response.json()}))
			  .catch(error => done({error: error.message}));
			""",
			method,
			path,
			body,
		)

	def test_st16_user_can_submit_a_rating_from_the_ratings_page(self):
		rater = self.make_user("Rating Author")
		rated_user = self.make_user("Rated Donor")
		self.open_as(rater, f"/ratings/?user_id={rated_user.user_id}")

		self.wait.until(expected.visibility_of_element_located((By.ID, "ratingsContent")))
		self.wait.until(
			lambda browser: "No ratings yet."
			in browser.find_element(By.ID, "existingRatings").text
		)
		self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, "#starPicker button[aria-label='5 stars']"))).click()
		self.browser.find_element(By.ID, "ratingComment").send_keys("Reliable donor")
		self.browser.find_element(By.CSS_SELECTOR, "#ratingForm button[type='submit']").click()
		self.wait.until(
			lambda browser: "Rating submitted successfully"
			in browser.find_element(By.ID, "ratingsMessage").text
		)

		rating = Rating.objects.get(rater=rater, rated_user=rated_user)
		self.assertEqual(rating.rating, 5)
		self.wait.until(
			lambda browser: "Reliable donor"
			in browser.find_element(By.ID, "existingRatings").text
		)

	def test_st16_invalid_and_self_ratings_are_rejected(self):
		rater = self.make_user("Rating Author")
		rated_user = self.make_user("Rated Donor")
		self.open_as(rater, f"/ratings/?user_id={rated_user.user_id}")

		for score in (0, 6):
			result = self.api_call(
				"POST",
				"/api/ratings/",
				{"rated_user": str(rated_user.user_id), "rating": score},
			)
			self.assertEqual(result["status"], 400)
		self_result = self.api_call(
			"POST",
			"/api/ratings/",
			{"rated_user": str(rater.user_id), "rating": 5},
		)
		self.assertEqual(self_result["status"], 400)
		self.assertFalse(Rating.objects.exists())

	def test_st17_donor_listing_shows_verification_and_average_rating(self):
		viewer = self.make_user("Donor Searcher")
		verified, _ = self.make_donor("Verified O Positive", verified=True)
		self.make_donor("Unverified O Positive", verified=False)
		rater = self.make_user("Donor Rater")
		Rating.objects.create(rater=rater, rated_user=verified, rating=5)
		Rating.objects.create(rater=viewer, rated_user=verified, rating=3)
		self.open_as(viewer, "/blood/")

		self.select_value("searchGroup", "O+")
		self.select_text("searchArea", "Dhaka")
		self.browser.find_element(By.ID, "donorSearchForm").submit()
		self.wait.until(
			lambda browser: (
				"★" in browser.find_element(By.ID, "donorSearchResults").text
				or "No available donors found" in browser.find_element(By.ID, "donorSearchResults").text
			)
		)

		cards = self.browser.find_elements(By.CSS_SELECTOR, ".donor-result")
		self.assertEqual(len(cards), 2)
		self.assertTrue(
			any("★ 4.0 · 2 ratings" in card.text for card in cards),
			[card.text for card in cards],
		)
		badges = self.browser.find_elements(By.CSS_SELECTOR, ".donor-result .donor-verified")
		self.assertEqual(
			len(badges),
			1,
			f"Expected one verified donor badge; rendered cards: {[card.text for card in cards]}",
		)

	def test_st18_donor_can_register_supported_blood_groups(self):
		donor = self.make_user("New Donor")
		self.open_as(donor, "/blood/")

		for group in ("A+", "B+", "O+", "AB+"):
			self.select_text("bloodGroup", group)
			self.select_text("donorArea", "Dhaka")
			available = self.browser.find_element(By.ID, "donorAvailable")
			if not available.is_selected():
				available.click()
			self.browser.find_element(By.ID, "donorProfileForm").submit()
			self.wait.until(
				lambda browser: "Donor profile saved"
				in browser.find_element(By.ID, "bloodMessage").text
			)
			self.wait.until(
				lambda _: DonorProfile.objects.get(user=donor).blood_group == group
			)
			profile = DonorProfile.objects.get(user=donor)
			self.assertEqual(profile.blood_group, group)
			self.assertEqual(profile.area, "Dhaka")

	def test_st19_donor_can_toggle_availability(self):
		donor, profile = self.make_donor("Availability Donor", available=True)
		self.open_as(donor, "/blood/")
		availability = self.wait.until(
			lambda browser: (
				element
				if (element := browser.find_element(By.ID, "donorAvailable")).is_selected()
				else False
			)
		)

		availability.click()
		self.browser.find_element(By.ID, "donorProfileForm").submit()
		self.wait.until(
			lambda browser: "Donor profile saved"
			in browser.find_element(By.ID, "bloodMessage").text
		)
		self.wait.until(lambda _: not DonorProfile.objects.get(user=donor).is_available)
		profile.refresh_from_db()
		self.assertFalse(profile.is_available)

		availability = self.browser.find_element(By.ID, "donorAvailable")
		availability.click()
		self.browser.find_element(By.ID, "donorProfileForm").submit()
		self.wait.until(
			lambda browser: "Donor profile saved"
			in browser.find_element(By.ID, "bloodMessage").text
		)
		self.wait.until(lambda _: DonorProfile.objects.get(user=donor).is_available)
		profile.refresh_from_db()
		self.assertTrue(profile.is_available)

	def test_st19_another_user_cannot_change_donor_availability(self):
		donor, profile = self.make_donor("Protected Donor", available=True)
		other_user = self.make_user("Different User")
		self.open_as(other_user, "/blood/")

		result = self.api_call(
			"PUT",
			"/api/blood/donor-profile/",
			{
				"user_id": str(donor.user_id),
				"blood_group": "O+",
				"area": "Dhaka",
				"is_available": False,
			},
		)
		profile.refresh_from_db()
		self.assertTrue(profile.is_available)
		self.assertEqual(result["status"], 200)
		self.assertEqual(result["body"]["data"]["user_id"], str(other_user.user_id))

	def test_st20_requester_can_create_an_open_blood_request(self):
		requester = self.make_user("Blood Requester")
		self.open_as(requester, "/blood/")
		self.select_value("requestGroup", "O+")
		self.select_text("requestArea", "Dhaka")
		self.browser.find_element(By.ID, "hospital").send_keys("Dhaka Medical College")
		self.browser.find_element(By.ID, "requestDetails").send_keys("Urgent patient request")
		self.browser.find_element(By.ID, "requestForm").submit()
		self.wait.until(
			lambda browser: "Blood request created"
			in browser.find_element(By.ID, "bloodMessage").text
		)

		blood_request = BloodRequest.objects.get(requester=requester)
		self.assertEqual(blood_request.status, BloodRequest.Status.OPEN)
		self.wait.until(
			lambda browser: "Dhaka Medical College"
			in browser.find_element(By.ID, "requestList").text
		)
		self.assertIn("Dhaka Medical College", self.browser.find_element(By.ID, "requestList").text)

	def test_st21_matching_excludes_wrong_group_area_and_unavailable_donors(self):
		requester = self.make_user("Matching Requester")
		match, _ = self.make_donor("Exact Match", "O+", "Dhaka", True)
		self.make_donor("Wrong Group", "A+", "Dhaka", True)
		self.make_donor("Wrong Area", "O+", "Khulna", True)
		self.make_donor("Unavailable", "O+", "Dhaka", False)
		blood_request = self.make_request(requester)
		self.open_as(requester, "/blood/")
		self.click_visible((By.XPATH, "//button[normalize-space()='Find matching donors']"))

		select = self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".donor-match-select")))
		options = Select(select).options
		option_users = [option.text for option in options]
		self.assertEqual(len(options), 2)
		self.assertIn("Exact Match · O+ · Dhaka", option_users)
		self.assertEqual(options[1].get_attribute("value"), str(match.user_id))
		self.assertEqual(blood_request.status, BloodRequest.Status.OPEN)

	def test_st22_matching_donor_sees_urgent_blood_alert(self):
		requester = self.make_user("Alert Requester")
		donor, _ = self.make_donor("Alert Donor", "O+", "Dhaka", True)
		self.open_as(requester, "/blood/")
		self.select_value("requestGroup", "O+")
		self.select_text("requestArea", "Dhaka")
		self.browser.find_element(By.ID, "hospital").send_keys("City Hospital")
		self.browser.find_element(By.ID, "requestDetails").send_keys("Urgent")
		self.browser.find_element(By.ID, "requestForm").submit()
		self.wait.until(
			lambda browser: "Blood request created"
			in browser.find_element(By.ID, "bloodMessage").text
		)

		self.assertTrue(Notification.objects.filter(user=donor, notification_type="blood_request").exists())
		self.open_as(donor, "/notifications/")
		alert = self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".notification-item")))
		self.assertIn("O+", alert.text)
		self.assertIn("Dhaka", alert.text)

	def test_st23_notification_can_be_read_and_is_private(self):
		owner = self.make_user("Notification Owner")
		other_user = self.make_user("Other Notification User")
		notification = Notification.objects.create(
			user=owner,
			message="Urgent O+ blood request in Dhaka.",
			notification_type="blood_request",
		)
		self.open_as(owner, "/notifications/")
		item = self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".notification-item.unread")))
		self.assertIn(notification.message, item.text)
		item.find_element(By.CSS_SELECTOR, ".notification-read-button").click()
		self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".notification-status")))
		notification.refresh_from_db()
		self.assertTrue(notification.is_read)

		self.open_as(other_user, "/notifications/")
		self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".notification-empty")))
		result = self.api_call("POST", f"/api/notifications/{notification.id}/read/")
		self.assertEqual(result["status"], 404)

	def test_st24_requester_can_fulfill_request_with_a_matching_donor(self):
		requester = self.make_user("Completion Requester")
		donor, donor_profile = self.make_donor("Completion Donor", "O+", "Dhaka", True)
		blood_request = self.make_request(requester)
		self.open_as(requester, "/blood/")
		self.click_visible((By.XPATH, "//button[normalize-space()='Find matching donors']"))
		select = self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".donor-match-select")))
		Select(select).select_by_value(str(donor.user_id))
		self.browser.find_element(By.XPATH, "//button[normalize-space()='Fulfill request']").click()
		self.wait.until(
			lambda browser: "Request fulfilled and donation history recorded"
			in browser.find_element(By.ID, "bloodMessage").text
		)

		blood_request.refresh_from_db()
		donor_profile.refresh_from_db()
		self.assertEqual(blood_request.status, BloodRequest.Status.FULFILLED)
		self.assertFalse(donor_profile.is_available)
		self.assertTrue(DonationHistory.objects.filter(donor=donor, blood_request=blood_request).exists())
		self.assertNotIn("Dhaka Medical College", self.browser.find_element(By.ID, "requestList").text)

	def test_st25_donor_history_shows_group_hospital_and_date(self):
		requester = self.make_user("History Requester")
		donor, _ = self.make_donor("History Donor", "AB+", "Dhaka", False)
		blood_request = self.make_request(requester, group="AB+", hospital="Central Hospital")
		history = DonationHistory.objects.create(donor=donor, blood_request=blood_request)
		self.open_as(donor, "/donation-history/")
		row = self.wait.until(expected.presence_of_element_located((By.CSS_SELECTOR, ".history-item")))

		self.assertIn("AB+ · Dhaka", row.text)
		self.assertIn("Central Hospital", row.text)
		self.assertIn(str(history.donated_at.year), row.text)

	def test_st27_blood_pages_have_no_leaderboard_or_advertising(self):
		user = self.make_user("No Ads User")
		paths = (
			"/blood/",
			"/blood-donor/",
			"/blood-request/",
			"/matching-donors/",
			"/donation-history/",
		)
		forbidden_text = re.compile(r"leaderboard|advertis(?:e|ement|ing)|sponsored|promotion", re.I)
		for path in paths:
			self.open_as(user, path)
			body_text = self.browser.find_element(By.TAG_NAME, "body").text
			self.assertIsNone(forbidden_text.search(body_text), f"Unexpected promotion text on {path}")
			promotional_elements = self.browser.find_elements(
				By.XPATH,
				"//*[contains(concat(' ', normalize-space(@class), ' '), ' leaderboard ') "
				"or contains(concat(' ', normalize-space(@class), ' '), ' advertisement ') "
				"or contains(concat(' ', normalize-space(@class), ' '), ' sponsored ')]",
			)
			self.assertEqual(promotional_elements, [], f"Promotional element found on {path}")
