# -*- coding: utf-8 -*-
# Code for Life
#
# Copyright (C) 2019, Ocado Limited
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ADDITIONAL TERMS – Section 7 GNU General Public Licence
#
# This licence does not grant any right, title or interest in any “Ocado” logos,
# trade names or the trademark “Ocado” or any other trademarks or domain names
# owned by Ocado Innovation Limited or the Ocado group of companies or any other
# distinctive brand features of “Ocado” as may be secured from time to time. You
# must not distribute any modification of this program using the trademark
# “Ocado” or claim any affiliation or association with Ocado or its employees.
#
# You are not authorised to use the name Ocado (or any of its trade names) or
# the names of any author or contributor in advertising or for publicity purposes
# pertaining to the distribution of this program, without the prior written
# authorisation of Ocado.
#
# Any propagation, distribution or conveyance of this program must include this
# copyright notice and these terms. You must not misrepresent the origins of this
# program; modified versions of the program must be marked as such and not
# identified as the original program.
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import TestCase

from datetime import datetime
from mock import patch

from portal.middleware.online_status import status


class TestOnlineStatus(TestCase):
    def setUp(self):
        self.user1 = User.objects.get_or_create(username="test1")[0]
        self.user2 = User.objects.get_or_create(username="test2")[0]

    def login_as(self, user):
        password = user.password
        if not password:
            password = "123"
            user.set_password(password)
            user.save()
        self.client.login(username=user.username, password=password)

    def list_len(self, length):
        users = cache.get(status.CACHE_USERS)
        self.assertEqual(len(users), length)

    def base_setup(self):
        cache.clear()
        self.client.get(reverse("dashboard"))
        useronline = cache.get(status.CACHE_PREFIX_USER % self.user1.pk)
        self.assertEqual(useronline, None)

        # Log user1 in, assert if online
        self.login_as(self.user1)
        self.client.get(reverse("dashboard"))
        useronline = cache.get(status.CACHE_PREFIX_USER % self.user1.pk)
        self.assertEqual(useronline.user, self.user1)
        self.assertEqual(useronline.status, 1)

        self.list_len(1)

        self.client.logout()

    def test_user_online(self):
        self.base_setup()

        # Log user2 in, assert if online
        self.login_as(self.user2)
        self.client.get(reverse("dashboard"))
        useronline = cache.get(status.CACHE_PREFIX_USER % self.user2.pk)
        self.assertEqual(useronline.user, self.user2)
        self.assertEqual(useronline.status, 1)

        self.list_len(2)

    @patch("portal.middleware.online_status.status.datetime")
    def test_user_idle(self, mocked_datetime):
        mocked_datetime.now.return_value = datetime(2019, 5, 1, 0, 0)
        self.base_setup()

        # Check idle
        mocked_datetime.now.return_value = datetime(2019, 5, 1, 0, 6)
        self.client.get(reverse("dashboard"))
        useronline = cache.get(status.CACHE_PREFIX_USER % self.user1.pk)
        self.assertEqual(useronline.user, self.user1)
        self.assertEqual(useronline.status, 0)

        self.list_len(1)

    @patch("portal.middleware.online_status.status.datetime")
    def test_user_offline(self, mocked_datetime):
        mocked_datetime.now.return_value = datetime(2019, 5, 1, 0, 0)
        self.base_setup()

        # Check offline
        mocked_datetime.now.return_value = datetime(2019, 5, 1, 0, 11)
        self.client.get(reverse("dashboard"))
        useronline = cache.get(status.CACHE_PREFIX_USER % self.user1.pk)
        self.assertEqual(useronline, None)

        self.list_len(0)
