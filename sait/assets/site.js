(function () {
  var btn = document.getElementById('menu-btn');
  var nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Каталог: търсене и филтър по категория
  var q = document.getElementById('q');
  var chips = document.getElementById('chips');
  if (q && chips) {
  var secs = Array.prototype.slice.call(document.querySelectorAll('.cat-sec'));
  var empty = document.getElementById('empty');
  var filter = '';
  var norm = function (s) { return s.toLowerCase().replace(/ō/g, 'o').replace(/á/g, 'a'); };
  secs.forEach(function (s) {
    s.querySelectorAll('.card').forEach(function (c) { c._t = norm(c.textContent); });
  });
  function apply() {
    var terms = norm(q.value.trim()).split(/\s+/).filter(Boolean);
    var shown = 0;
    secs.forEach(function (s) {
      var inCat = !filter || s.getAttribute('data-sec') === filter;
      var n = 0;
      s.querySelectorAll('.card').forEach(function (c) {
        var ok = inCat && terms.every(function (t) { return c._t.indexOf(t) !== -1; });
        c.hidden = !ok; if (ok) n++;
      });
      s.hidden = n === 0; shown += n;
    });
    empty.hidden = shown !== 0;
  }
  q.addEventListener('input', apply);
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
