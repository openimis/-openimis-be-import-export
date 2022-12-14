from django.shortcuts import render
from django.views import View
from tablib import Dataset

from .forms import ImportForm
from .resource import InsureeResource

# Create your views here.

# https://vinaykumarmaurya30.medium.com/import-data-using-django-import-export-library-479871df2536

class ImportExpenseView(View):

    def get(self,request):
        form = ImportForm()
        return render(request,'report/import.html',{'form':form})

    def post(self,request):
        form = ImportForm(request.POST, request.FILES)
        expense_resource = InsureeResource()
        data_set = Dataset()
        if form.is_valid():
            file = request.FILES['import_file']
            imported_data = data_set.load(file.read())
            result = expense_resource.import_data(data_set, dry_run=True)  # Test the data import

            if not result.has_errors():
                expense_resource.import_data(data_set, dry_run=False)  # Actually import now

        else:
            form = ImportForm()
        return render(request, 'report/import.html', {'form': form})