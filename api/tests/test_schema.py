from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class SchemaSecurityTests(SimpleTestCase):
    # Every security requirement names a declared scheme and lists string scopes
    def test_security_requirements_reference_declared_schemes(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        schemes = schema['components']['securitySchemes']
        self.assertIn('tokenAuth', schemes)
        checked = 0
        for path, operations in schema['paths'].items():
            for method, operation in operations.items():
                for requirement in operation.get('security', []):
                    for name, scopes in requirement.items():
                        with self.subTest(path=path, method=method, scheme=name):
                            self.assertIn(name, schemes)
                            self.assertIsInstance(scopes, list)
                            self.assertTrue(all(isinstance(s, str) for s in scopes))
                        checked += 1
        self.assertGreater(checked, 0)
