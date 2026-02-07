from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.schemas import TelegramEnv
from src.telegram_bot import TelegramBot


class TestTelegramBot:
    def setup_method(self):
        with patch("src.telegram_bot.telegram.Bot"):
            self.bot = TelegramBot(TelegramEnv(bot_token="tok", chat_id="123"))
            self.bot.bot = MagicMock()

    def test_send_message_formats_html(self):
        self.bot.send_message("hello <world>")
        self.bot.bot.send_message.assert_called_once_with(
            chat_id="123",
            text="<code>hello &lt;world&gt;</code>",
            parse_mode="HTML",
            disable_notification=False,
        )

    def test_send_message_silent(self):
        self.bot.send_message("test", silent=True)
        call_kwargs = self.bot.bot.send_message.call_args[1]
        assert call_kwargs["disable_notification"] is True

    def test_send_message_error_does_not_raise(self):
        self.bot.bot.send_message.side_effect = Exception("network error")
        self.bot.send_message("test")  # should not raise
