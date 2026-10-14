from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)

from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .forms import AssessmentForm
from .models import Assessment

class AssessmentListView(ListView):
    model = Assessment
    template_name = "assessments/list.html"
    context_object_name = "assessments"

class AssessmentDetailView(DetailView):
    model = Assessment
    template_name = "assessments/detail.html"
    context_object_name = "assessment"

class AssessmentCreateView(LoginRequiredMixin, CreateView):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/create.html"
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class AssessmentUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView
):
    model = Assessment
    form_class = AssessmentForm
    template_name = "assessments/create.html"
    def test_func(self):
        assessment = self.get_object()
        return assessment.owner == self.request.user

class AssessmentDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView
):
    model = Assessment
    template_name = "assessments/confirm_delete.html"
    success_url = reverse_lazy("assessments:list")
    def test_func(self):
        assessment = self.get_object()
        return assessment.owner == self.request.user