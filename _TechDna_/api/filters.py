import django_filters
from assessments.models import Assessment

class AssessmentFilter(django_filters.FilterSet):
    """
    Filtro avanzado para las evaluaciones de TechDNA.
    Permite filtrar por tecnología, rol y búsqueda exacta o parcial según sea necesario.
    """
    class Meta:
        model = Assessment
        fields = {
            "technology": ["exact"],
            "role": ["exact"],
        }