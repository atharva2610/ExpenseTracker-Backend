from rest_framework import serializers
from app_expenses.models import FundAccount

class FundAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundAccount
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)