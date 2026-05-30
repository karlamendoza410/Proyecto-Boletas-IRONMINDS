import flet as ft
import flet_charts as fch
import requests
import asyncio

API_URL = "http://127.0.0.1:8000"

async def main(page: ft.Page):
    page.title = "Contador de votos"
    page.padding = 30
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1300 
    page.window_height = 900
    page.scroll = ft.ScrollMode.AUTO

    titulo = ft.Text(
        "Contador de boletas", 
        style=ft.TextStyle(size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
    )
    
    status_icon = ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE_GREY_400, size=20)
    status_text = ft.Text("Listo para procesar actas", color=ft.Colors.BLUE_GREY_700, font_family="monospace")
    loading_spinner = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)
    status_row = ft.Row([loading_spinner, status_icon, status_text], alignment=ft.MainAxisAlignment.START)

    input_url = ft.TextField(
        label="URL del acta", 
        hint_text="Ingresa tu URL aqui", 
        expand=True,
        border_color=ft.Colors.BLUE_400
    )
    
    texto_total_votos = ft.Text(
        "Votos Totales: 0", 
        style=ft.TextStyle(size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_ACCENT_700)
    )

    def on_chart_event(e):
        for idx, section in enumerate(grafica_pastel.sections):
            is_hovered = idx == e.section_index
            section.radius = 180 if is_hovered else 150
            
            if section.title != "":
                section.title_style = ft.TextStyle(size=20, weight="bold", color=ft.Colors.WHITE) if is_hovered else ft.TextStyle(size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                
        grafica_pastel.update()

    tabla_resultados = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Partido", weight=ft.FontWeight.BOLD)), 
            ft.DataColumn(ft.Text("Votos", weight=ft.FontWeight.BOLD), numeric=True), 
            ft.DataColumn(ft.Text("%", weight=ft.FontWeight.BOLD), numeric=True)
        ],
        rows=[]
    )
    grafica_pastel = fch.PieChart(
        sections=[],
        sections_space=3,
        center_space_radius=80,
        on_event=on_chart_event, 
        expand=True
    )

    contenedor_leyenda = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, height=250)

    # Colores
    colores = [
        ft.Colors.BLUE, ft.Colors.GREEN, ft.Colors.RED, ft.Colors.ORANGE, 
        ft.Colors.PURPLE, ft.Colors.CYAN, ft.Colors.PINK, ft.Colors.BROWN, 
        ft.Colors.TEAL, ft.Colors.YELLOW_700, ft.Colors.INDIGO
    ]

    async def actualizar_dashboard():
        loading_spinner.visible = True
        page.update()
        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: requests.get(f"{API_URL}/resultados-globales/"))
            
            if res.status_code == 200:
                datos = res.json()
                
                tabla_resultados.rows.clear()
                grafica_pastel.sections.clear()
                contenedor_leyenda.controls.clear()

                if "conteo_por_partido" not in datos or not datos["conteo_por_partido"]:
                    texto_total_votos.value = "Votos totales: 0"
                    status_text.value = datos.get("mensaje", "Sin datos en el backend")
                    status_icon.name = ft.Icons.WARNING
                    status_icon.color = ft.Colors.ORANGE_500
                    return

                total = datos['total_votos_emitidos']
                texto_total_votos.value = f"Votos totales: {total:,}"
                
                for i, item in enumerate(datos["conteo_por_partido"]):
                    color_asignado = colores[i % len(colores)]
                    
                    # 1. Tabla
                    tabla_resultados.rows.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(item["partido"], weight=ft.FontWeight.W_500)),
                            ft.DataCell(ft.Text(f"{item['votos']:,}")),
                            ft.DataCell(ft.Text(f"{item['porcentaje']}%", weight=ft.FontWeight.BOLD))
                        ])
                    )
                    if item["votos"] > 0:
                        mostrar_texto = item["porcentaje"] >= 3.0
                        texto_rebanada = f"{item['porcentaje']}%" if mostrar_texto else ""

                        grafica_pastel.sections.append(
                            fch.PieChartSection(
                                value=item["votos"],
                                title=texto_rebanada,
                                color=color_asignado,
                                radius=150, 
                                title_style=ft.TextStyle(size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                            )
                        )
                        
                        contenedor_leyenda.controls.append(
                            ft.Row([
                                ft.Container(width=15, height=15, bgcolor=color_asignado, border_radius=3),
                                ft.Text(f"{item['partido']}: {item['votos']:,} votos ({item['porcentaje']}%)", size=14, weight=ft.FontWeight.W_500)
                            ])
                        )

                status_text.value = "datos y grafica sincronizado"
                status_icon.name = ft.Icons.CHECK_CIRCLE
                status_icon.color = ft.Colors.GREEN_600
            else:
                raise Exception("error en respuesta de API")
        except Exception as ex:
            status_text.value = f"error de conexion: {ex}"
            status_icon.name = ft.Icons.REPORT_PROBLEM
            status_icon.color = ft.Colors.RED_600
        finally:
            loading_spinner.visible = False
            page.update()

    async def procesar_url_acta(e):
        url = input_url.value.strip()
        if not url:
            status_text.value = "La URL no es valida"
            status_icon.name = ft.Icons.ERROR
            status_icon.color = ft.Colors.RED_600
            page.update()
            return

        status_text.value = "Procesando imagen de azure"
        status_icon.name = ft.Icons.CLOUD_DOWNLOAD
        status_icon.color = ft.Colors.ORANGE_500
        loading_spinner.visible = True
        input_url.disabled = True
        btn_cargar.disabled = True
        page.update()

        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: requests.post(f"{API_URL}/escanear-acta/", json={"url": url}))

            if res.status_code == 200:
                resultado_api = res.json()
                
                if resultado_api.get("status") == "ok":
                    status_text.value = f"¡Éxito! Folio: {resultado_api.get('folio', 'N/A')}"
                    status_icon.name = ft.Icons.VERIFIED
                    status_icon.color = ft.Colors.GREEN_600
                    input_url.value = "" 
                    await actualizar_dashboard()
                else:
                    mensaje = resultado_api.get("mensaje", "Discrepancia detectada en el acta")
                    folio_err = resultado_api.get("folio", "Desconocido")
                    
                    status_text.value = f"Acta {folio_err} rechazada por inconsistencia"
                    status_icon.name = ft.Icons.WARNING
                    status_icon.color = ft.Colors.ORANGE_600
                    
                    dialogo_alerta = ft.AlertDialog(
                        title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_500), ft.Text("Acta Rechazada")]),
                        content=ft.Text(f"Se detecto un problema en esta acta:\n\n{mensaje}\n\nLos votos no cuadran y no se van a sumar los votos"),
                    )

                    def cerrar_alerta(_):
                        dialogo_alerta.open = False
                        page.update()

                    dialogo_alerta.actions = [ft.TextButton("Entendido", on_click=cerrar_alerta)]
                    page.overlay.append(dialogo_alerta)
                    dialogo_alerta.open = True
                    page.update()
                    
            else:
                detalle = res.json().get('detail', 'Error desconocido')
                status_text.value = f"Error: {detalle}"
                status_icon.name = ft.Icons.ERROR
                status_icon.color = ft.Colors.RED_600
        except Exception as ex:
            status_text.value = f"Fallo de conexión: {ex}"
            status_icon.name = ft.Icons.THUNDERSTORM
            status_icon.color = ft.Colors.RED_600
        finally:
            loading_spinner.visible = False
            input_url.disabled = False
            btn_cargar.disabled = False
            page.update()

    async def ejecutar_delete():
        loading_spinner.visible = True
        status_text.value = "Borrando datos"
        page.update()
        
        try:
            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, lambda: requests.delete(f"{API_URL}/reiniciar-conteo/"))
            
            if res.status_code == 200:
                status_text.value = "Historial electoral eliminado."
                status_icon.name = ft.Icons.DELETE_SWEEP
                status_icon.color = ft.Colors.BLUE_GREY_600
                await actualizar_dashboard() 
            else:
                status_text.value = f"La API rechazo el borrado (Error {res.status_code})."
                status_icon.name = ft.Icons.ERROR
                status_icon.color = ft.Colors.RED_600
        except Exception as ex:
            status_text.value = f"error de conexion con API: {ex}"
            status_icon.name = ft.Icons.REPORT_PROBLEM
            status_icon.color = ft.Colors.RED_600
        finally:
            loading_spinner.visible = False
            page.update()

    async def confirmar_reset(_):
        dialogo_reset = ft.AlertDialog(
            title=ft.Text("Confirmar reinicio?"),
            content=ft.Text("Se van a eliminar todos los datos"),
            actions_alignment=ft.MainAxisAlignment.END,
        )

        async def accionar_borrado(_):
            dialogo_reset.open = False
            page.update()
            await ejecutar_delete()

        async def cancelar_borrado(_):
            dialogo_reset.open = False
            page.update()

        dialogo_reset.actions = [
            ft.TextButton("Cancelar", on_click=cancelar_borrado),
            ft.TextButton("Sí, Resetear", on_click=accionar_borrado),
        ]

        page.overlay.append(dialogo_reset)
        dialogo_reset.open = True
        page.update()

    # --- Componentes y Botones ---
    btn_cargar = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME), ft.Text("Procesar URL")], tight=True),
        on_click=procesar_url_acta,
        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600)
    )

    btn_reset = ft.Button(
        content=ft.Row([ft.Icon(ft.Icons.DELETE, color=ft.Colors.RED_700), ft.Text("Resetear sistema", color=ft.Colors.RED_700)], tight=True),
        on_click=confirmar_reset,
        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50)
    )

    # --- Layout Principal ---
    page.add(
        ft.Row([titulo, ft.IconButton(icon=ft.Icons.REFRESH, icon_color=ft.Colors.BLUE_800, on_click=lambda _: asyncio.create_task(actualizar_dashboard()), tooltip="Sincronizar datos")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        
        ft.Row([input_url, btn_cargar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        ft.Container(
            content=ft.Row([btn_reset, status_row], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            bgcolor=ft.Colors.GREY_100,
            border_radius=12,
            margin=10
        ),
        
        ft.Divider(height=20),
        texto_total_votos,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        
        ft.Row(
            [
                ft.Column([
                    ft.Text("Tabla de Resultados", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(content=tabla_resultados, border_radius=8, border=ft.Border.all(1, ft.Colors.GREY_300))
                ], expand=1),
                ft.VerticalDivider(width=1),
                
                ft.Column([
                    ft.Text("Distribución de Votos", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(grafica_pastel, height=500, width=500),                    
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Text("Leyenda de Partidos", size=14, weight=ft.FontWeight.BOLD),
                    contenedor_leyenda
                ], expand=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    )

    page.update()
    await actualizar_dashboard()

ft.run(main)