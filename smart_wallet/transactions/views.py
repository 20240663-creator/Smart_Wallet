from django.shortcuts import render
from rest_framework import  generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from . import models
from . import serializer
from . import permessions
# Create your views here.




class TransactionsViewSets(ModelViewSet):
    serializer_class = serializer.TransactionSerializer
    permission_classes = [IsAuthenticated,permessions.IsOwnerOfWallet]

    def perform_create(self, serializer):
        wallet = getattr(self.request.user, "wallet", None)
        if not wallet:
            raise ValidationError("User has no wallet")
        
        amount = serializer.validated_data['amount']
        type = serializer.validated_data['type']
        budget = serializer.validated_data.get('budget')
        goal = serializer.validated_data.get('saving_goals')

        if type == 'income':
            wallet.total_balance += amount
            wallet.total_income += amount
            wallet.save()
        elif type == 'expense':
            if amount > wallet.total_balance:
                raise ValidationError("Not enough balance")
            
            if budget:
                if budget.spended + amount > budget.amount:
                    raise ValidationError("Exceed the limit of budget")
                budget.spended += amount
                budget.percentage = (budget.spended / budget.amount) * 100
                budget.save()

            if goal:
                if goal.current_amount + amount > goal.target_amount:
                    raise ValidationError("Exceed the limit of goal")
                if goal.current_amount + amount == goal.target_amount:
                    goal.status = 'complete'
                goal.current_amount += amount 
                goal.save()
            wallet.total_balance -= amount
            wallet.total_expense += amount
            wallet.save()

        serializer.save(wallet=wallet)


    def get_queryset(self):
        queryset = models.Transaction.objects.all()
        type = self.request.query_params.get('type')
        wallet = self.request

        if type is not None:
            queryset = queryset.filter(type=type)

        if self.request.user.is_staff:
            return queryset
        
        return queryset.filter(wallet__user=self.request.user)
    

class CategoryViewSets(ModelViewSet):
    serializer_class = serializer.CategorySerializer
    permission_classes = [IsAuthenticated,permessions.IsMyCategory]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Category.objects.all()
        return models.Category.objects.filter(
            wallet__user=self.request.user
        )
    
    def perform_create(self, serializer):
        wallet = self.request.user.wallet
        serializer.save(wallet=wallet)

    

class BudgetViewSets(ModelViewSet):
    serializer_class = serializer.BudgetSerializer
    permission_classes = [IsAuthenticated,permessions.IsMyBudget]

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.Budget.objects.all()
        return models.Budget.objects.filter(
            wallet__user=self.request.user
        )

    

    
class SavingGoalsViewSets(ModelViewSet):
    serializer_class = serializer.SavingGoalsSerializer
    permission_classes = [IsAuthenticated,permessions.IsMySaving]
    query = models.SavingGoals.objects.all()

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.query
        return self.query.filter(wallet=self.request.user.wallet)
    

