#!/usr/bin/env python3
"""Unit tests for validate_handoff.py. Standard library only.

Run from anywhere:
    python3 context-handoff/scripts/test_validate_handoff.py
"""

import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_handoff as vh  # noqa: E402

SECTIONS = "\n\n".join(f"## {name}\n\nNone." for name in vh.REQUIRED_SECTIONS)


def secret_checks(text):
    return [f for f in vh.check_secrets(text) if f.level == "ERROR"]


class Sections(unittest.TestCase):
    def test_complete_handoff_has_no_section_errors(self):
        self.assertEqual(vh.check_sections(SECTIONS), [])

    def test_missing_section_is_an_error(self):
        text = SECTIONS.replace("## Dead ends", "## Things we tried")
        self.assertEqual([f.message for f in vh.check_sections(text)],
                         ["missing required section '## Dead ends'"])

    def test_resume_here_must_come_first(self):
        text = "## Goal\n\nx\n\n" + SECTIONS.replace("## Goal\n\nNone.", "")
        self.assertEqual(len(vh.check_section_order(text)), 1)


class Secrets(unittest.TestCase):
    def test_github_token(self):
        self.assertTrue(secret_checks("used ghp_" + "a" * 36))

    def test_password_assignment(self):
        self.assertTrue(secret_checks("password=hunter2-staging"))

    def test_password_in_prose(self):
        found = secret_checks("Staging DB password is hunter2-staging-9981 (in 1Password).")
        self.assertEqual([f.message.split(":")[0] for f in found], ["possible credential in prose"])

    def test_prose_without_a_secret_is_not_flagged(self):
        for line in ("The password is required for staging.",
                     "The token is stored in repo secrets as DEPLOY_TOKEN.",
                     "The secret was rotated yesterday."):
            with self.subTest(line=line):
                self.assertEqual(secret_checks(line), [])

    def test_redacted_value_passes(self):
        self.assertEqual(secret_checks("password is <REDACTED:db-password> (1Password vault)"), [])
        self.assertEqual(secret_checks("password=<REDACTED:db-password>"), [])

    def test_hex_next_to_key_wording_is_an_error(self):
        self.assertTrue(secret_checks("wallet private key " + "ab" * 32))

    def test_bare_hex_is_only_a_warning(self):
        findings = vh.check_secrets("tx " + "ab" * 32)
        self.assertEqual([f.level for f in findings], ["WARN"])

    def test_secret_is_masked_in_output(self):
        token = "ghp_" + "Z" * 36
        self.assertNotIn(token, " ".join(f.message for f in vh.check_secrets(token)))


class Placeholders(unittest.TestCase):
    def test_raw_template_block_fails(self):
        template = (HERE.parent / "references" / "template.md").read_text(encoding="utf-8")
        block = re.search(r"```markdown\n(.*?)\n```", template, re.S).group(1)
        self.assertEqual(len(vh.check_placeholders(block)), 12)

    def test_placeholders_inside_code_fences_are_ignored(self):
        self.assertEqual(vh.check_placeholders("```\nTODO: fill in\n```"), [])


class Links(unittest.TestCase):
    def test_claude_chat_link_warns(self):
        self.assertEqual(len(vh.check_links("see https://claude.ai/chat/abc-123")), 1)


if __name__ == "__main__":
    unittest.main()
