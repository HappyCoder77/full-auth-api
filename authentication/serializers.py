from djoser.serializers import UserSerializer as BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + \
            ('is_superuser', 'is_regionalmanager',
             "is_localmanager", "is_sponsor", "is_dealer", "is_collector", "has_profile")
