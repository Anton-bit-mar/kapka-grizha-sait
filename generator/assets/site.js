(function () {
  var btn = document.getElementById('menu-btn');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Мега-меню „Магазин“ (на телефон се отваря с натискане)
  Array.prototype.forEach.call(document.querySelectorAll('.mega-wrap'), function (w) {
    var b = w.querySelector('.mega-btn');
    b.addEventListener('click', function () {
      var o = w.classList.toggle('open');
      b.setAttribute('aria-expanded', o ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { w.classList.remove('open'); b.setAttribute('aria-expanded', 'false'); } });
  });

  // Ленти със стрелки
  Array.prototype.forEach.call(document.querySelectorAll('.rail-wrap'), function (w) {
    var rail = w.querySelector('.rail'), prev = w.querySelector('.prev'), next = w.querySelector('.next');
    function upd() {
      prev.disabled = rail.scrollLeft < 8;
      next.disabled = rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 8;
    }
    prev.addEventListener('click', function () { rail.scrollBy({ left: -rail.clientWidth * 0.8 }); });
    next.addEventListener('click', function () { rail.scrollBy({ left: rail.clientWidth * 0.8 }); });
    rail.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd); upd();
  });

  // ---- Търсачка -------------------------------------------------------------
  // Всичко се свежда до „скелет“ на латиница, за да се намира продуктът и при
  // кирилица/латиница („дийп блу“ = „Deep Blue“), главни/малки букви, тирета,
  // ™, окончания („лавандулово“) и дребни грешки („лавандла“).
  var TR = { 'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sht', 'ъ': 'a', 'ь': 'y', 'ю': 'yu', 'я': 'ya', 'ё': 'yo', 'ы': 'i', 'э': 'e' };
  function skel(s) {
    s = String(s || '').toLowerCase();
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    s = s.replace(/[а-яё]/g, function (c) { return TR[c] || c; });
    s = s.replace(/ch/g, '\u0001').replace(/c(?=[eiy])/g, 's').replace(/c/g, 'k').replace(/\u0001/g, 'ch')
      .replace(/ph/g, 'f').replace(/th/g, 't').replace(/ee|ea|ie/g, 'i').replace(/oo|ou/g, 'u')
      .replace(/y/g, 'i').replace(/w/g, 'v').replace(/q/g, 'k').replace(/x/g, 'ks').replace(/ts/g, 's')
      .replace(/gu(?=[aeiou])/g, 'g').replace(/dzh|dj|zh/g, 'j').replace(/([a-z])\1+/g, '$1');
    return s.replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function lev(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var prev = [], cur, i, j;
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur = [i]; var best = i;
      for (j = 1; j <= b.length; j++) {
        cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (cur[j] < best) best = cur[j];
      }
      if (best > max) return max + 1;
      prev = cur;
    }
    return prev[b.length];
  }
  function field(s) {
    var k = skel(s), w = k ? k.split(' ') : [];
    var pairs = [];
    for (var i = 0; i + 1 < w.length; i++) pairs.push(w[i] + w[i + 1]);
    return { s: ' ' + k, c: w.join(''), w: w.concat(pairs) };
  }
  // Колко добре дума t пасва на поле f (0 = не пасва)
  function hit(t, f, fuzzy) {
    if (f.s.indexOf(' ' + t) !== -1) return 3;           // начало на дума
    if (t.length < 3) return 0;
    if (f.c.indexOf(t) !== -1) return 2;                 // вътре в дума / слято („ролон“)
    if (!fuzzy || t.length < 5) return 0;
    var need = Math.max(4, t.length - 3), max = t.length >= 8 ? 2 : 1;
    for (var i = 0; i < f.w.length; i++) {
      var w = f.w[i], n = 0;
      while (n < w.length && n < t.length && w[n] === t[n]) n++;
      if (n >= need && w.length >= need) return 1.5;     // окончание: „лавандулово“
      if (w.length >= 4 && lev(t, w, max) <= max) return 1; // правописна грешка
    }
    return 0;
  }
  var W = { n: 10, a: 7, l: 5, m: 3, c: 3 };
  var IDX = (window.KAPKA_IDX || []).map(function (p, i) {
    var o = { p: p, i: i, f: {} };
    for (var k in W) o.f[k] = field(p[k]);
    o.raw = String(p.n || '').toLowerCase().replace(/^dōterra\s+/, '');
    return o;
  });
  // Връща [{o, score, body}] сортирани по точност
  function search(query, bodyOf) {
    var rawQ = String(query).toLowerCase().trim();
    var terms = skel(String(query).replace(/(\S)-(?=\S)/g, '$1')).split(' ').filter(Boolean); // „рол-он“ → „ролон“
    if (!terms.length) return [];
    var out = [];
    IDX.forEach(function (o) {
      var total = 0, named = true;
      for (var j = 0; j < terms.length; j++) {
        var t = terms[j], best = 0;
        for (var k in W) { var h = hit(t, o.f[k], k !== 'm' && k !== 'c'); if (h * W[k] > best) best = h * W[k]; }
        if (!best) {
          named = false;
          var b = bodyOf && bodyOf(o.p.u);
          var hb = b ? hit(t, b, false) : 0;
          if (!hb) return;
          best = hb * 0.5;
        }
        total += t.length < 3 ? best * 0.2 : best; // „on“, „hd“ тежат малко
      }
      if (o.f.n.s.indexOf(' ' + terms.join(' ')) === 0) total += 20; // името започва със заявката
      var raw = o.raw, rq = rawQ;                                     // и буквално, на същата азбука:
      if (raw.indexOf(rq) === 0) total += 40;                         // „ла“ → първо „Лавандула“, „Лайм“
      else if (raw.indexOf(' ' + rq) !== -1) total += 15;
      out.push({ o: o, score: total, body: !named });
    });
    out.sort(function (x, y) { return (x.body - y.body) || (y.score - x.score) || (x.o.i - y.o.i); });
    return out;
  }

  // Предложения под търсачката в горната лента
  var topQ = document.getElementById('top-q'), sug = document.getElementById('suggest');
  if (topQ && sug && IDX.length) {
    var form = topQ.form, root = form.action.replace(/katalog\.html.*$/, ''), sel = -1;
    var preQ = new URLSearchParams(location.search).get('q');
    if (preQ && /katalog\.html/.test(location.pathname)) topQ.value = preQ;
    var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
    var close = function () { sug.hidden = true; sel = -1; topQ.setAttribute('aria-expanded', 'false'); };
    var mark = function () {
      Array.prototype.forEach.call(sug.children, function (li, i) { li.setAttribute('aria-selected', i === sel ? 'true' : 'false'); });
    };
    topQ.addEventListener('input', function () {
      var v = topQ.value.trim();
      if (!v) { close(); return; }
      var res = search(v).slice(0, 6);
      var h = res.map(function (r) {
        var p = r.o.p;
        return '<li role="option" aria-selected="false"><a href="' + root + 'produkti/' + p.u + '.html"><img src="' + root + 'images/' + p.i + '" alt="">' +
          '<span><b>' + esc(p.n) + '</b><small>' + esc(p.m || p.c) + '</small></span></a></li>';
      }).join('');
      h += '<li role="option" aria-selected="false" class="sug-all"><a href="' + root + 'katalog.html?q=' + encodeURIComponent(v) + '">' +
        (res.length ? 'Всички резултати за „' + esc(v) + '“ →' : 'Няма точно съвпадение. Потърсете в описанията →') + '</a></li>';
      sug.innerHTML = h; sug.hidden = false; sel = -1; topQ.setAttribute('aria-expanded', 'true');
    });
    topQ.addEventListener('keydown', function (e) {
      if (sug.hidden) return;
      var n = sug.children.length;
      if (e.key === 'ArrowDown') { sel = (sel + 1) % n; mark(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { sel = (sel - 1 + n) % n; mark(); e.preventDefault(); }
      else if (e.key === 'Escape') { close(); }
      else if (e.key === 'Enter' && sel >= 0) { e.preventDefault(); location.href = sug.children[sel].querySelector('a').href; }
    });
    document.addEventListener('click', function (e) { if (!form.contains(e.target)) close(); });
    topQ.addEventListener('focus', function () { if (topQ.value.trim() && sug.innerHTML) { sug.hidden = false; topQ.setAttribute('aria-expanded', 'true'); } });
  }

  // Каталог: търсене и филтър по категория
  var q = document.getElementById('q');
  var chips = document.getElementById('chips');
  if (q && chips) {
    var secs = Array.prototype.slice.call(document.querySelectorAll('.cat-sec'));
    var empty = document.getElementById('empty');
    var results = document.getElementById('results'), resHead = document.getElementById('res-head');
    var resMain = document.getElementById('res-main'), resMore = document.getElementById('res-more'), resSub = document.getElementById('res-sub');
    var filter = '', cards = {}, bodies = {};
    secs.forEach(function (s) {
      s.querySelectorAll('.card').forEach(function (c) {
        var a = c.querySelector('.card-name'), slug = a.getAttribute('href').replace(/^.*\/|\.html$/g, '');
        if (!cards[slug]) { cards[slug] = c; bodies[slug] = field(c.getAttribute('data-k') || ''); }
      });
    });
    var bodyOf = function (u) { return bodies[u]; };
    var apply = function () {
      var v = q.value.trim();
      if (!v) {
        results.hidden = true;
        var shown = 0;
        secs.forEach(function (s) {
          var on = !filter || s.getAttribute('data-sec') === filter;
          s.hidden = !on; if (on) shown++;
        });
        empty.hidden = shown !== 0;
        return;
      }
      var res = search(v, bodyOf).filter(function (r) {
        var c = cards[r.o.p.u];
        return c && (!filter || c.getAttribute('data-cat') === filter);
      });
      secs.forEach(function (s) { s.hidden = true; });
      resMain.innerHTML = ''; resMore.innerHTML = '';
      var main = 0, more = 0;
      res.forEach(function (r) {
        var c = cards[r.o.p.u].cloneNode(true);
        c.hidden = false;
        if (r.body) { resMore.appendChild(c); more++; } else { resMain.appendChild(c); main++; }
      });
      var total = main + more;
      results.hidden = total === 0; empty.hidden = total !== 0;
      resHead.textContent = main ? 'Намерени продукти за „' + v + '“: ' + main : 'Няма продукт с това име.';
      resSub.hidden = !more;
      resSub.textContent = main ? 'Споменават „' + v + '“ в описанието си (' + more + ')' : 'Тези продукти споменават „' + v + '“ в описанието си (' + more + '):';
    };
    var t;
    q.addEventListener('input', function () {
      clearTimeout(t); t = setTimeout(apply, 80);
      try { var u = new URL(location.href); if (q.value.trim()) u.searchParams.set('q', q.value.trim()); else u.searchParams.delete('q'); history.replaceState(null, '', u); } catch (e) {}
    });
    var pre = new URLSearchParams(location.search).get('q');
    if (pre) { q.value = pre; apply(); }
    chips.addEventListener('click', function (e) {
      var b = e.target.closest('.chip'); if (!b) return;
      filter = b.getAttribute('data-f');
      chips.querySelectorAll('.chip').forEach(function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
      apply();
    });
  }

  // Форми (наръчник, среща): изпращат се към Netlify Forms, когато сайтът е качен там.
  Array.prototype.forEach.call(document.querySelectorAll('form.lead-form'), function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = f.querySelector('.form-msg');
      var btn = f.querySelector('button[type=submit]');
      var done = f.getAttribute('data-done');
      var body = new URLSearchParams(new FormData(f)).toString();
      btn.disabled = true;
      function show(html) { msg.innerHTML = html; msg.hidden = false; btn.disabled = false; }
      var ok = function () {
        f.reset();
        show(done ? 'Благодаря! <a href="' + done + '" download>Изтеглете наръчника тук</a>. Ще ви пиша скоро.'
                  : 'Благодаря! Получих съобщението и ще ви пиша, за да се уговорим.');
      };
      fetch('/', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: body })
        .then(function (r) { if (r.ok) ok(); else throw r; })
        .catch(function () {
          show('Формата ще заработи, когато сайтът е публикуван. Дотогава ми пишете във Viber или Instagram.' +
               (done ? ' <a href="' + done + '" download>Наръчникът е тук.</a>' : ''));
        });
    });
  });

  // Тест „Кое масло е за вас“
  var quiz = document.getElementById('quiz');
  if (quiz) {
    var data = JSON.parse(quiz.getAttribute('data-quiz'));
    var Q = [
      { k: 'g', t: 'Какво търсите най-много?', a: [['vecher', 'Спокойни вечери и уют'], ['dom', 'Свеж и приятен дом'], ['energia', 'Енергия и фокус през деня'], ['koja', 'Грижа за кожата'], ['deca', 'Нещо за децата']] },
      { k: 's', t: 'Кои аромати харесвате?', a: [['cvetni', 'Цветни и нежни'], ['citrus', 'Цитрусови и слънчеви'], ['darvesni', 'Дървесни и топли'], ['svezhi', 'Свежи и ментови']] },
      { k: 'u', t: 'Как искате да ги използвате?', a: [['difuzer', 'В дифузер, за аромат в стаята'], ['rolon', 'Върху кожата, с готов рол-он'], ['dvete', 'И двете']] },
      { k: 'e', t: 'Използвали ли сте етерични масла досега?', a: [['nov', 'Не, тепърва започвам'], ['opit', 'Да, имам някои']] }
    ];
    // цел / аромат / употреба за всеки продукт
    var T = {
      27: ['vecher koja', 'cvetni', 'difuzer'], 95: ['vecher deca', 'cvetni', 'rolon'], 81: ['vecher', 'cvetni darvesni', 'difuzer'],
      9: ['vecher', 'darvesni', 'difuzer'], 28: ['dom energia', 'citrus', 'difuzer'], 63: ['dom energia', 'citrus', 'difuzer'],
      79: ['dom', 'svezhi citrus', 'difuzer'], 51: ['dom energia', 'citrus', 'difuzer'], 37: ['energia', 'svezhi', 'difuzer'],
      72: ['energia', 'darvesni', 'rolon'], 69: ['energia', 'citrus cvetni', 'difuzer'], 20: ['koja', 'darvesni', 'difuzer rolon'],
      80: ['koja', 'cvetni', 'rolon'], 32: ['koja dom', 'svezhi', 'difuzer rolon'], 113: ['deca', 'cvetni citrus darvesni svezhi', 'rolon'],
      115: ['deca vecher', 'cvetni', 'rolon'], 119: ['deca energia', 'svezhi', 'rolon'], 74: ['dom', 'darvesni citrus', 'difuzer'],
      101: ['dom', 'darvesni', 'rolon']
    };
    var ans = {}, step = 0;
    function has(list, v) { return (' ' + list + ' ').indexOf(' ' + v + ' ') !== -1; }
    function card(id) {
      var p = data.p[id]; if (!p) return '';
      return '<a class="card" href="produkti/' + p.s + '.html"><span class="card-img"><img src="images/' + p.i + '" alt=""></span>' +
        '<span class="card-body"><span class="card-name">' + p.n + '</span><span class="card-meta">' + p.m + '</span></span></a>';
    }
    function result() {
      var sc = Object.keys(T).map(function (id) {
        var t = T[id], s = 0;
        if (has(t[0], ans.g)) s += 4;
        if (has(t[1], ans.s)) s += 2;
        if (ans.u === 'dvete' || has(t[2], ans.u)) s += 1;
        return [id, s];
      }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 3);
      var buy = data.ext ? '<a class="btn" href="' + data.buy + '" target="_blank" rel="noopener">Поръчай с моя линк</a>'
                         : '<a class="btn" href="' + data.buy + '">Поръчай с моя линк</a>';
      var extra = ans.e === 'nov' ? '<p class="quiz-tip">Тепърва започвате? Добро начало е и <a href="produkti/' + data.p[1].s + '.html">' + data.p[1].n + '</a> и <a href="produkti/' + data.p[121].s + '.html">' + data.p[121].n + '</a>.</p>' : '';
      quiz.innerHTML = '<div class="quiz-res"><p class="script">вашите масла</p><h3 class="h3">Предлагам ви да започнете с тези 3</h3>' +
        '<div class="grid">' + sc.map(function (x) { return card(x[0]); }).join('') + '</div>' + extra +
        '<div class="actions">' + buy + '<a class="btn ghost" href="' + data.viber + '">Обсъди с мен във Viber</a>' +
        '<button type="button" class="btn ghost" id="quiz-again">Отначало</button></div></div>';
      document.getElementById('quiz-again').onclick = function () { ans = {}; step = 0; render(); };
    }
    function render() {
      if (step >= Q.length) return result();
      var q = Q[step];
      quiz.innerHTML = '<p class="quiz-step">Въпрос ' + (step + 1) + ' от ' + Q.length + '</p>' +
        '<div class="quiz-bar"><span style="width:' + (step / Q.length * 100) + '%"></span></div>' +
        '<h3 class="h3">' + q.t + '</h3><div class="quiz-opts">' +
        q.a.map(function (a) { return '<button type="button" class="quiz-opt" data-v="' + a[0] + '">' + a[1] + '</button>'; }).join('') +
        '</div>' + (step ? '<button type="button" class="quiz-back">← Назад</button>' : '');
      Array.prototype.forEach.call(quiz.querySelectorAll('.quiz-opt'), function (b) {
        b.onclick = function () { ans[q.k] = b.getAttribute('data-v'); step++; render(); };
      });
      var back = quiz.querySelector('.quiz-back');
      if (back) back.onclick = function () { step--; render(); };
    }
    render();
  }
})();
