from rest_framework import serializers

from catalogo.models import Usuario


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class CrearInvitacionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nombre = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=150)
    rol = serializers.ChoiceField(choices=Usuario.Rol.choices)


class AceptarInvitacionSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirmar_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        if attrs['password'] != attrs['confirmar_password']:
            raise serializers.ValidationError(
                {'confirmar_password': 'Las contraseñas no coinciden.'}
            )
        return attrs
