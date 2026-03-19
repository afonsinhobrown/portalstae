from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import ResultadoMesa
from .forms import ResultadoMesaForm

def dashboard(request):
    resultados = ResultadoMesa.objects.all().order_by('-mesa')
    total_processados = resultados.count()
    return render(request, 'apuramento/dashboard.html', {'resultados': resultados, 'total_processados': total_processados})

def lancar_resultado(request):
    return redirect('rs:lancar_edital')

def editar_resultado(request, resultado_id):
    resultado = get_object_or_404(ResultadoMesa, id=resultado_id)
    if request.method == 'POST':
        form = ResultadoMesaForm(request.POST, instance=resultado)
        if form.is_valid():
            form.save()
            return redirect('apuramento:dashboard')
    else:
        form = ResultadoMesaForm(instance=resultado)
    return render(request, 'apuramento/form_resultado.html', {'form': form, 'titulo': 'Corrigir Lançamento'})
