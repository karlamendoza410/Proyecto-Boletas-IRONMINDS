import flet as ft
import requests
import asyncio

API_URL = "http://127.0.0.1:8000"


async def main(page: ft.Page):
    #ventana
    page.title = "Panel Electoral - Escaneo de Actas"
    page.padding = 30
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 750
    page.scroll = ft.ScrollMode.AUTO


    file_picker = ft.FilePicker()


    titulo = ft.Text(
        "Sistema de Escrutinio con IA",
        style=ft.TextStyle(size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
    )

    status_icon = ft.Icon(name=ft.Icons.INFO, color=ft.Colors.BLUE_GREY_400, size=20)
    status_text = ft.Text("Listo para escanear actas...", color=ft.Colors.BLUE_GREY_700, font_family="monospace")


    loading_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)


    status_row = ft.Row([loading_spinner, status_icon, status_text], alignment=ft.MainAxisAlignment.START)


    tabla_resultados = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Partido Político", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Votos Totales", weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("Porcentaje", weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=[]
    )


    async def actualizar_grafica_y_tabla():
        loading_spinner.visible = True
        page.update()

        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: requests.get(f"{API_URL}/resultados-globales/"))

            if res.status_code == 200:
                datos = res.json()

                if "conteo_por_partido" not in datos:
                    status_text.value = datos.get("mensaje", "Sin datos en el backend.")
                    status_icon.name = ft.Icons.WARNING
                    status_icon.color = ft.Colors.ORANGE_500
                    page.update()
                    return

                tabla_resultados.rows.clear()
                for item in datos["conteo_por_partido"]:
                    tabla_resultados.rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(item["partido"], weight=ft.FontWeight.W_500)),
                                ft.DataCell(ft.Text(f"{item['votos']:,}")),
                                ft.DataCell(ft.Text(f"{item['porcentaje']}%", weight=ft.FontWeight.BOLD)),
                            ]
                        )
                    )
                status_text.value = f"Datos sincronizados. Total votos: {datos['total_votos_emitidos']:,}"
                status_icon.name = ft.Icons.CHECK_CIRCLE
                status_icon.color = ft.Colors.GREEN_600
            else:
                raise Exception("Error en respuesta de API")
        except Exception:
            status_text.value = "Error de API. Desplegando datos locales (Mock)."
            status_icon.name = ft.Icons.REPORT_PROBLEM
            status_icon.color = ft.Colors.RED_600
            inyectar_mock_data()
        finally:
            loading_spinner.visible = False
            page.update()

    def inyectar_mock_data():
        tabla_resultados.rows.clear()
        mock_items = [
            {"partido": "Partido Alianza Inteligente (PAI)", "votos": 2100, "porcentaje": 46.67},
            {"partido": "Unión de Datos Democráticos (UDD)", "votos": 1800, "porcentaje": 40.0},
            {"partido": "Frente de Código Libre (FCL)", "votos": 600, "porcentaje": 13.33}
        ]
        for item in mock_items:
            tabla_resultados.rows.append(
                ft.DataRow(cells=[ft.DataCell(ft.Text(item["partido"])), ft.DataCell(ft.Text(str(item["votos"]))),
                                  ft.DataCell(ft.Text(f"{item['porcentaje']}%"))])
            )

    # 3. ENDPOINT 2: POST /escanear-acta/ (Subida Validada)
    async def al_seleccionar_archivo(e: ft.FilePickerResultEvent):
        if not e.files:
            return

        archivo_ruta = e.files[0].path
        status_text.value = f"Ingestando {e.files[0].name}..."
        status_icon.name = ft.Icons.CLOUD_UPLOAD
        status_icon.color = ft.Colors.ORANGE_500
        loading_spinner.visible = True
        page.update()

        try:
            def enviar_post():
                with open(archivo_ruta, "rb") as f:
                    files = {"file": (e.files[0].name, f, "image/jpeg")}
                    return requests.post(f"{API_URL}/escanear-acta/", files=files)

            loop = asyncio.get_running_loop()
            respuesta = await loop.run_in_executor(None, enviar_post)

            if respuesta.status_code == 200:
                resultado_api = respuesta.json()
                if resultado_api.get("status") == "ok":
                    status_text.value = f"¡Éxito! Folio: {resultado_api.get('folio', 'N/A')}"
                    status_icon.name = ft.Icons.VERIFIED
                    status_icon.color = ft.Colors.GREEN_600
                    await actualizar_grafica_y_tabla()
                else:
                    status_text.value = f"Fallo: {resultado_api.get('mensaje')}"
                    status_icon.name = ft.Icons.ERROR
                    status_icon.color = ft.Colors.RED_600
            else:
                status_text.value = f"Error de servidor ({respuesta.status_code})"
                status_icon.name = ft.Icons.ERROR
                status_icon.color = ft.Colors.RED_600
        except Exception as ex:
            status_text.value = f"Fallo de conexión: {ex}"
            status_icon.name = ft.Icons.THUNDERSTORM
            status_icon.color = ft.Colors.RED_600
        finally:
            loading_spinner.visible = False
            page.update()

    file_picker.on_result = al_seleccionar_archivo

    btn_cargar = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.FILE_UPLOAD), ft.Text("Ingestar Acta (JPG)")], tight=True),
        on_click=lambda _: file_picker.pick_files(allow_multiple=False),
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600)
    )


    btn_refresh = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=ft.Colors.BLUE_800,
        on_click=lambda _: asyncio.create_task(actualizar_grafica_y_tabla()),
        tooltip="Sincronizar Datos"
    )


    async def confirmar_reset(e):
        def cerrar_dialogo(action):
            page.dialog.open = False
            page.update()
            if action == "si":
                asyncio.create_task(ejecutar_delete())

        page.dialog = ft.AlertDialog(
            title=ft.Text("¿Confirmar Reinicio?"),
            content=ft.Text("Esta acción borrará la información"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar_dialogo("no")),
                ft.TextButton("Sí, Resetear", on_click=lambda _: cerrar_dialogo("si")),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()

    async def ejecutar_delete():
        loading_spinner.visible = True
        status_text.value = "Borrando datos analíticos..."
        page.update()
        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: requests.delete(f"{API_URL}/reiniciar-conteo/"))
            if res.status_code == 200:
                status_text.value = "Historial electoral reseteado."
                status_icon.name = ft.Icons.DELETE_SWEEP
                status_icon.color = ft.Colors.BLUE_GREY_600
                await actualizar_grafica_y_tabla()
        except Exception as e:
            status_text.value = f"No se pudo borrar: {e}"
        finally:
            loading_spinner.visible = False
            page.update()

    btn_reset = ft.Button(
        content=ft.Row(
            [ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED_700), ft.Text("Resetear Sistema", color=ft.Colors.RED_700)],
            tight=True),
        on_click=confirmar_reset,
        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50)
    )

    # interfaz
    page.overlay.append(file_picker)

    page.add(
        ft.Row([titulo, btn_refresh], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        ft.Container(
            content=ft.Row([btn_cargar, btn_reset, status_row], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border_radius=12
        ),
        ft.Divider(height=20),
        ft.Text("Resultados Globales Acumulados (Procesados con Pandas/NumPy):",
                style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD)),
        ft.Container(content=tabla_resultados, border_radius=8, border=ft.Border.all(1, ft.Colors.GREY_300))
    )

    page.update()
    await actualizar_grafica_y_tabla()


ft.run(main)