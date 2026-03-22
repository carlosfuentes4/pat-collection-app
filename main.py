import os
import sys
import random
import subprocess
import tempfile

import requests
import flet as ft


class MainWindow:
    def __init__(self, page: ft.Page):
        self.page = page
        self.API_KEY = "0e0c969a4361b574abb5bb8c"
        self.tasa_actual = None
        self._precio_usd = None
        self._precio_hnl = None
        self._costo_usd  = None
        self._costo_hnl  = None
        self._ultimo_png = None  # ruta de la última etiqueta generada

        self.page_setup()
        self.create_component()
        self.build_ui()
        self.page.update()

    def page_setup(self):
        self.page.title = "App de Precios – Pat Collection"
        self.page.window.width = 450
        self.page.window.height = 720
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#1a1a2e"
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.update()

    # ─── API ───
    def obtener_tasa_hnl(self):
        if self.tasa_actual:
            return self.tasa_actual
        url = f"https://v6.exchangerate-api.com/v6/{self.API_KEY}/latest/USD"
        try:
            response = requests.get(url, timeout=6)
            data = response.json()
            if data["result"] == "success":
                self.tasa_actual = data["conversion_rates"]["HNL"]
                return self.tasa_actual
        except Exception as e:
            print(f"Error de conexión: {e}")
        return None

    def convertir_usd_a_hnl(self, cantidad_usd):
        tasa = self.obtener_tasa_hnl()
        return cantidad_usd * tasa if tasa else None

    def convertir_hnl_a_usd(self, cantidad_hnl):
        tasa = self.obtener_tasa_hnl()
        return cantidad_hnl / tasa if tasa else None

    # ─── Alertas ───
    def show_message(self, message):
        self.dlg = ft.AlertDialog(
            title=ft.Text("Aviso", color="#ffffff"),
            content=ft.Text(message, color="#ffffff", size=15),
            bgcolor="#16213e",
            actions=[ft.TextButton("OK", on_click=lambda _: self._cerrar_alerta())],
        )
        self.page.overlay.append(self.dlg)
        self.dlg.open = True
        self.page.update()

    def _cerrar_alerta(self):
        self.dlg.open = False
        self.page.update()

    # ─── Componentes ───
    def create_component(self):
        self.moneda_radio = ft.RadioGroup(
            content=ft.Row(
                [
                    ft.Radio(value="USD", label="USD ($)", fill_color="#e94560"),
                    ft.Radio(value="HNL", label="Lempiras (L)", fill_color="#e94560"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            value="USD",
        )

        self.prefijo_costo = ft.Text("$ ", color="#aaaaaa")
        self.campo_costo = ft.TextField(
            label="Costo del producto",
            prefix=self.prefijo_costo,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#e94560",
            focused_border_color="#ff6b6b",
            color="#ffffff",
            label_style=ft.TextStyle(color="#aaaaaa"),
            bgcolor="#16213e",
            border_radius=10,
            on_change=self._actualizar_prefijo,
        )

        self.campo_margen = ft.TextField(
            label="Margen de ganancia (%)",
            suffix=ft.Text(" %", color="#aaaaaa"),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#e94560",
            focused_border_color="#ff6b6b",
            color="#ffffff",
            label_style=ft.TextStyle(color="#aaaaaa"),
            bgcolor="#16213e",
            border_radius=10,
        )

        margenes = [10, 20, 30, 40, 50, 60]
        self.botones_margen = ft.Row(
            [
                ft.FilledButton(
                    f"{m}%",
                    on_click=lambda e, m=m: self._set_margen(m),
                    style=ft.ButtonStyle(
                        bgcolor={"": "#0f3460"},
                        color={"": "#ffffff"},
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                )
                for m in margenes
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True,
        )

        self.btn_calcular = ft.FilledButton(
            "Calcular Precio de Venta",
            icon=ft.Icons.CALCULATE,
            on_click=self.calcular,
            style=ft.ButtonStyle(
                bgcolor={"": "#e94560"},
                color={"": "#ffffff"},
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=4,
            ),
            width=300,
            height=50,
        )

        self.lbl_precio_usd = ft.Text("—", size=22, weight=ft.FontWeight.BOLD, color="#e94560")
        self.lbl_ganancia   = ft.Text("—", size=15, color="#aaaaaa")
        self.lbl_tasa       = ft.Text("Tasa: obteniendo…", size=12, color="#555555")

        self.campo_precio_hnl = ft.TextField(
            value="—",
            text_align=ft.TextAlign.CENTER,
            text_style=ft.TextStyle(size=22, weight=ft.FontWeight.BOLD, color="#4ecca3"),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#333355",
            focused_border_color="#4ecca3",
            bgcolor="transparent",
            border_radius=8,
            width=160,
            on_change=self._precio_hnl_editado,
            hint_text="L 0",
            hint_style=ft.TextStyle(color="#555555"),
        )

        self.card_resultado = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Precio de Venta", size=14, color="#aaaaaa"),
                    ft.Row(
                        [
                            ft.Column(
                                [ft.Text("USD", size=12, color="#aaaaaa"), self.lbl_precio_usd],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.VerticalDivider(color="#333355"),
                            ft.Column(
                                [
                                    ft.Row(
                                        [ft.Text("HNL", size=12, color="#aaaaaa"),
                                         ft.Icon(ft.Icons.EDIT, size=11, color="#555577")],
                                        spacing=4,
                                    ),
                                    self.campo_precio_hnl,
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    ),
                    ft.Divider(color="#333355"),
                    self.lbl_ganancia,
                    self.lbl_tasa,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor="#16213e",
            border_radius=16,
            padding=20,
            border=ft.Border.all(1, "#333355"),
            visible=False,
        )

        self.btn_etiqueta = ft.FilledButton(
            "🏷️  Crear Etiqueta",
            on_click=self._abrir_dialogo_etiqueta,
            style=ft.ButtonStyle(
                bgcolor={"": "#4ecca3"},
                color={"": "#1a1a2e"},
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=4,
            ),
            width=300,
            height=50,
            visible=False,
        )

        # ── Botón compartir ──
        self.btn_compartir = ft.FilledButton(
            "📤  Compartir Etiqueta",
            on_click=self._compartir_etiqueta,
            style=ft.ButtonStyle(
                bgcolor={"": "#0f3460"},
                color={"": "#ffffff"},
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=4,
            ),
            width=300,
            height=50,
            visible=False,
        )

        self.btn_limpiar = ft.TextButton(
            "Limpiar",
            icon=ft.Icons.CLEAR,
            on_click=self.limpiar,
            style=ft.ButtonStyle(color={"": "#aaaaaa"}),
        )

    # ─── UI Layout ───
    def build_ui(self):
        header = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.SHOPPING_BAG_ROUNDED, size=40, color="#e94560"),
                    ft.Text("Pat Collection", size=24, weight=ft.FontWeight.BOLD, color="#ffffff"),
                    ft.Text("Calculadora de precios", size=13, color="#aaaaaa"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding.only(bottom=10),
        )

        self.page.add(
            header,
            ft.Text("Moneda del costo", size=13, color="#aaaaaa"),
            self.moneda_radio,
            self.campo_costo,
            self.campo_margen,
            ft.Text("Márgenes rápidos:", size=13, color="#aaaaaa"),
            self.botones_margen,
            ft.Container(height=6),
            ft.Row([self.btn_calcular], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.btn_limpiar], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=4),
            self.card_resultado,
            ft.Container(height=8),
            ft.Row([self.btn_etiqueta],   alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=6),
            ft.Row([self.btn_compartir],  alignment=ft.MainAxisAlignment.CENTER),
        )

    # ─── Lógica ───
    def _actualizar_prefijo(self, e):
        self.prefijo_costo.value = "$ " if self.moneda_radio.value == "USD" else "L "
        self.page.update()

    def _set_margen(self, valor):
        self.campo_margen.value = str(valor)
        self.page.update()

    def calcular(self, e):
        try:
            costo_raw = float(self.campo_costo.value.replace(",", "."))
        except (ValueError, TypeError):
            self.show_message("Ingresa un costo válido.")
            return
        try:
            margen = float(self.campo_margen.value.replace(",", "."))
            if not (0 < margen < 151):
                raise ValueError
        except (ValueError, TypeError):
            self.show_message("Ingresa un margen entre 1 y 150 %.")
            return

        moneda = self.moneda_radio.value
        if moneda == "USD":
            costo_usd = costo_raw
            costo_hnl = self.convertir_usd_a_hnl(costo_usd)
        else:
            costo_hnl = costo_raw
            costo_usd = self.convertir_hnl_a_usd(costo_hnl)

        if costo_usd is None or costo_hnl is None:
            self.show_message("No se pudo obtener la tasa de cambio. Verifica tu conexión.")
            return

        factor     = margen / 100
        precio_usd = costo_usd + (costo_usd * factor)
        precio_hnl = self._redondear_precio(costo_hnl + (costo_hnl * factor))

        self._costo_usd  = costo_usd
        self._costo_hnl  = costo_hnl
        self._precio_usd = precio_usd
        self._precio_hnl = precio_hnl

        ganancia_usd = precio_usd - costo_usd
        ganancia_hnl = precio_hnl - costo_hnl

        self.lbl_precio_usd.value   = f"$ {precio_usd:,.2f}"
        self.campo_precio_hnl.value = f"{precio_hnl:,.0f}"
        self.lbl_ganancia.value     = f"Ganancia:  $ {ganancia_usd:,.2f}  /  L {ganancia_hnl:,.2f}"
        tasa = self.obtener_tasa_hnl()
        self.lbl_tasa.value = f"Tasa USD → HNL: {tasa:.4f}" if tasa else "Tasa: no disponible"

        self.card_resultado.visible = True
        self.btn_etiqueta.visible   = True
        self.page.update()

    def limpiar(self, e):
        self.campo_costo.value        = ""
        self.campo_margen.value       = ""
        self.campo_precio_hnl.value   = "—"
        self.card_resultado.visible   = False
        self.btn_etiqueta.visible     = False
        self.btn_compartir.visible    = False
        self._precio_usd = None
        self._precio_hnl = None
        self._costo_usd  = None
        self._costo_hnl  = None
        self._ultimo_png = None
        self.page.update()

    def _redondear_precio(self, precio: float) -> float:
        return float(round(precio))

    def _precio_hnl_editado(self, e):
        if self._costo_hnl is None:
            return
        try:
            nuevo = float(
                self.campo_precio_hnl.value
                .replace(",", "")
                .replace("L", "")
                .strip()
            )
            if nuevo <= 0:
                return
        except (ValueError, TypeError):
            return

        tasa = self.obtener_tasa_hnl()
        self._precio_hnl = nuevo
        self._precio_usd = nuevo / tasa if tasa else self._precio_usd

        ganancia_hnl = nuevo - self._costo_hnl
        ganancia_usd = ganancia_hnl / tasa if tasa else 0

        self.lbl_precio_usd.value = f"$ {self._precio_usd:,.2f}"
        self.lbl_ganancia.value   = (
            f"Ganancia:  $ {ganancia_usd:,.2f}  /  L {ganancia_hnl:,.2f}"
        )
        self.page.update()

    # ─── Compartir etiqueta ───
    def _compartir_etiqueta(self, e):
        if not self._ultimo_png or not os.path.exists(self._ultimo_png):
            self.show_message("Primero genera una etiqueta.")
            return

        try:
            # iOS — usa el share sheet nativo (WhatsApp, correo, AirDrop, etc.)
            if sys.platform == "ios" or sys.platform == "darwin":
                subprocess.run(["open", self._ultimo_png])

            # Android
            elif "/data/user" in os.path.abspath(__file__) or "com.flet" in os.path.abspath(__file__):
                try:
                    from android.content import Intent
                    from android.net import Uri
                    import android
                    intent = Intent(Intent.ACTION_SEND)
                    intent.setType("image/png")
                    intent.putExtra(Intent.EXTRA_STREAM, Uri.parse(f"file://{self._ultimo_png}"))
                    android.mActivity.startActivity(Intent.createChooser(intent, "Compartir etiqueta"))
                except Exception:
                    subprocess.run(["xdg-open", self._ultimo_png])

            # Windows
            elif sys.platform == "win32":
                os.startfile(self._ultimo_png)

            else:
                subprocess.run(["xdg-open", self._ultimo_png])

        except Exception as ex:
            self.show_message(f"No se pudo compartir:\n{ex}")

    # ─── Diálogo nombre/descripción ───
    def _abrir_dialogo_etiqueta(self, e):
        if self._precio_usd is None:
            self.show_message("Primero calcula un precio.")
            return

        self._campo_nombre = ft.TextField(
            label="Nombre del producto",
            hint_text="Ej: Blusa floral talla M",
            border_color="#e94560",
            focused_border_color="#ff6b6b",
            color="#ffffff",
            label_style=ft.TextStyle(color="#aaaaaa"),
            hint_style=ft.TextStyle(color="#555555"),
            bgcolor="#0f0f1e",
            border_radius=8,
            autofocus=True,
        )
        self._campo_desc = ft.TextField(
            label="Descripción / talla (opcional)",
            hint_text="Ej: Talla S  |  Ref. 001",
            border_color="#555577",
            focused_border_color="#4ecca3",
            color="#ffffff",
            label_style=ft.TextStyle(color="#aaaaaa"),
            hint_style=ft.TextStyle(color="#555555"),
            bgcolor="#0f0f1e",
            border_radius=8,
        )

        self._dlg_etiqueta = ft.AlertDialog(
            modal=True,
            title=ft.Text("Datos de la etiqueta", color="#ffffff", weight=ft.FontWeight.BOLD),
            bgcolor="#16213e",
            content=ft.Column(
                [self._campo_nombre, self._campo_desc],
                tight=True,
                spacing=12,
            ),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda _: self._cerrar_dlg_etiqueta(),
                    style=ft.ButtonStyle(color={"": "#aaaaaa"}),
                ),
                ft.FilledButton(
                    "Generar imagen",
                    icon=ft.Icons.IMAGE,
                    on_click=self._confirmar_etiqueta,
                    style=ft.ButtonStyle(
                        bgcolor={"": "#4ecca3"},
                        color={"": "#1a1a2e"},
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self._dlg_etiqueta)
        self._dlg_etiqueta.open = True
        self.page.update()

    def _cerrar_dlg_etiqueta(self):
        self._dlg_etiqueta.open = False
        self.page.update()

    def _confirmar_etiqueta(self, e):
        nombre = (self._campo_nombre.value or "").strip()
        if not nombre:
            self._campo_nombre.error_text = "Escribe un nombre para el producto"
            self.page.update()
            return
        desc = (self._campo_desc.value or "").strip()
        self._cerrar_dlg_etiqueta()
        self.crear_etiqueta_imagen(nombre, desc)

    # ─── Generar etiqueta como PNG ───
    def crear_etiqueta_imagen(self, nombre: str, descripcion: str):
        try:
            import barcode
            from barcode.writer import ImageWriter
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as err:
            self.show_message(
                f"Dependencia faltante:\n{err}\n\nEjecuta:\nuv add python-barcode[images] pillow"
            )
            return

        codigo_num     = str(random.randint(100_000_000_000, 999_999_999_999))
        codigo_display = f"PC-{codigo_num[:4]}-{codigo_num[4:8]}-{codigo_num[8:]}"

        tmp_dir      = tempfile.gettempdir()
        barcode_base = os.path.join(tmp_dir, f"bc_{codigo_num}")
        bc = barcode.get("code128", codigo_num, writer=ImageWriter())
        bc.save(
            barcode_base,
            options={
                "module_height": 15,
                "module_width": 0.38,
                "font_size": 9,
                "text_distance": 4,
                "quiet_zone": 3,
                "write_text": True,
                "background": "white",
                "foreground": "black",
            },
        )
        barcode_png = barcode_base + ".png"

        W, H   = 900, 550
        img    = Image.new("RGB", (W, H), color="#1a1a2e")
        draw   = ImageDraw.Draw(img)

        def get_font(size, bold=False, italic=False):
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
            except Exception:
                base_dir = ""
            assets_dir = os.path.join(base_dir, "assets")
            if italic:
                candidates = [
                    os.path.join(assets_dir, "italic.ttf"),
                    "KUNSTLER.TTF", "Gabriola.ttf", "timesi.ttf",
                    "DejaVuSerif-Italic.ttf",
                ]
            elif bold:
                candidates = [
                    os.path.join(assets_dir, "bold.ttf"),
                    "impact.ttf", "Impact.ttf", "arialbd.ttf",
                    "DejaVuSans-Bold.ttf",
                ]
            else:
                candidates = [
                    os.path.join(assets_dir, "regular.ttf"),
                    "arial.ttf", "Arial.ttf",
                    "DejaVuSans.ttf",
                ]
            for name in candidates:
                try:
                    return ImageFont.truetype(name, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        def text_width(text, font):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]

        HEADER_H = 148
        draw.rectangle([0, 0, W, HEADER_H], fill="#000000")

        font_pat        = get_font(52, bold=True)
        font_collection = get_font(76, italic=True)
        txt_pat        = "PAT"
        txt_collection = "Collection"
        w_pat  = text_width(txt_pat, font_pat)
        w_col  = text_width(txt_collection, font_collection)
        gap    = 3
        total  = w_pat + gap + w_col
        x_pat  = (W - total) // 2
        x_col  = x_pat + w_pat + gap
        y_logo = 40
        draw.text((x_pat, y_logo),      txt_pat,        font=font_pat,        fill="white")
        draw.text((x_col, y_logo - 12), txt_collection, font=font_collection, fill="white")

        font_sub = get_font(20)
        draw.text((W // 2, 118), "Moda & Estilo", font=font_sub, fill="#ffd0d8", anchor="mm")
        lw = 180
        draw.line([(W//2 - lw, 130), (W//2 + lw, 130)], fill="#ffffff44", width=1)

        font_nombre  = get_font(28, bold=True)
        nombre_corto = nombre[:40] + ("…" if len(nombre) > 40 else "")
        draw.text((W // 2, 170), nombre_corto, font=font_nombre, fill="#ffffff", anchor="mm")

        if descripcion:
            font_desc  = get_font(22)
            desc_corta = descripcion[:50] + ("…" if len(descripcion) > 50 else "")
            draw.text((W // 2, 204), desc_corta, font=font_desc, fill="#aaaaaa", anchor="mm")

        font_label  = get_font(22, bold=True)
        font_precio = get_font(68, bold=True)
        draw.text((W // 2, 238), "PRECIO:", font=font_label, fill="#898989", anchor="mm")
        draw.text((W // 2, 302), f"L {self._precio_hnl:,.2f}", font=font_precio, fill="white", anchor="mm")

        draw.line([(30, 338), (W - 30, 338)], fill="#2a2a4a", width=2)

        bc_img = Image.open(barcode_png).convert("RGBA")
        bc_area_w, bc_area_h = 820, 165
        bc_x0 = (W - bc_area_w) // 2
        bc_y0 = 348
        draw.rectangle([bc_x0, bc_y0, bc_x0 + bc_area_w, bc_y0 + bc_area_h], fill="white", outline="#2a2a4a", width=1)
        bc_resized = bc_img.resize((bc_area_w - 20, bc_area_h - 20), Image.LANCZOS)
        img.paste(bc_resized, (bc_x0 + 10, bc_y0 + 5), bc_resized)

        font_cod = get_font(18)
        draw.text((W // 2, 528), codigo_display, font=font_cod, fill="#888888", anchor="mm")

        etiquetas_dir = self._get_directorio_etiquetas()
        nombre_archivo = "".join(c if c.isalnum() or c in " _-" else "_" for c in nombre).strip()
        nombre_archivo = nombre_archivo.replace(" ", "_")[:40]
        png_path = os.path.join(etiquetas_dir, f"{nombre_archivo}_{codigo_num[-6:]}.png")

        img.save(png_path, "PNG", dpi=(300, 300))

        # Guardar ruta para compartir después
        self._ultimo_png = png_path

        # Mostrar botón compartir
        self.btn_compartir.visible = True
        self.page.update()

        # Abrir automáticamente en escritorio
        try:
            if sys.platform == "win32":
                os.startfile(png_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", png_path])
        except Exception:
            pass

        self.show_message(
            f"Etiqueta generada!\n\n"
            f"Producto: {nombre}\n"
            f"Codigo: {codigo_display}\n\n"
            f"Usa el botón Compartir para enviarla por WhatsApp."
        )

    def _get_directorio_etiquetas(self):
        try:
            es_android = "/data/user" in os.path.abspath(__file__) or \
                        "com.flet" in os.path.abspath(__file__)
            if es_android:
                base = "/storage/emulated/0/DCIM/PatCollection"
            elif sys.platform == "ios":
                base = os.path.expanduser("~/Documents/etiquetas")
            else:
                base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "etiquetas")
            os.makedirs(base, exist_ok=True)
            return base
        except Exception:
            fallback = os.path.join(tempfile.gettempdir(), "etiquetas")
            os.makedirs(fallback, exist_ok=True)
            return fallback


def main(page: ft.Page):
    MainWindow(page)


if __name__ == "__main__":
    ft.run(main)