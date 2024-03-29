from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .serializers import MedicalConsultSerializer
from apps.medical_consult.models import MedicalConsult
from apps.doctor.api.serializers import DoctorSerializer
from apps.doctor.models import Doctor
from datetime import datetime


class MedicalConsultViewSet(ModelViewSet):
    queryset = MedicalConsult.objects.all()
    serializer_class = MedicalConsultSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete']

    def create(self, request, *args, **kwargs):
        try:
            doctor = Doctor.objects.get(id=self.request.data['doctor'])
            date = datetime.strptime(self.request.data['day'], '%Y-%m-%d').date()
            time = datetime.strptime(self.request.data['time'], '%H:%M').time()

            assert date == datetime.now().date() \
                   and time >= datetime.now().time() \
                   or date >= datetime.now().date()

            has_consult = MedicalConsult.objects.filter(day=date, time=time)

            if len(has_consult) > 0:
                return Response(
                    {'message', 'Uma consulta ja existe nesse horário e data'},
                    status=403
                )

            query = MedicalConsult.objects.create(
                day=self.request.data['day'],
                time=self.request.data['time'],
                doctor=doctor,
                user=self.request.user,
            )
            query.save()
            doctor = DoctorSerializer(doctor)
            response = {
                'id': query.id,
                'dia': query.day,
                'horario': query.time,
                'data_agendamento': query.scheduling_date,
                'doctor': doctor.data
            }
            return Response(response)
        except IntegrityError:
            return Response(
                {
                    'code': 403,
                    'message': 'Você já criou uma consulta como essa data e horário'
                }
            )
        except AssertionError:
            return Response(
                {
                    'code': 403,
                    'message': 'Você não pode criar uma consulta com essa data'
                }
            )

    def list(self, request, *args, **kwargs):
        try:
            user = User.objects.get(id=self.request.user.id)
            queryset = MedicalConsult.objects.all()
            serializer = MedicalConsultSerializer(queryset, many=True)
            consult_list = []
            for key, value in enumerate(serializer.data):

                if value['user'] == user.id:
                    consult_list.append({
                        'id': value['id'],
                        'day': value['day'],
                        'time': value['time'],
                        'scheduling_date': value['scheduling_date'],
                        'doctor': value['doctor']
                    })
            if len(consult_list) > 1:
                return Response(consult_list)
            else:
                return Response({'message': 'Sem consultas agendadas'})

        except Exception:
            return Response({'message': 'Erro inesperado'})

    def destroy(self, request, *args, **kwargs):
        try:
            id_consult = int(self.kwargs['pk'])
            consult = MedicalConsult.objects.get(id=id_consult)
            if self.request.user == consult.user:
                consult.delete()
                return Response(status=204)
            else:
                return Response(
                    {'message': 'Você não tem permissão para fazer isso'},
                    status=403
                )
        except Exception:
            return Response(
                {'message': 'Nenhuma consulta com esse ID'},
                status=404
            )
