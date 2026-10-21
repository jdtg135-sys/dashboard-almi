/* =======================================================================
   ESPIA DE LA CAPA DE DATOS — cotizador ALMI
   -----------------------------------------------------------------------
   Para que: el valor de conversion llega en cero desde el 1-oct. El monto
   SI llega a GA4 como metrica (3,3 millones de promedio), pero la variable
   "JS - loan_amount" de GTM, que lee window.dataLayer, devuelve 0. Hay que
   ver con que nombre y de que tipo viaja el monto en el momento exacto en
   que dispara loan_request_created.

   Como usarlo:
   1. Abrir https://cotizador.almifinanciera.com en una pestana nueva.
   2. F12 -> pestana "Console".
   3. Pegar TODO este archivo y dar Enter. Debe responder "espia activo".
   4. Hacer la solicitud completa, hasta que diga que quedo creada.
   5. Volver a la consola y escribir:  copy(ALMI.informe())
      Eso copia el informe al portapapeles. Pegarlo en el chat.

   No modifica nada del sitio: solo observa y registra.
   ======================================================================= */
(function () {
  var CLAVES = ['loan_amount', 'selectedAmount', 'selected_amount', 'newAmount',
                'new_amount', 'maxApproved', 'max_approved', 'value', 'amount',
                'monto', 'approvedAmount', 'credit_amount'];

  var registro = [];
  var fbqCalls = [];

  function limpiarNumero(v) {
    var b = String(v).replace(/[^0-9.,]/g, '');
    if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(b)) b = b.replace(/\./g, '').replace(',', '.');
    else if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(b)) b = b.replace(/,/g, '');
    else b = b.replace(',', '.');
    var n = parseFloat(b);
    return isNaN(n) ? null : n;
  }

  function tipoYValor(v) {
    return { tipo: typeof v, valor: v, esNumero: typeof v === 'number',
             parseado: typeof v === 'string' ? limpiarNumero(v) : null };
  }

  function montosEn(obj) {
    var out = {};
    for (var k in obj) {
      if (!Object.prototype.hasOwnProperty.call(obj, k)) continue;
      // cualquier clave que suene a monto, no solo las que esperamos
      if (CLAVES.indexOf(k) > -1 || /amount|monto|valor|value|salary|salario/i.test(k)) {
        out[k] = tipoYValor(obj[k]);
      }
    }
    return out;
  }

  // --- lo que ya habia antes de activar el espia ---
  var previos = (window.dataLayer || []).map(function (x) {
    return { evento: x && (x.event || '(sin evento)'), montos: montosEn(x || {}),
             claves: Object.keys(x || {}) };
  });

  // --- interceptar los push nuevos ---
  var dl = window.dataLayer = window.dataLayer || [];
  var pushOriginal = dl.push.bind(dl);
  dl.push = function (obj) {
    try {
      registro.push({
        momento: new Date().toISOString(),
        evento: obj && (obj.event || '(sin evento)'),
        claves: Object.keys(obj || {}),
        montos: montosEn(obj || {}),
        // que devolveria nuestra variable de GTM en ESTE instante
        variableGTM: (function () {
          try {
            for (var i = dl.length - 1; i >= 0; i--) {
              var capa = dl[i];
              if (!capa) continue;
              for (var k = 0; k < CLAVES.length; k++) {
                var v = capa[CLAVES[k]];
                if (v === undefined || v === null) continue;
                if (typeof v === 'number' && v > 0) return { encontrado: CLAVES[k], valor: v, tipo: 'number' };
                if (typeof v === 'string') {
                  var b = v.replace(/[^0-9.,]/g, '');
                  if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(b)) {
                    b = b.replace(/\./g, '').replace(',', '.');
                  } else if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(b)) {
                    b = b.replace(/,/g, '');
                  } else {
                    b = b.replace(',', '.');
                  }
                  var n = parseFloat(b);
                  if (!isNaN(n) && n > 0) return { encontrado: CLAVES[k], valor: n, tipo: 'string' };
                }
              }
            }
          } catch (e) {}
          return { encontrado: null, valor: 0 };
        })(),
        crudo: (function () { try { return JSON.parse(JSON.stringify(obj)); } catch (e) { return String(obj); } })()
      });
    } catch (e) {}
    return pushOriginal(obj);
  };

  // --- interceptar lo que recibe el pixel de Meta ---
  if (typeof window.fbq === 'function') {
    var fbqOriginal = window.fbq;
    window.fbq = function () {
      try { fbqCalls.push(Array.prototype.slice.call(arguments)); } catch (e) {}
      return fbqOriginal.apply(this, arguments);
    };
    for (var p in fbqOriginal) {
      if (Object.prototype.hasOwnProperty.call(fbqOriginal, p)) window.fbq[p] = fbqOriginal[p];
    }
  }

  window.ALMI = {
    informe: function () {
      return JSON.stringify({
        url: location.href,
        previos: previos,
        pushes: registro,
        fbq: fbqCalls,
        // estado final: que ve nuestra variable al terminar
        variableAlFinal: (function () {
          var r = {};
          (window.dataLayer || []).forEach(function (capa) {
            if (!capa) return;
            Object.keys(montosEn(capa)).forEach(function (k) { r[k] = montosEn(capa)[k]; });
          });
          return r;
        })()
      }, null, 1);
    },
    eventos: function () { return registro.map(function (r) { return r.evento; }); },
    montos: function () { return registro.filter(function (r) { return Object.keys(r.montos).length; }); }
  };

  console.log('%cespia activo', 'color:#0a0;font-weight:bold',
              '— ya habia ' + previos.length + ' entradas. Haz la solicitud y luego: copy(ALMI.informe())');
})();
