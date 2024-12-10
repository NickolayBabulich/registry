from django.contrib.auth.models import User
from rest_framework import serializers

from apps.registry.models import Document, DocumentField, RegistrySchema


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


class RegistrySchemaSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = RegistrySchema
        fields = ['id', 'name', 'description', 'fields_schema', 'created_at', 'owner']
        read_only_fields = ['created_at', 'owner']

    def validate_fields_schema(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('fields_schema должна быть списком')

        required_keys = {'name', 'type'}
        allowed_types = {'text', 'number', 'date', 'boolean'}

        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("Каждое поле должно быть объектом")

            if missing := required_keys - field.keys():
                raise serializers.ValidationError(f"Отсутствуют обязательные ключи: {missing}")

            if field['type'] not in allowed_types:
                raise serializers.ValidationError(f"Недопустимый тип поля: {field['type']}")

        return value


class DocumentFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentField
        fields = ['id', 'data']


class DocumentSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    registry_schema = RegistrySchemaSerializer(read_only=True)
    registry_schema_id = serializers.PrimaryKeyRelatedField(
        queryset=RegistrySchema.objects.all(),
        write_only=True,
        source='registry_schema'
    )
    document_fields = DocumentFieldSerializer(many=True, required=False)

    class Meta:
        model = Document
        fields = ['id', 'name', 'registry_schema', 'registry_schema_id',
                  'created_by', 'created_at', 'updated_at', 'document_fields']
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def validate_registry_schema_id(self, value):
        if not value.owner == self.context['request'].user:
            raise serializers.ValidationError(
                "Вы можете создавать документы только на основе своих схем реестра"
            )
        return value

    def create(self, validated_data):
        fields_data = validated_data.pop('document_fields', [])
        document = Document.objects.create(**validated_data)

        for field_data in fields_data:
            DocumentField.objects.create(document=document, **field_data)

        return document

    def update(self, instance, validated_data):
        # Обновляем основные поля документа
        instance.name = validated_data.get('name', instance.name)
        instance.registry_schema = validated_data.get('registry_schema', instance.registry_schema)
        instance.save()

        # Если есть новые данные полей
        if 'document_fields' in validated_data:
            # Создаем новые поля, не удаляя старые
            for field_data in validated_data.get('document_fields', []):
                DocumentField.objects.create(
                    document=instance,
                    **field_data
                )

        return instance

