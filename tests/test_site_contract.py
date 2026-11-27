from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class SiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = (DIST / "index.html").read_text(encoding="utf-8")
        cls.panel = (DIST / "panel/index.html").read_text(encoding="utf-8")
        cls.help = (DIST / "help/index.html").read_text(encoding="utf-8")
        cls.news = (DIST / "news/index.html").read_text(encoding="utf-8")

    def test_legacy_help_alias_redirects_to_migrated_help(self):
        alias = (DIST / "help.html").read_text(encoding="utf-8")
        self.assertIn("location.replace", alias)
        self.assertIn("location.hash", alias)
        self.assertIn("/help/", alias)

    def test_legacy_news_alias_redirects_to_migrated_news(self):
        alias = (DIST / "news.html").read_text(encoding="utf-8")
        self.assertIn("location.replace", alias)
        self.assertIn("/news/", alias)

    def test_help_migrates_operational_topics_and_anchors(self):
        for anchor in ("actualizaciones", "ssh", "docker", "https", "recuperacion"):
            self.assertRegex(self.help, rf'id=["\']{anchor}["\']')
        for term in ("instalador", "solo lectura", "SHA-256", "copias de seguridad"):
            self.assertIn(term.lower(), self.help.lower())

    def test_product_screenshots_are_real_assets_linked_from_panel_page(self):
        for name in ("panel-desktop.png", "panel-tablet.png"):
            image = ROOT / "assets/screenshots" / name
            self.assertTrue(image.is_file(), f"Falta captura: {image}")
            self.assertGreater(image.stat().st_size, 4096)
            self.assertIn(name, self.panel)

    def test_stable_download_is_manifest_driven_and_secure(self):
        self.assertRegex(self.panel, r"v\d+\.\d+\.\d+")
        self.assertIn("https://github.com/juanramonvf/miura-panel/releases/download/", self.panel)
        self.assertIn("SHA-256", self.panel)
        self.assertNotIn("203.0.113.", self.panel)

    def test_legacy_text_manual_is_migrated_and_uses_the_stable_feed_data(self):
        manual = (DIST / "README.txt").read_text(encoding="utf-8")
        self.assertTrue(manual.startswith("MIURA PANEL — AYUDA OFICIAL"))
        self.assertIn("https://miura.srtgateway.ovh/help/", manual)
        self.assertIn("https://github.com/juanramonvf/miura-panel/releases/download/", manual)
        self.assertNotIn("sep.mundopeke.es", manual)

    def test_only_existing_products_are_listed(self):
        self.assertIn("Miura Panel", self.home)
        self.assertNotRegex(self.home, r"Coming soon|Próximamente|Invented app")
        self.assertEqual(len(re.findall(r'class="card app-card"', self.home)), 1)

    def test_pages_workflow_pins_verified_actions_and_refreshes_feed(self):
        workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa", workflow)
        self.assertIn("actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e", workflow)
        self.assertIn("schedule:", workflow)


if __name__ == "__main__":
    unittest.main()
