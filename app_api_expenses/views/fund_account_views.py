from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from ..serializers import FundAccountSerializer, FundAccount

class ListFundAccounts(ListAPIView):
    serializer_class = FundAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FundAccount.get_for_user(self.request.user)

class RetrieveFundAccount(RetrieveAPIView):
    serializer_class = FundAccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FundAccount.get_for_user(self.request.user)
   
class CreateFundAccount(CreateAPIView):
    serializer_class = FundAccountSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()
    
    # def post(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response({'message': 'Fund Account added successfully!!!', 'payload': serializer.data}, status=status.HTTP_201_CREATED)
    #     return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)