# ALMI Financiera — Especificaciones de contenido para producción visual

Noviembre 2026 · Para generación de imagen con Magnific (Mystic, Upscaler, Relight)

> Este documento acompaña a `Lote_creativos_noviembre2026.md`, que tiene los
> guiones y el copy. Aquí van las especificaciones visuales y los prompts.
> Las dos cosas se leen juntas.

---

## 0. Qué hace y qué no hace esta herramienta

Magnific genera y mejora **imágenes fijas**. No genera video. Entonces:

- Los seis videos se resuelven con **fotogramas clave generados aquí** más
  animación externa o rodaje. Este documento entrega los prompts de esos
  fotogramas.
- Las piezas estáticas sí salen completas de aquí.
- **El texto NO se genera dentro de la imagen.** Los modelos de imagen
  escriben mal en español y arruinan la tipografía de marca. Todo el texto se
  monta en post, en Poppins. Los prompts de abajo piden composiciones con
  espacio vacío reservado para ese texto.

---

## 1. Restricciones de marca · obligatorias en toda pieza

### Paleta oficial, y solo esta

| Color | HEX | Uso | Proporción |
|---|---|---|---|
| Azul oscuro | `#051B3E` | Base, fondos, confianza | 40-50% |
| Celeste vívido | `#009AC9` | CTA, acentos, movimiento | 25-35% |
| Blanco | `#FFFFFF` | Respiración visual | 20-30% |
| Negro | `#000000` | Solo texto legal | 5% |
| Neutro | `#F4F7FA` | Fondos secundarios | — |

Nada de dorados, verdes de "dinero", rojos de urgencia ni degradados arcoíris.
Si la foto generada trae colores fuera de paleta en ropa o entorno, se corrige
con **Relight** hacia temperatura fría azulada, o se regenera.

### Tipografía

Poppins. Bold para títulos y cifras, SemiBold para subtítulos, Regular para
cuerpo, Light para legal. **Máximo dos pesos por pieza.** Montserrat solo en
piezas B2B. Nunca Arial.

Las cifras y cuotas van en Poppins Bold: son el argumento más fuerte de la
marca y deben pesar visualmente.

### Logo

Esquina superior izquierda en piezas rectangulares. Zona de exclusión igual a
la altura de la A del ícono por todos los lados. No distorsionar, no rotar, no
aplicar sombras. El logo se monta en post, nunca se genera.

### Concepto rector

**"El respiro que te impulsa".** Cada pieza debe producir alivio, no presión.
Arquetipo Cuidador: protege y acompaña, nunca empuja.

Traducido a imagen: hombros bajos, respiración, luz suave, espacio. Nunca
gestos de angustia extrema, nunca relojes de arena, nunca cuentas regresivas,
nunca manos arrebatando dinero.

---

## 2. Casting y dirección de arte

Las dos personas de la marca. Toda pieza B2C debe ser una de las dos.

### Carlos Andrés — el padre esforzado

Hombre colombiano, 35 a 48 años, piel trigueña a morena, contextura media,
aspecto de trabajador operativo real: logística, manufactura, servicios,
vigilancia. Manos trabajadas. Nada de modelo de catálogo, nada de dentadura
perfecta, nada de traje.

Vestuario: camisa de trabajo o polo, chaqueta sencilla, colores neutros o
azules. Si lleva uniforme, que sea genérico y **sin logotipos legibles**.

Entorno: bodega, taller, patio de maniobras, transporte público, casa de
barrio popular colombiano.

### Paola Andrea — la mujer multitarea

Mujer colombiana, 28 a 42 años, piel trigueña a morena, aspecto administrativo
o de servicios. Madre o jefa de hogar. Expresión resuelta, no sufrida.

Vestuario: blusa sencilla, cardigan, colores neutros o celestes.

Entorno: oficina pequeña, cocina de casa, transporte público, parque de barrio.

### Reglas de realismo

- Rasgos latinoamericanos colombianos, **no genéricos de banco de imágenes**.
- Luz natural, hora dorada suave o luz de interior cálida compensada en frío.
- Nada de sonrisas exageradas sosteniendo billetes.
- Nada de billetes, monedas, alcancías ni símbolos de dinero. El dinero en
  ALMI se representa con **tranquilidad y movimiento**, no con efectivo.
- Dispositivo: celular de gama media, nunca el último modelo de lujo.

---

## 3. Formatos técnicos

| Pieza | Relación | Resolución de entrega | Zona segura |
|---|---|---|---|
| Video vertical (fotogramas) | 9:16 | 1080 × 1920 | 250 px arriba, 420 px abajo |
| Estático feed | 4:5 | 1080 × 1350 | 120 px por lado |
| Estático cuadrado | 1:1 | 1080 × 1080 | 100 px por lado |

Generar en Mystic a la relación nativa, luego **Upscaler a 2×** y bajar a la
resolución de entrega. Eso da bordes limpios y piel con textura real.

### Ajustes sugeridos de Magnific

- **Mystic:** realismo alto, fidelidad al prompt media-alta.
- **Upscaler:** engine Illusio para retrato y piel; creativity baja (0 a 1)
  para no inventar rasgos; HDR bajo (0 a 2) para no caer en el aspecto
  sobreprocesado; resemblance alta para respetar el original.
- **Relight:** solo para empujar la temperatura hacia el azul de marca cuando
  la toma salga demasiado cálida.
- **Style Transfer:** no usar. Rompe la coherencia entre piezas.

Lo sobreprocesado es el error más frecuente y el más dañino aquí: una imagen
con HDR alto se lee como publicidad agresiva, que es justo lo contrario del
arquetipo Cuidador.

---

## 4. Prompts · fotogramas de los seis videos

Estructura de cada prompt: sujeto, acción, entorno, luz, encuadre, espacio
para texto. En inglés, que es donde el modelo responde mejor.

### Negativo común a todos

```
text, letters, words, watermark, logo, brand names, uniform logos,
cash, banknotes, coins, piggy bank, money symbols,
stock photo smile, perfect teeth, fashion model, suit and tie,
hourglass, countdown, red warning colors, cluttered background,
oversaturated, HDR halo, plastic skin, extra fingers
```

### V1 · "Los cincuenta documentos" — fricción del banco

**Fotograma A (0-3s):**
```
Colombian working-class man, 40 years old, tan skin, weathered hands,
holding a thick overflowing folder of paperwork, tired resigned expression,
plain neutral office waiting room, cool desaturated light,
vertical 9:16 composition, subject in lower third,
large empty space in upper half for text overlay, photorealistic
```

**Fotograma B (13-18s):**
```
Same Colombian man, relaxed shoulders, calm relieved expression,
looking at a mid-range smartphone in his hands, warm natural window light
with cool blue tones, modest home interior out of focus,
vertical 9:16, subject lower third, clean empty space above, photorealistic
```

### V2 · "La fila" — fricción del banco

**Fotograma A:**
```
Long queue of people waiting inside a plain institutional branch office,
shot from behind, anonymous, cold fluorescent light, muted colors,
sense of slow time, vertical 9:16, wide empty ceiling space for text
```

**Fotograma B:**
```
Colombian woman, 35 years old, sitting on her sofa at home with a
smartphone, calm and unhurried, soft daylight from a window,
modest Colombian apartment, vertical 9:16, subject right side,
empty space on the left for text, photorealistic
```

### V3 · "Tu trabajo responde" — la nómina como respaldo

**Fotograma A:**
```
Colombian man in generic work clothes without any visible logo,
standing confidently at his workplace in a warehouse,
arms relaxed at his sides, steady gaze to camera,
soft industrial daylight, blue tones, vertical 9:16,
subject centered lower, open space above for text, photorealistic
```

**Fotograma B (montaje de oficios):**
```
Series concept: Colombian workers in different ordinary trades,
logistics, light manufacturing, cleaning services, security,
all generic uniforms with no readable logos, neutral and blue palette,
natural light, each framed vertical 9:16 with space for text
```

### V4 · "La cuota que cabe" — la nómina como respaldo

**Fotograma A:**
```
Close-up of Colombian hands holding a mid-range smartphone,
thumb adjusting a slider on a clean blue and white interface,
soft daylight, shallow depth of field, modest home table surface,
vertical 9:16, device in lower half, empty space above, photorealistic
```

> La interfaz se monta en post con la pantalla real del cotizador. En el
> prompt se pide un celular con pantalla neutra o apagada.

### V5 · "Mientras sigues en lo tuyo" — agilidad sin plazos

**Fotograma A:**
```
Colombian woman putting her phone into her bag and walking away,
mid-stride, everyday street in a Colombian city, morning light,
movement and ease, vertical 9:16, subject lower third, sky space above
```

**Fotograma B:**
```
Same woman later in the day, pausing to check her phone,
small satisfied expression, warm end-of-day light, blue shadows,
vertical 9:16, generous negative space, photorealistic
```

### V6 · "Una sola vez" — agilidad sin plazos

**Fotograma A:**
```
Over-the-shoulder view of a Colombian person facing a blank smartphone
screen, slight frustration, dim indoor light, vertical 9:16,
screen left neutral for post-production interface
```

**Fotograma B:**
```
Same person, relaxed, phone lowered, soft exhale, calm expression,
clean bright background in near-white and pale blue,
vertical 9:16, large empty area for text, photorealistic
```

---

## 5. Prompts · piezas estáticas por campaña

### C1 — Convenio por sectores

**C1-A, "No sabías que podías":**
```
Colombian man, 40s, looking at a printed payroll slip in his hands,
curious thoughtful expression, modest kitchen table, morning light,
cool blue tones, 4:5 composition, subject on the right,
large clean area on the left for headline, photorealistic
```

**C1-B, "Pregunta antes de asumir":**
```
Composite of three Colombian workers from different ordinary sectors,
neutral generic clothing with no logos, calm confident expressions,
flat navy blue background, even soft light, 4:5,
empty band across the top for headline, photorealistic
```

### C2 — Empleados sector privado

**C2-A, "No es solo para públicos":**
```
Colombian woman in plain office attire at a small private company desk,
looking directly at camera with a composed confident expression,
soft daylight, blue and white environment, 4:5,
subject left, clean space on the right for text, photorealistic
```

**C2-B, "Miramos tu trabajo":**
```
Colombian man in work clothes, arms crossed without aggression,
standing in a small workshop, steady calm gaze,
natural light with cool blue fill, 4:5,
lower third left empty for text, photorealistic
```

### C3 — Reportados · **leer la nota de cumplimiento**

> **Corrección obligatoria al lote anterior.** El brand book prohíbe
> expresamente la expresión "sin importar tu historial" y toda promesa de
> aprobación. El copy que propuse para C3 bordeaba esa prohibición. El ángulo
> se reencuadra: **no se habla del historial, se habla de que lo que se
> evalúa es la estabilidad laboral.** Nada de "aquí sí te prestamos", nada de
> "aquí sí calificas", nada de "tu historial no cierra la puerta".
>
> Copy correcto: *"Lo que evaluamos es tu estabilidad laboral y que la cuota
> te quepa. Con cuatro meses en tu empresa puedes solicitarlo."*

**C3-A, "Lo que evaluamos":**
```
Colombian person seated at a table, calm and attentive,
hands relaxed, soft neutral interior, warm light with cool shadows,
reassuring and non-judgmental mood, 4:5,
wide empty space above subject for text, photorealistic
```

### C4 — Retargeting

**C4-A, "Lo dejaste a medias":**
```
Colombian person's hands resting beside a smartphone on a table,
screen neutral, unhurried pause, soft indoor evening light,
blue and white palette, 4:5, device lower right,
large clean space upper left for text, photorealistic
```

---

## 6. Revisión antes de entregar

Cada pieza pasa por esta lista. Si falla una, no sale.

- [ ] ¿Solo paleta oficial `#051B3E`, `#009AC9`, `#FFFFFF`?
- [ ] ¿Poppins, máximo dos pesos?
- [ ] ¿Logo arriba a la izquierda con su zona de exclusión?
- [ ] ¿Texto montado en post, ninguno generado por el modelo?
- [ ] ¿Sin billetes, monedas ni símbolos de dinero?
- [ ] ¿Sin logotipos de terceros legibles en ropa o entorno?
- [ ] ¿Sin promesa de aprobación, sin "sin importar tu historial",
      sin urgencia artificial, sin "última oportunidad"?
- [ ] ¿Sin plazos exactos? Nada de "en 24 horas", "el mismo día", "en días".
- [ ] ¿Aparece el habilitador de los cuatro meses de antigüedad?
- [ ] ¿La persona se lee como colombiana real y no como banco de imágenes?
- [ ] ¿La pieza transmite alivio y no presión?
- [ ] ¿Carlos Andrés o Paola Andrea la entenderían en cinco segundos?
- [ ] ¿Una sola idea y un solo llamado a la acción?

---

## 7. Nomenclatura de archivos

```
almi_<campaña>_<pieza>_<formato>_v<n>.<ext>
```

Ejemplos: `almi_c2_a_4x5_v1.png`, `almi_v1_frameA_9x16_v2.png`

Mantener el mismo nombre entre la versión generada y la escalada, cambiando
solo el número de versión. Así se puede rastrear qué pieza rindió cuándo.
