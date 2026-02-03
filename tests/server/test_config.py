import asyncio
import unittest
from unittest.mock import Mock

from narrativegraphs.server.app import app, get_config


class TestConfigEndpoint(unittest.TestCase):
    def test_config_cooccurrence_only_true(self):
        """Test config endpoint returns cooccurrence_only=True when set."""
        app.state.cooccurrence_only = True

        request = Mock()
        request.app = app

        result = asyncio.run(get_config(request))

        self.assertEqual(result["cooccurrence_only"], True)
        self.assertEqual(result["default_connection_type"], "cooccurrence")

    def test_config_cooccurrence_only_false(self):
        """Test config endpoint returns cooccurrence_only=False when set."""
        app.state.cooccurrence_only = False

        request = Mock()
        request.app = app

        result = asyncio.run(get_config(request))

        self.assertEqual(result["cooccurrence_only"], False)
        self.assertEqual(result["default_connection_type"], "relation")

    def test_config_cooccurrence_only_default(self):
        """Test config endpoint returns False when cooccurrence_only not set."""
        # Remove the attribute if it exists
        if hasattr(app.state, "cooccurrence_only"):
            delattr(app.state, "cooccurrence_only")

        request = Mock()
        request.app = app

        result = asyncio.run(get_config(request))

        self.assertEqual(result["cooccurrence_only"], False)
        self.assertEqual(result["default_connection_type"], "relation")


class TestBackgroundServerCooccurrenceOnly(unittest.TestCase):
    def test_background_server_accepts_cooccurrence_only(self):
        """Test BackgroundServer accepts cooccurrence_only parameter."""
        from narrativegraphs.server.backgroundserver import BackgroundServer

        engine = Mock()

        # Should not raise
        server = BackgroundServer(engine, port=8001, cooccurrence_only=True)
        self.assertTrue(server._cooccurrence_only)

        server = BackgroundServer(engine, port=8001, cooccurrence_only=False)
        self.assertFalse(server._cooccurrence_only)

    def test_background_server_default_cooccurrence_only(self):
        """Test BackgroundServer defaults cooccurrence_only to False."""
        from narrativegraphs.server.backgroundserver import BackgroundServer

        engine = Mock()
        server = BackgroundServer(engine, port=8001)
        self.assertFalse(server._cooccurrence_only)


if __name__ == "__main__":
    unittest.main()
