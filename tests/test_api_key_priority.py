"""API key resolution priority tests (scenarios A–E).

Run:  python tests/test_api_key_priority.py

Scenarios:
  A. No user key + default credential env present -> AI works (env key)
  B. User sets own key                          -> user key wins
  C. User deletes own key                       -> falls back to env default
  D. Neither present                            -> NO key (AI not configured)
  E. No key content leaked via status / errors
"""
import os
import sys
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent / "server"
sys.path.insert(0, str(SERVER))

import config_manager as cm

FAKE_USER_KEY = "sk-user-abc1234567890"
FAKE_DEFAULT_KEY = "sk-default-xyz9876543210"


class FakeKeyring:
    def __init__(self):
        self.store = {}

    def get_password(self, service, username):
        return self.store.get((service, username))

    def set_password(self, service, username, password):
        self.store[(service, username)] = password

    def delete_password(self, service, username):
        self.store.pop((service, username), None)


def setup(user_key, default_key):
    """Install a fake keyring and set/clear the default-credential env var."""
    fake = FakeKeyring()
    if user_key:
        fake.store[(cm._KEYRING_SERVICE, cm._KEYRING_USERNAME)] = user_key
    cm.keyring.get_password = fake.get_password
    cm.keyring.set_password = fake.set_password
    cm.keyring.delete_password = fake.delete_password
    if default_key:
        os.environ[cm._DEFAULT_KEY_ENV] = default_key
    else:
        os.environ.pop(cm._DEFAULT_KEY_ENV, None)
    return fake


def assert_eq(actual, expected, label):
    ok = actual == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {actual!r}")
    return ok


def main():
    results = []

    print("=== A. 无用户Key + 存在默认凭据(env) -> AI 正常 ===")
    setup(None, FAKE_DEFAULT_KEY)
    results.append(assert_eq(cm.get_deepseek_api_key(), FAKE_DEFAULT_KEY, "key == default"))
    results.append(assert_eq(cm.is_ai_configured(), True, "is_ai_configured"))
    st = cm.get_config_status()
    results.append(assert_eq(st["available"], True, "status.available"))
    results.append(assert_eq(st["configured"], False, "status.configured (no user key)"))
    results.append(assert_eq(st["using_default"], True, "status.using_default"))

    print("=== B. 用户配置自己的Key -> 优先使用用户Key ===")
    setup(FAKE_USER_KEY, FAKE_DEFAULT_KEY)
    results.append(assert_eq(cm.get_deepseek_api_key(), FAKE_USER_KEY, "key == user (wins over default)"))
    st = cm.get_config_status()
    results.append(assert_eq(st["configured"], True, "status.configured"))
    results.append(assert_eq(st["using_default"], False, "status.using_default"))

    print("=== C. 用户删除自己的Key -> 回退默认凭据(env) ===")
    setup(FAKE_USER_KEY, FAKE_DEFAULT_KEY)
    cm.set_deepseek_api_key("")  # clears user key from keyring
    results.append(assert_eq(cm.get_deepseek_api_key(), FAKE_DEFAULT_KEY, "key == default after delete"))
    st = cm.get_config_status()
    results.append(assert_eq(st["configured"], False, "status.configured=False"))
    results.append(assert_eq(st["using_default"], True, "status.using_default=True"))

    print("=== D. 无用户Key且无环境变量 -> AI 未配置 (无内置Key) ===")
    setup(None, None)
    results.append(assert_eq(cm.get_deepseek_api_key(), "", "key == empty"))
    results.append(assert_eq(cm.is_ai_configured(), False, "is_ai_configured=False"))
    st = cm.get_config_status()
    results.append(assert_eq(st["available"], False, "status.available=False"))
    results.append(assert_eq(st["using_default"], False, "status.using_default=False"))

    print("=== E. 状态/错误不泄露Key ===")
    setup(FAKE_USER_KEY, FAKE_DEFAULT_KEY)
    st = cm.get_config_status()
    dumped = json.dumps(st, ensure_ascii=False)
    results.append(assert_eq(FAKE_USER_KEY in dumped, False, "user key not in status JSON"))
    results.append(assert_eq(FAKE_DEFAULT_KEY in dumped, False, "default key not in status JSON"))
    # placeholder env values must never be treated as a credential
    os.environ[cm._DEFAULT_KEY_ENV] = "sk-your-deepseek-key-here"
    results.append(assert_eq(cm.get_default_api_key(), "", "placeholder env -> empty"))
    os.environ.pop(cm._DEFAULT_KEY_ENV, None)

    print()
    total = len(results)
    failed = results.count(False)
    print(f"RESULT: {total - failed}/{total} passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
