from .utils import MailmanAPITestCase
from Mailman import MailList, UserDesc, Defaults
from time import strftime

class TestAPI(MailmanAPITestCase):
    url = '/'
    data = {'address': 'user@email.com'}
    list_name = 'list'

    def setUp(self):
        super(TestAPI, self).setUp()
        self.create_list(self.list_name)

    def tearDown(self):
        super(TestAPI, self).tearDown()
        self.remove_list(self.list_name)

    def test_subscribe_no_moderation(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 0)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, resp.json)

    def test_subscribe_confirm(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 1)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, resp.json)

    def test_subscribe_approval(self):
        path = '/members'

        self.change_list_attribute('subscribe_policy', 2)
        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(2, resp.json)

    def test_subscribe_banned(self):
        path = '/members'
        mlist = MailList.MailList(self.list_name)
        mlist.ban_list.append(self.data['address'])
        mlist.Save()
        mlist.Unlock()

        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(4, resp.json)

    def test_subscribe_already_member(self):
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)
        mlist = MailList.MailList(self.list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.put(self.url + self.list_name + path,
                               self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(3, resp.json)

    def test_subscribe_bad_email(self):
        path = '/members'
        data = {'address': 'user@emailcom'}
        resp = self.client.put(self.url + self.list_name + path,
                               data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(5, resp.json)

    def test_unsubscribe(self):
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)
        mlist = MailList.MailList(self.list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.delete(self.url + self.list_name + path,
                                  self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, resp.json)

    def test_unsubscribe_not_member(self):
        path = '/members'
        resp = self.client.delete(self.url + self.list_name + path,
                                  self.data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(7, resp.json)

    def test_sendmail(self):
        mlist = MailList.MailList(self.list_name)
        data = {}
        data['email_to'] = mlist.GetListEmail()
        data['message_id'] = 1
        data['ip_from'] = '127.0.0.1'
        data['timestamp'] = strftime('%a, %d %b %Y %H:%M:%S %z (%Z)')
        data['name_from'] = 'user test'
        data['email_from'] = self.data['address']
        data['subject'] = 'subject test'
        data['body'] = 'body test'

        resp = self.client.post(self.url + self.list_name,
                                data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, resp.json)

    def test_sendmail_with_reply(self):
        mlist = MailList.MailList(self.list_name)
        data = {}
        data['email_to'] = mlist.GetListEmail()
        data['message_id'] = 1
        data['ip_from'] = '127.0.0.1'
        data['timestamp'] = strftime('%a, %d %b %Y %H:%M:%S %z (%Z)')
        data['name_from'] = 'user test'
        data['email_from'] = self.data['address']
        data['subject'] = 'subject test'
        data['body'] = 'body test'
        data['in_reply_to'] = 1

        resp = self.client.post(self.url + self.list_name,
                                data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, resp.json)

    def test_sendmail_missing_information(self):
        data = {}
        resp = self.client.post(self.url + self.list_name,
                                data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(8, resp.json)

    def test_sendmail_unknown_list(self):
        path = ''
        data = {}

        resp = self.client.post(self.url + path + 'unknown_list',
                                data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(12, resp.json)

    def test_mailman_site_list_not_listed_among_lists(self):
        mailman_site_list = Defaults.MAILMAN_SITE_LIST

        self.create_list(mailman_site_list)

        resp = self.client.get(self.url, expect_errors=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            self.assertNotEqual(mlist.get("listname"), mailman_site_list)

    def test_list_lists(self):
        resp = self.client.get(self.url, expect_errors=True)
        total_lists = len(resp.json)
        found = False

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertGreaterEqual(total_lists, 1)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            if mlist.get("listname") == self.list_name:
                found = True

        self.assertTrue(found)

    def test_create_list(self):
        new_list = 'new_list'
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456'}

        resp = self.client.put(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(0, resp.json)
        self.remove_list(new_list)

    def test_create_list_already_exists(self):
        new_list = self.list_name
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456'}

        resp = self.client.put(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(13, resp.json)

    def test_create_private_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 1}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_public_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 0}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_archive_private_out_of_max_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': 2}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_archive_private_out_of_min_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'archive_private': -1}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.archive_private), 0)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_confirm_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 1}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_approval_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 2}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 2)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_confirm_and_approval_list(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 3}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 3)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_subscribe_policy_out_of_max_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 4}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_subscribe_policy_out_of_min_range(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 0}
        resp = self.client.put(url, data, expect_errors=True)
        mlist = MailList.MailList(new_list)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(int(mlist.subscribe_policy), 1)
        mlist.Unlock()
        self.remove_list(new_list)

    def test_create_list_invalid_params(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': '123456',
                'subscribe_policy': 'Invalid', 'archive_private': 'Invalid'}
        resp = self.client.put(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, 14)
        self.remove_list(new_list)

    def test_create_list_invalid_password(self):
        new_list = "new_list"
        url = self.url + new_list

        data = {'admin': self.data['address'], 'password': ''}
        resp = self.client.put(url, data, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json, 11)
        self.remove_list(new_list)

    def test_members(self):
        list_name = 'list13'
        path = '/members'
        user_desc = UserDesc.UserDesc(self.data['address'], 'fullname', 1)

        self.create_list(list_name)

        mlist = MailList.MailList(list_name)
        mlist.AddMember(user_desc)
        mlist.Save()
        mlist.Unlock()

        resp = self.client.get(self.url + list_name + path, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([self.data['address']], resp.json)

    def test_member_singular(self):
        #TODO
        pass

    def test_members_unknown_list(self):
        list_name = 'list14'
        path = '/members'

        resp = self.client.get(self.url + list_name + path, expect_errors=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(12, resp.json)

    def test_delete_list(self):
        #TODO place holder for future addition of list deletion
        pass

    def test_list_attr(self):
        resp = self.client.get(self.url + self.list_name, expect_errors=True)
        total_lists = len(resp.json)
        found = False

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertEqual(total_lists, 1)

        for mlist in resp.json:
            self.assertIsInstance(mlist, dict)
            if mlist.get("listname") == self.list_name:
                found = True
        self.assertTrue(found)
