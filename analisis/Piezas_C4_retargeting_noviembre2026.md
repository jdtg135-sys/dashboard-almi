# C4 Retargeting · Lote de piezas y videos
**ALMI Financiera · noviembre 2026 · documento de producción**

Este documento se entrega a producción (diseño y el Claude con Magnific). Trae el diagnóstico que lo origina, el inventario de lo que ya existe, los guiones completos de los cuatro videos nuevos, el copy de cada anuncio y las reglas de marca y formato. Todo el contenido numérico viene de Meta y GA4, medido el 9 de noviembre de 2026.

---

## 1. Por qué se renueva C4

C4 es la campaña de retargeting: le habla a quien **ya entró al cotizador y no terminó**. Hoy tiene un problema de concentración y uno de desgaste.

**Concentración.** Del 1 al 8 de noviembre, `c4-video-6` se llevó el 79% de la inversión de la campaña y el 85% de las solicitudes. La campaña entera depende de una sola pieza.

**Desgaste.** Esa misma pieza se está cansando, y se puede comprobar:

| `c4-video-6` | 1-4 nov | 5-8 nov |
|---|---|---|
| Costo por solicitud | 2.362 | **2.875** (+22%) |
| CTR | 4,92 | 4,50 |
| CPM | 9.893 | 9.669 |
| Frecuencia | 1,31 | 1,31 |

El CPM bajó y la frecuencia no se movió. Es decir: **no es que la audiencia se haya saturado ni que la subasta se haya encarecido para nosotros; la pieza perdió poder de atracción.** Esa es la definición de fatiga de creativo y se corrige con piezas nuevas, no con presupuesto.

El resto del inventario no sostiene la campaña: `c4-video-2` escaló de 12.167 a 101.733 de inversión y entregó a 3.083; `c4-video-1` está en 3.908 y `c4-video-3` prácticamente no tiene entrega.

---

## 2. Qué tiene que hacer una pieza de C4 (y en qué se diferencia de C1 y C2)

La persona que ve estos anuncios **ya conoce el producto**. Entró, simuló o avanzó, y se detuvo. Explicarle qué es un crédito por libranza es gastar el anuncio en algo que ya sabe.

El trabajo de C4 es **quitar la cosa concreta que la detuvo**. Y sabemos dónde se detiene, porque el embudo del cotizador lo muestra (GA4, 1 al 8 de noviembre):

| Paso | % de los que entran |
|---|---|
| 1. Selecciona empresa | 100% |
| 2. Clic en cotizar | 85,2% |
| 3. Cuota calculada | 83,5% |
| 4. **Acepta preaprobación** | **61,4%** ← se pierden 22 puntos |
| 5. **Entrega datos personales** | **41,5%** ← se pierden 20 puntos |
| 6. Datos bancarios | 37,2% |
| 7. Solicitud creada | 35,3% |

Hay dos fugas, y son las dos más grandes del recorrido:

- **Entre ver la cuota y aceptar la preaprobación.** Vio el número y no siguió.
- **Entre aceptar y entregar datos personales.** Dijo que sí y se frenó al momento de dar información.

**Cada uno de los cuatro videos ataca una de esas dos fugas.** Esa es la lógica del lote y es lo que lo diferencia de producir cuatro piezas bonitas sueltas.

---

## 3. Lo que ya existe y no se ha usado

Hay cuatro estáticas de C4 ya diseñadas, en 1x1 y 4x5, sin subir a la cuenta:

| Archivo | Titular | Fuga que ataca |
|---|---|---|
| `almi_c4_a_*` | "Vuelve a ver tu cuota." | Cuota → preaprobación |
| `almi_c4_b_*` | "Tu crédito sigue disponible." | General / retomar |
| `almi_c4_texto1_*` | "Tu cuota, cuando estés listo." | Cuota → preaprobación |
| `almi_c4_texto2_*` | "Sin filas, sin fiador, 100% en línea." | General |

**Observación de producción:** las cuatro resuelven bien la fuga de la cuota y el mensaje de "retoma", pero **ninguna toca la segunda fuga**, la de los datos personales, que vale 20 puntos del embudo. Ese hueco lo cubren los videos V2 y V4 de este lote.

Las cuatro estáticas entran tal como están. No hay que rehacerlas.

---

## 4. Reglas de marca · obligatorias

Tomadas del Brand Book v2.0. Una pieza que incumpla cualquiera de estas se devuelve.

**Paleta, y solo esta:** Azul Oscuro `#051B3E` (40-50%), Celeste Vívido `#009AC9` (25-35%, exclusivo de CTA y acentos), Blanco `#FFFFFF` (20-30%), Negro `#000000` solo en texto legal.

**Tipografía:** Poppins. Bold en titulares y cifras, Regular en cuerpo, Light en legal. **Máximo dos pesos por pieza.**

**Logo:** versión blanca, esquina superior izquierda, zona de exclusión igual a la altura de la A del ícono. Sin sombras, sin rotación, sin distorsión.

**Legal obligatorio al pie de toda pieza:**
> Aprobación sujeta a estudio de crédito y políticas de ALMI Financiera S.A.S.

**Arquetipo: el Cuidador.** Acompaña, no presiona. En retargeting esto importa el doble, porque la tentación natural del formato es la insistencia.

**Prohibido, sin excepción:**

- "Aprobación garantizada", "sin importar tu historial", "crédito inmediato sin condiciones", "última oportunidad".
- Cualquier forma de urgencia artificial: cuentas regresivas, "quedan pocos cupos", "tu solicitud vence hoy".
- Cualquier forma de reproche: "no terminaste", "te quedaste a mitad", "¿se te olvidó?". El tono es *tu proceso te está esperando*, nunca *tú fallaste*.
- Plazos exactos de desembolso. Se habla de agilidad, no de días.

**Dato de producto que sí va:** la antigüedad requerida es de **6 meses** en la empresa. Seis, no cuatro.

**Destino de todas las piezas:** `https://cotizador.almifinanciera.com/`

---

## 5. Casting y dirección de arte

Las dos personas del Brand Book, ambas presentes en el lote:

**Carlos Andrés**, 35-48, operativo (logística, manufactura, servicios). Proveedor principal del hogar. Ropa de trabajo real, manos de trabajo, entornos de bodega, taller o casa de barrio.

**Paola Andrea**, 28-42, administrativa o servicios. Madre o jefa de hogar. Oficina sencilla, casa ordenada, celular en mano.

**Reglas de realismo, que es donde se cae el material genérico:**

- Colombia, no genérico latino. Ropa, interiores y luz creíbles en Cali o Bogotá.
- Nada de oficinas corporativas de stock, trajes, rascacielos ni gente aplaudiendo.
- Edad real en la piel y en las manos. Sin retoque de belleza.
- Expresión: alivio contenido o concentración tranquila. **Nunca euforia.**
- El celular es protagonista: el proceso ocurre ahí.
- Luz natural, hora del día identificable.

---

## 6. Los cuatro videos

Formato común a los cuatro:

- **9:16**, 1080 × 1920, MP4 H.264, 30 fps.
- **Duración 15 a 18 segundos.** Gancho en los primeros 3.
- **Legibles sin audio.** Todo mensaje crítico va en pantalla; el audio es refuerzo, nunca soporte único.
- Texto en pantalla dentro del 80% central vertical, fuera de las zonas que tapan la interfaz de Reels y Stories.
- Cierre con tarjeta final: fondo `#051B3E`, logo, titular, botón celeste y legal.
- Sin música con letra. Sin voz en off locutada estilo radio.

---

### V1 · "El número no se mueve"

**Fuga que ataca:** cuota calculada → preaprobación.
**Persona:** Carlos Andrés. **Pilar:** beneficios funcionales.

La duda real en ese paso es *¿el número que vi es el que voy a pagar?*. La pieza responde eso y nada más.

| Seg | Imagen | Texto en pantalla |
|---|---|---|
| 0-3 | Primer plano del celular con una cuota en pantalla. El dedo se detiene sobre ella, no avanza. | **El número que viste es el que pagas.** |
| 3-8 | Carlos sentado al final del turno, mira la pantalla, respira, asiente. | La cuota sale directo de tu nómina. |
| 8-13 | Plano de la mano desplazándose en el cotizador, avanzando al siguiente paso. | Fija, sin sorpresas, mes a mes. |
| 13-17 | Tarjeta final. | **Vuelve a ver tu cuota** · botón "Simula tu cuota" |

**Lo que no debe aparecer:** cifras de cuota inventadas. Si se muestra un monto en pantalla, tiene que ser uno coherente con el simulador real; si no hay un número validado, se muestra la interfaz desenfocada.

---

### V2 · "Para qué te pedimos lo que te pedimos"

**Fuga que ataca:** preaprobación → datos personales. **Es la pieza que no existe hoy en ningún formato.**
**Persona:** Paola Andrea. **Pilar:** innovación / detrás de ALMI.

La duda real es *¿para qué quieren mis datos y qué van a hacer con ellos?*. Se responde con transparencia, que es el territorio natural de la marca.

| Seg | Imagen | Texto en pantalla |
|---|---|---|
| 0-3 | Paola en casa, celular en mano, se detiene en un formulario. | **¿Por qué te pedimos estos datos?** |
| 3-8 | Plano cercano del formulario, campos simples, pocos. | Para confirmar que la cuota te cabe. Nada más. |
| 8-13 | Ella escribe tranquila, sin apuro. Luz de tarde. | Sin extractos. Sin cartas laborales. Sin fiador. |
| 13-17 | Tarjeta final. | **Termina en línea, desde tu celular** · botón "Retoma tu solicitud" |

> **Verificar antes de producir:** si se quiere afirmar algo sobre tratamiento de datos o sobre consulta en centrales de riesgo, el texto exacto lo aprueba el área legal de ALMI. **No producir ninguna versión que afirme que el proceso no afecta el historial financiero sin esa aprobación por escrito.**

---

### V3 · "Donde lo dejaste"

**Fuga que ataca:** retomar sin empezar de cero. Es la objeción de esfuerzo.
**Persona:** Carlos Andrés. **Pilar:** beneficios funcionales.

La duda real es *¿tengo que hacer todo otra vez?*.

| Seg | Imagen | Texto en pantalla |
|---|---|---|
| 0-3 | Celular sobre la mesa de la cocina, pantalla apagada. Una mano lo toma. | **No empiezas de cero.** |
| 3-8 | La pantalla se enciende en el punto exacto donde quedó el proceso. | Tu solicitud sigue donde la dejaste. |
| 8-13 | Carlos avanza dos pasos, sin fricción. Plano de la mano y la pantalla. | Lo terminas en minutos, desde el celular. |
| 13-17 | Tarjeta final. | **Tu crédito sigue disponible** · botón "Retoma tu solicitud" |

**Tono crítico aquí:** "no empiezas de cero" es un alivio. "No terminaste" es un reproche. La diferencia es toda la pieza.

---

### V4 · "Avanzar no es firmar"

**Fuga que ataca:** preaprobación → datos personales, por miedo al compromiso.
**Persona:** Paola Andrea. **Pilar:** educación financiera.

La duda real es *si sigo, ¿ya quedé amarrada?*.

| Seg | Imagen | Texto en pantalla |
|---|---|---|
| 0-3 | Paola mira el celular con una ceja levantada, dudando. | **¿Si avanzo, ya estoy comprometida?** |
| 3-8 | Plano de la pantalla, paso a paso simple. | No. Decides al final, con el número en frente. |
| 8-13 | Ella deja el celular, se sirve un café, lo retoma. Sin prisa. | Puedes mirarlo hoy y decidir mañana. |
| 13-17 | Tarjeta final. | **Simula sin compromiso** · botón "Simula tu cuota" |

> **Verificar antes de producir:** la frase "decides al final" tiene que corresponder al flujo real del cotizador. Confirmar con producto en qué paso exacto existe compromiso, y ajustar el guion a eso si difiere.

---

## 7. Las cuatro gráficas nuevas

Cada video tiene su gemela gráfica. Mismo mensaje, mismo ángulo, formato
distinto. Se hace así por dos razones: en retargeting la gráfica suele ganarle
al video en coste por clic, y tener el par permite saber si lo que funciona es
**el mensaje o el formato**, que con piezas sueltas nunca se sabe.

Con las cuatro que ya existen, C4 queda con ocho gráficas y cuatro videos.

**Regla que no se negocia:** el texto se monta en post, en Poppins. **Ningún
texto lo genera el modelo de imagen.** Los modelos deforman las tildes y la ñ,
y una pieza de una financiera con un error tipográfico cuesta credibilidad.
El prompt debe pedir siempre el espacio limpio donde va el texto.

---

### E1 · "Para qué te pedimos tus datos" — gemela de V2
**Fuga:** preaprobación → datos personales. **Persona:** Paola Andrea.
**Tipo:** fotográfica.

- **Titular:** Te pedimos pocos datos. Y te decimos para qué.
- **Bajada:** Para confirmar que la cuota te cabe. Nada más.
- **Habilitador:** Con 6 meses en tu empresa ya puedes solicitar.
- **Botón:** Retoma tu solicitud

```
Colombian woman in her thirties at a small kitchen table at home,
holding a smartphone with both hands, calm and unhurried expression,
looking down at the screen, soft late afternoon daylight from a window,
cool blue and white interior, no brand logos anywhere,
4:5 composition, subject on the lower right,
large clean uncluttered area across the top left for headline text,
photorealistic, natural skin texture, no beauty retouching
```

---

### E2 · "Avanzar no es firmar" — gemela de V4
**Fuga:** preaprobación → datos, por miedo al compromiso. **Persona:** Paola Andrea.
**Tipo:** tipográfica sobre fondo navy.

- **Titular:** Simular no te compromete.
- **Bajada:** Miras el número, lo piensas y decides después.
- **Botón:** Simula tu cuota

Sin fotografía. Fondo `#051B3E` pleno, titular en Poppins Bold blanco, arco
celeste inferior derecho como en las piezas tipográficas que ya existen, para
que la familia se reconozca. Es la pieza más barata de producir y la que mejor
aguanta el recorte a 1:1.

> **Verificar antes de producir:** igual que en V4, “decides después” tiene que
> corresponder al flujo real del cotizador. Confirmar con producto en qué paso
> exacto existe compromiso.

---

### E3 · "El número no se mueve" — gemela de V1
**Fuga:** cuota calculada → preaprobación. **Persona:** Carlos Andrés.
**Tipo:** fotográfica, plano cerrado.

- **Titular:** El número que viste es el que pagas.
- **Bajada:** Sale directo de tu nómina. Fija, mes a mes.
- **Habilitador:** Con 6 meses en tu empresa ya puedes solicitar.
- **Botón:** Vuelve a ver tu cuota

```
Close-up of the weathered hands of a Colombian man in his forties
holding a smartphone, screen facing away or neutral and unreadable,
worn work jacket sleeve visible, end of the workday,
plain industrial wall out of focus behind, cool blue shadows,
no brand logos anywhere, 4:5 composition, hands in the lower third,
large clean empty space in the upper two thirds for headline text,
photorealistic, real skin texture on the hands, no beauty retouching
```

**Nota:** la pantalla va neutra o desenfocada. Si se quiere mostrar una cuota
real, el número lo monta diseño en post y tiene que ser coherente con el
simulador; nunca un monto inventado por el modelo.

---

### E4 · "No empiezas de cero" — gemela de V3
**Objeción:** esfuerzo. **Persona:** Carlos Andrés. **Tipo:** tipográfica con
elemento de interfaz.

- **Titular:** No empiezas de cero.
- **Bajada:** Tu solicitud sigue donde la dejaste. La terminas en minutos.
- **Botón:** Retoma tu solicitud

Fondo `#051B3E`. A la derecha, una representación limpia y simplificada del
avance del cotizador —una barra de pasos con los primeros marcados— dibujada en
vectores por diseño, **no generada por el modelo**. Es el único recurso gráfico
del lote que muestra producto, y es justo el que responde la objeción.

---

### Formatos de las gráficas

| Relación | Resolución | Dónde |
|---|---|---|
| 4:5 | 1080 × 1350 | Feed de Facebook e Instagram, la principal |
| 1:1 | 1080 × 1080 | Feed cuadrado y ubicaciones mixtas |
| 9:16 | 1080 × 1920 | Historias y Reels |

Zona segura: 120 px por lado en 4:5, 100 px en 1:1, y en 9:16 dejar 250 px
arriba y 420 px abajo libres de texto, que es lo que tapa la interfaz.

**Ajustes de Magnific.** Mystic con realismo alto y fidelidad al prompt
media-alta; generar a la relación nativa y luego Upscaler a 2× con engine
Illusio, creativity entre 0 y 1 para que no invente rasgos, HDR entre 0 y 2 y
resemblance alta. Relight solo si la toma sale demasiado cálida y hay que
empujarla al azul de marca. Style Transfer no se usa: rompe la coherencia entre
piezas. El error más frecuente y más dañino aquí es lo sobreprocesado: una
imagen con HDR alto se lee como publicidad agresiva, que es lo contrario del
arquetipo Cuidador.

**Nombres de archivo:**

```
almi_c4_e1_4x5_v1.png   almi_c4_e1_1x1_v1.png   almi_c4_e1_9x16_v1.png
almi_c4_e2_4x5_v1.png   almi_c4_e2_1x1_v1.png   almi_c4_e2_9x16_v1.png
almi_c4_e3_4x5_v1.png   almi_c4_e3_1x1_v1.png   almi_c4_e3_9x16_v1.png
almi_c4_e4_4x5_v1.png   almi_c4_e4_1x1_v1.png   almi_c4_e4_9x16_v1.png
```

---

## 8. Copy de los anuncios

Cuatro cuerpos, cuatro títulos y dos descripciones, para que Meta combine. Todos cumplen el framework de la marca: gancho cotidiano → explicación simple → tranquilidad → CTA amable.

**Cuerpos**

1. Tu solicitud sigue donde la dejaste. No tienes que empezar de nuevo: la retomas desde tu celular y la terminas cuando estés listo.
2. La cuota que viste es la que pagas. Sale directo de tu nómina, fija y sin sorpresas. Con 6 meses en tu empresa ya puedes solicitar.
3. Simular no te compromete a nada. Miras el número, lo piensas y decides después. Sin extractos bancarios, sin cartas laborales y sin fiador.
4. Te pedimos pocos datos y te decimos para qué: para confirmar que la cuota te cabe. Todo en línea, sin filas y sin papeleo.

**Títulos**

- Retoma tu solicitud
- Tu cuota te espera
- Decides tú, al final
- Sin filas, sin fiador

**Descripciones**

- Descuento directo por nómina
- 100% en línea, desde tu celular

**Llamado a la acción de Meta:** `GET_QUOTE` ("Obtener cotización").

---

## 9. Resumen de entregables

| Pieza | Estado | Formatos a entregar |
|---|---|---|
| V1 a V4 · videos | **por producir** | 9:16 (1080×1920). Opcional 4:5 recortado con el texto reubicado, no escalado. |
| E1 a E4 · gráficas nuevas | **por producir** | 4:5, 1:1 y 9:16 |
| 4 gráficas existentes | ya entregadas | 1:1 y 4:5, entran sin cambios |

Son **8 archivos de video o imagen nuevos** (4 videos + 4 gráficas), que con los
tres formatos de cada gráfica suman 16 archivos nuevos en total.

**Nomenclatura**, igual a la del lote anterior para no romper el reporte:

```
almi_c4_v1_9x16_v1.mp4     almi_c4_e1_4x5_v1.png
almi_c4_v2_9x16_v1.mp4     almi_c4_e2_4x5_v1.png
almi_c4_v3_9x16_v1.mp4     almi_c4_e3_4x5_v1.png
almi_c4_v4_9x16_v1.mp4     almi_c4_e4_4x5_v1.png
```

El sufijo `c4` indica campaña, como en `almi_c4_a_4x5_v1.png`. Mantenerlo: es lo
que permite saber a qué campaña pertenece cada archivo sin abrirlo. `v` para
video, `e` para estática.

---

## 10. Cómo se montan

El conjunto `retargeting-general` **no es dinámico**, así que cada pieza entra
como un anuncio independiente y convive con lo que ya corre. Agregar anuncios a
un conjunto que no es dinámico no reinicia el aprendizaje.

**El problema de meter las doce de una.** Entre las 8 gráficas y los 4 videos
serían doce anuncios nuevos sobre los cinco que ya existen. Meta reparte el
presupuesto del conjunto entre todos, así que con diecisiete anuncios ninguno
junta entregas suficientes para que el algoritmo distinga cuál rinde: en la
práctica elige dos o tres al azar temprano y apaga el resto. Por eso el lote
entra en dos olas.

**Ola 1 · al recibir el material**

1. Entran los **4 videos** y las **4 gráficas nuevas** (E1 a E4): ocho anuncios.
2. Se apagan `c4-video-1` (3.908 por solicitud) y `c4-video-3` (sin entrega real).
3. `c4-video-6` **se deja prendido**. Sigue siendo la pieza con más volumen; se
   apaga solo cuando una nueva lo supere, no antes.
4. `c4-video-2` se deja una semana más y se decide con datos.

Quedan diez anuncios activos, que ya es bastante.

**Ola 2 · una semana después**

5. Se apagan las piezas nuevas que no hayan entregado nada y entran las 4
   gráficas que ya existían, para ocupar ese espacio.

**Qué se mira para decidir la ola 2.** Cada par video-gráfica comparte mensaje,
así que la comparación es limpia: si E3 le gana a V1 y E1 le gana a V2, lo que
funciona en retargeting es la gráfica y el siguiente lote se produce así, que
además cuesta una fracción. Si pasa al revés, se concentra en video. Esa
respuesta es el verdadero entregable de este lote.

---

## 11. Revisión antes de entregar

- [ ] ¿Solo `#051B3E`, `#009AC9`, `#FFFFFF` y negro en el legal?
- [ ] ¿Poppins, máximo dos pesos?
- [ ] ¿Logo blanco arriba a la izquierda con su zona de exclusión?
- [ ] ¿Está el legal completo al pie?
- [ ] ¿Dice 6 meses, no 4?
- [ ] ¿Todo el texto está montado en post, ninguno generado por el modelo?
- [ ] ¿Sin billetes, monedas ni símbolos de dinero?
- [ ] ¿Sin logotipos de terceros legibles en ropa o entorno?
- [ ] ¿La persona se lee como colombiana real y no como banco de imágenes?
- [ ] ¿Se entiende sin audio?
- [ ] ¿El gancho ocurre antes del segundo 3?
- [ ] ¿Una sola idea y un solo CTA por pieza?
- [ ] ¿Cero urgencia artificial y cero reproche?
- [ ] ¿Ninguna promesa de aprobación?
- [ ] ¿Las frases marcadas para verificación legal fueron aprobadas por escrito?
- [ ] ¿Carlos Andrés o Paola Andrea lo entienden en 5 segundos?
