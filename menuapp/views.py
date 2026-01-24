from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
import subprocess
import json
import csv
import os
import re


URL_RE = re.compile(r'^(https?://)', re.IGNORECASE)


def open_show_folder(ruta):
    subprocess.Popen(f'explorer "{ruta}"')


def open_json(file_to_open, asJSON=True):
    json_file = os.path.join(settings.BASE_DIR, "static", "data", file_to_open)
    with open(json_file, 'r', encoding='utf-8') as file:
        my_json = file.read()
    if asJSON:
        my_json = re.sub(r'%2F', '/', my_json)
        my_json = json.loads(my_json)
    return my_json


def open_csv(file_to_open, asJSON=True):
    output_dict = {}
    csv_file = os.path.join(settings.BASE_DIR, "static", "data", file_to_open)
    with open(csv_file, 'r', encoding='utf-8') as file:
        if asJSON:
            for i, fila in enumerate(csv.DictReader(file)):
                output_dict[i] = fila
        else:
            output_dict = file.read()
    return output_dict


def save(filename, data):
    full_filename = os.path.join(settings.BASE_DIR, "static", "data", filename)
    parsed_data = re.sub(r"/", "%2F", data)
    with open(full_filename, 'w', encoding='utf-8', newline='') as file:
        file.write(parsed_data)


def get_links():
    General = open_json("General.json")
    Oferta = open_json("Ofertas.json")
    lista_ofertas = open_csv("Ofertas.csv")
    Oferta["links"] = lista_ofertas
    Proyectos = open_json("Proyectos.json")
    lista_proyectos = open_csv("Proyectos.csv")
    Proyectos["links"] = lista_proyectos
    Desarrollos = open_json("Desarrollos.json")
    lista_desarrollos = open_csv("Desarrollos.csv")
    Desarrollos["links"] = lista_desarrollos
    OfObsoletas = open_json("OfObsoletas.json")
    lista_OfObsoletas = open_csv("OfObsoletas.csv")
    OfObsoletas["links"] = lista_OfObsoletas
    PrAntiguos = open_json("PrAntiguos.json")
    lista_PrAntiguos = open_csv("PrAntiguos.csv")
    PrAntiguos["links"] = lista_PrAntiguos
    return General, Oferta, Proyectos, Desarrollos, OfObsoletas, PrAntiguos


def is_url(s: str) -> bool:
    return isinstance(s, str) and bool(URL_RE.match(s))


def home(request):
    group_name_param = request.GET.get('group_name', 'General')
    General, Ofertas, Proyectos, Desarrollos, OfObsoletas, PrAntiguos = get_links()

    grupos = {
        'General': General,
        'Ofertas': Ofertas,
        'Proyectos': Proyectos,
        'Desarrollos': Desarrollos,
        'Of.Obsoletas': OfObsoletas,
        'Proy.Antiguos': PrAntiguos,
    }

    group_name = grupos.get(group_name_param, General)
    return render(request, 'index.html', {'group_name': group_name})


def editor(request, datos, filename):
    parsed_data = re.sub(r'%2F', '/', datos)
    name, extension = os.path.splitext(filename)
    
    # Usar editor de tabla para archivos CSV
    if extension == ".csv":
        return render(request, 'table_editor.html', {'datos': parsed_data, 'filename': filename})
    # Usar editor de JSON para archivos JSON
    elif extension == ".json":
        return render(request, 'json_editor.html', {'datos': parsed_data, 'filename': filename})
    else:
        return render(request, 'editor.html', {'datos': parsed_data, 'filename': filename})


def abrir(request, filename):
    name, extension = os.path.splitext(filename)
    if extension == ".csv":
        datos = open_csv(filename, asJSON=False)
    elif extension == ".json":
        datos = open_json(filename, asJSON=False)
    else:
        # Para extensiones no soportadas, redirigir al home
        return redirect(reverse('home') + '?group_name=General')
    return redirect(reverse('editor', kwargs={'datos': datos, 'filename': filename}))


def abrir_carpeta(request, folder, group_name):
    if os.path.exists(folder):
        open_show_folder(folder)
    else:
        print("La carpeta no existe")
    return redirect(reverse('home') + f'?group_name={group_name}')


def guarda(request):
    if request.method == 'POST':
        datos = request.POST['datos_modificados']
        filename = request.POST['filename']
        _, extension = os.path.splitext(request.POST['filename'])
        if extension == ".csv" or extension == ".json":
            save(filename=filename, data=datos)
        else:
            return redirect(reverse('home') + '?group_name=General')
        return redirect(reverse('home') + '?group_name=General')
    return redirect(reverse('home') + '?group_name=General')
