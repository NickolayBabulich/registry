from rest_framework.routers import DefaultRouter

from apps.registry.api.routes import DocumentViewSet, RegistrySchemaViewSet

router = DefaultRouter()
router.register(r'registry-schemas', RegistrySchemaViewSet, basename='api-registry-schema')
router.register(r'documents', DocumentViewSet, basename='api-document')
