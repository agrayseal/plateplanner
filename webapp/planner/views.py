from django.shortcuts import render, redirect, get_object_or_404
from .models import Plate
from .forms import PlateForm
import pandas as pd


# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Plate
from .forms import PlateForm
import pandas as pd

def index(request):
    plates = Plate.objects.all().order_by('pos')
    context = {'plates': plates}
    return render(request, 'planner/index.html', context)

def edit_plate(request, pos):
    plate = get_object_or_404(Plate, pk=pos)
    if request.method == 'POST':
        form = PlateForm(request.POST, instance=plate)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PlateForm(instance=plate)
    return render(request, 'planner/edit_plate.html', {'form': form, 'plate': plate})

def load_csv(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        df = pd.read_csv(file, dtype=str)
        for index, row in df.iterrows():
            Plate.objects.update_or_create(
                pos=row['pos'],
                defaults={'sample': row['sample'], 'primers': row['primers']}
            )
        return redirect('index')
    return render(request, 'planner/load_csv.html')

def save_csv(request):
    plates = Plate.objects.all().order_by('pos')
    df = pd.DataFrame.from_records(plates.values('pos', 'sample', 'primers'))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plates.csv"'
    df.to_csv(path_or_buf=response, index=False)
    return response
