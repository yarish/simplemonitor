"""
SimpleMonitor alerting via BulkSMS
"""

from typing import cast

import requests

from ..Monitors.monitor import Monitor
from .alerter import Alerter, AlertLength, AlertType, register


@register
class BulkSMSAlerter(Alerter):
    """
    Send SMS alerts using the BulkSMS service

    Subscription required, see http://www.bulksms.co.uk"""

    alerter_type = "bulksms"
    urgent = True

    def __init__(self, config_options: dict) -> None:
        super().__init__(config_options)
        self.username = cast(
            str, self.get_config_option("username", required=True, allow_empty=False)
        )
        self.password = cast(
            str, self.get_config_option("password", required=True, allow_empty=False)
        )
        self.target = cast(
            str, self.get_config_option("target", required=True, allow_empty=False)
        )

        self.sender = cast(str, self.get_config_option("sender", default="SmplMntr"))
        if len(self.sender) > 11:
            self.alerter_logger.warning("truncating SMS sender name to 11 chars")
            self.sender = self.sender[:11]

        self.api_host = self.get_config_option("api_host", default="www.bulksms.co.uk")

        self.support_catchup = True

    def send_alert(self, name: str, monitor: Monitor) -> None:
        """Send an SMS alert."""

        alert_type = self.should_alert(monitor)
        if alert_type not in [AlertType.FAILURE, AlertType.SUCCESS]:
            return

        message = self.build_message(AlertLength.SMS, alert_type, monitor)

        url = "https://{}/eapi/submission/send_sms/2/2.0".format(self.api_host)
        params = {
            "username": self.username,
            "password": self.password,
            "message": message,
            "msisdn": self.target,
            "sender": self.sender,
            "repliable": "0",
        }

        if not self._dry_run:
            try:
                response = requests.get(url, params=params)
                status = response.text
                if not status.startswith("0"):
                    self.alerter_logger.error(
                        "Unable to send SMS: %s (%s)",
                        status.split("|")[0],
                        status.split("|")[1],
                    )
            except requests.exceptions.RequestException:
                self.alerter_logger.exception("SMS sending failed")
        else:
            self.alerter_logger.info(
                "dry_run: would send SMS: %s with message %s", url, message
            )

    def _describe_action(self) -> str:
        return "SMSing {target} via BulkSMS".format(target=self.target)
