import os
import subprocess as sp
import unittest

try:
    import ukt
except ImportError:
    ukt = None

try:
    from scrooge.contrib.kyototycoon import KyotoTycoonScrooge, KyotoTycoonStorage
except ImportError:
    if ukt is not None:
        raise

from scrooge.tests.base import BaseTestCase
from scrooge.tests.test_storage import StorageTests

has_ktserver = sp.call(["which", "ktserver"], stdout=sp.PIPE) == 0


@unittest.skipIf(ukt is None, "requires ukt")
@unittest.skipIf(not has_ktserver, "kyototycoon server not installed")
class TestKyotoTycoonScrooge(StorageTests, BaseTestCase):
    @classmethod
    def setUpClass(cls):
        lua_path = os.path.join(os.path.dirname(__file__), "scripts/")
        lua_script = os.path.join(lua_path, "kt.lua")
        cls._server = ukt.EmbeddedServer(
            database="%", serializer=ukt.KT_NONE, server_args=["-scr", lua_script]
        )
        cls._server.run()
        cls.db = cls._server.client

    @classmethod
    def tearDownClass(cls):
        if cls._server is not None:
            cls._server.stop()
            cls.db.close_all()
            cls.db = None

    def tearDown(self):
        if self.db is not None:
            self.db.clear()

    def get_scrooge(self):
        return KyotoTycoonScrooge(client=self.db, utc=False)

    def test_expire_results(self):
        scrooge = KyotoTycoonScrooge(client=self.db, utc=False, result_expire_time=3600)
        s = scrooge.storage

        s.put_data(b"k1", b"v1")
        s.put_data(b"k2", b"v2", is_result=True)
        self.assertEqual(s.pop_data(b"k1"), b"v1")
        self.assertEqual(s.pop_data(b"k2"), b"v2")

        self.assertTrue(s.has_data_for_key(b"k2"))
        self.assertFalse(s.put_if_empty(b"k2", b"v2-x"))
        self.assertFalse(s.has_data_for_key(b"k3"))
        self.assertTrue(s.put_if_empty(b"k3", b"v3"))

        self.assertTrue(s.delete_data(b"k2"))
        self.assertFalse(s.delete_data(b"k2"))
        self.assertEqual(s.result_items(), {"k1": b"v1", "k3": b"v3"})
        self.assertEqual(s.result_store_size(), 2)
