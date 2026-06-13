class KimiError(Exception):
    pass


class KimiAuthError(KimiError):
    pass


class KimiAPIError(KimiError):
    def __init__(self, code, detail=""):
        self.code = code
        self.detail = detail
        msg = f"Kimi API error: {code}"
        if detail:
            msg += f" — {detail}"
        super().__init__(msg)


class KimiUploadError(KimiError):
    pass


class KimiSessionLimitError(KimiError):
    pass
