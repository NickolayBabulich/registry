from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.registry.api.serializers import DocumentFieldSerializer, DocumentSerializer, RegistrySchemaSerializer
from apps.registry.models import Document, DocumentField, RegistrySchema


@extend_schema_view(
    list=extend_schema(
        summary="Получить список схем реестра",
        description="Возвращает список схем реестра, принадлежащих текущему пользователю",
        responses={200: RegistrySchemaSerializer(many=True)},
        tags=['registry-schemas']
    ),
    create=extend_schema(
        summary="Создать схему реестра",
        description="Создает новую схему реестра для текущего пользователя",
        request=RegistrySchemaSerializer,
        responses={
            201: RegistrySchemaSerializer,
            400: OpenApiResponse(description="Ошибка валидации")
        },
        tags=['registry-schemas'],
        examples=[
            OpenApiExample(
                "Пример схемы реестра",
                value={
                    "name": "Документы проекта",
                    "description": "Схема для хранения проектной документации",
                    "fields_schema": [
                        {"name": "title", "type": "text"},
                        {"name": "date", "type": "date"},
                        {"name": "amount", "type": "number"}
                    ]
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="Получить схему реестра",
        description="Получить детальную информацию о схеме реестра",
        responses={200: RegistrySchemaSerializer},
        tags=['registry-schemas']
    ),
    update=extend_schema(
        summary="Обновить схему реестра",
        description="Полное обновление схемы реестра",
        request=RegistrySchemaSerializer,
        responses={200: RegistrySchemaSerializer},
        tags=['registry-schemas']
    ),
    partial_update=extend_schema(
        summary="Частично обновить схему реестра",
        description="Частичное обновление схемы реестра",
        request=RegistrySchemaSerializer,
        responses={200: RegistrySchemaSerializer},
        tags=['registry-schemas']
    ),
    destroy=extend_schema(
        summary="Удалить схему реестра",
        description="Удаление схемы реестра",
        responses={204: None},
        tags=['registry-schemas']
    )
)
class RegistrySchemaViewSet(viewsets.ModelViewSet):
    serializer_class = RegistrySchemaSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return RegistrySchema.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Получить список документов",
        description="Возвращает список документов, доступных текущему пользователю",
        responses={200: DocumentSerializer(many=True)},
        tags=['documents']
    ),
    create=extend_schema(
        summary="Создать документ",
        description="Создает новый документ на основе существующей схемы реестра",
        request=DocumentSerializer,
        responses={
            201: DocumentSerializer,
            400: OpenApiResponse(description="Ошибка валидации")
        },
        tags=['documents']
    ),
    retrieve=extend_schema(
        summary="Получить документ",
        description="Получить детальную информацию о документе",
        responses={200: DocumentSerializer},
        tags=['documents']
    ),
    update=extend_schema(
        summary="Обновить документ",
        description="Полное обновление документа",
        request=DocumentSerializer,
        responses={200: DocumentSerializer},
        tags=['documents']
    ),
    partial_update=extend_schema(
        summary="Частично обновить документ",
        description="Частичное обновление документа",
        request=DocumentSerializer,
        responses={200: DocumentSerializer},
        tags=['documents']
    ),
    destroy=extend_schema(
        summary="Удалить документ",
        description="Удаление документа",
        responses={204: None},
        tags=['documents']
    )
)
class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Document.objects.filter(
            Q(created_by=self.request.user) |
            Q(shared_access__user=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @extend_schema(
        summary="Управление полем документа",
        description="Обновление или удаление конкретного поля документа",
        parameters=[
            OpenApiParameter(
                name="field_id",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="ID поля документа"
            )
        ],
        methods=['PUT', 'DELETE'],
        request=DocumentFieldSerializer,
        responses={
            200: DocumentFieldSerializer,
            204: None,
            404: OpenApiResponse(description="Поле не найдено"),
            400: OpenApiResponse(description="Ошибка валидации")
        },
        tags=['documents']
    )
    @action(detail=True, methods=['put', 'delete'], url_path='fields/(?P<field_id>[^/.]+)')
    def manage_field(self, request, pk=None, field_id=None):
        document = self.get_object()

        try:
            field = document.document_fields.get(id=field_id)
        except DocumentField.DoesNotExist:
            return Response(
                {"error": "Поле не найдено"},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'DELETE':
            field.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        elif request.method == 'PUT':
            serializer = DocumentFieldSerializer(field, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Список полей документа",
        description="Получить список всех полей конкретного документа",
        responses={200: DocumentFieldSerializer(many=True)},
        tags=['documents']
    )
    @action(detail=True, methods=['get'], url_path='fields')
    def list_fields(self, request, pk=None):
        document = self.get_object()
        fields = document.document_fields.all()
        serializer = DocumentFieldSerializer(fields, many=True)
        return Response(serializer.data)
