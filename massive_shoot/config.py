import os


class ProjectConfig:
    def __init__(self) -> None:
        self.service_name = os.environ.get("SERVICE_NAME", "massive-shoot")

        self.line_channel_access_token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
        self.line_channel_secret = os.environ["LINE_CHANNEL_SECRET"]
        self.line_login_channel_id = os.environ["LINE_LOGIN_CHANNEL_ID"]
        self.hosting_image_domain = os.environ["HOSTING_IMAGE_DOMAIN"]
        self.hosting_image_acm_arn = os.environ["HOSTING_IMAGE_ACM_ARN"]
        self.sentry_dsn = os.environ.get("SENTRY_DSN", "")
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")

        self.save_image_prefix = ".images"
        self.hosting_image_prefix = "images"
