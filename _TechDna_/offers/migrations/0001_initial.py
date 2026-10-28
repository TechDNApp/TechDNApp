# Sesión 9: ofertas de empleo, contraofertas y caducidad.

import django.core.validators
import django.db.models.deletion
from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('assessments', '0006_assessment_idx_assessment_active_mode_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_title', models.CharField(max_length=150)),
                ('salary', models.DecimalField(decimal_places=2, help_text='Salario bruto anual en euros.', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('modality', models.CharField(choices=[('remote', 'Remoto'), ('hybrid', 'Híbrido'), ('onsite', 'Presencial')], default='remote', max_length=10)),
                ('message', models.TextField(blank=True, max_length=2000)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('accepted', 'Aceptada'), ('rejected', 'Rechazada'), ('cancelled', 'Cancelada'), ('countered', 'Contraofertada'), ('expired', 'Caducada')], default='pending', max_length=12)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('responded_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_offers', to='assessments.assessment')),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_job_offers', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proposed_job_offers', to=settings.AUTH_USER_MODEL)),
                ('evaluator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_job_offers', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counter_offers', to='offers.joboffer')),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['candidate', 'status'], name='idx_offer_candidate_status'),
                    models.Index(fields=['evaluator', 'status'], name='idx_offer_evaluator_status'),
                ],
                'constraints': [
                    models.CheckConstraint(condition=models.Q(('salary__gt', 0)), name='check_offer_salary_positive'),
                    models.CheckConstraint(condition=models.Q(('evaluator', models.F('candidate')), _negated=True), name='check_offer_not_self'),
                    models.UniqueConstraint(condition=models.Q(('status', 'pending')), fields=('assessment', 'candidate'), name='unique_pending_offer_per_assessment_candidate'),
                ],
            },
        ),
    ]
