from rest_framework import serializers
from . import models




class TransactionSerializer(serializers.ModelSerializer):
    class Meta():
        model = models.Transaction
        fields = "__all__"

    def validate(self, data):
        user = self.context['request'].user

        if not hasattr(user, 'wallet'):
            raise serializers.ValidationError("User has no wallet")

        wallet = user.wallet
        amount = data.get('amount')
        transaction_type = data.get('type')

        if transaction_type != 'income' and amount > wallet.total_balance:
            raise serializers.ValidationError("Not enough money")

        return data
        


class CategorySerializer(serializers.ModelSerializer):
    class Meta():
        model = models.Category
        fields = "__all__"


class BudgetSerializer(serializers.ModelSerializer):
    class Meta():
        model = models.Budget
        fields = "__all__"


    def validate(self, data):
        user = self.context['request'].user
        wallet = user.wallet

        category = data['category']

        if category.wallet != wallet:
            raise serializers.ValidationError("Invalid category for this wallet")

        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        wallet = user.wallet

        return models.Budget.objects.create(
            wallet=wallet,
            **validated_data
        )
