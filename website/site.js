/* Barrett Lemons — shared behavior: photo lightbox + writing list. No dependencies. */
(function () {
  'use strict';

  /* ---------- Lightbox ----------
     Any <a class="zoom" href="full-image"> opens in a modal. Without JS (or <dialog>
     support) the link simply opens the image itself. */
  if (window.HTMLDialogElement) {
    var dlg = document.createElement('dialog');
    dlg.className = 'lightbox';
    dlg.innerHTML = '<button class="lightbox-close" type="button" aria-label="Close">Close</button>' +
      '<img alt=""><p class="lightbox-caption"></p>';
    document.body.appendChild(dlg);
    var big = dlg.querySelector('img');
    var cap = dlg.querySelector('.lightbox-caption');

    document.addEventListener('click', function (e) {
      var a = e.target.closest && e.target.closest('a.zoom');
      if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      var thumb = a.querySelector('img');
      var fig = a.closest('figure');
      var fc = fig && fig.querySelector('figcaption');
      big.src = a.href;
      big.alt = thumb ? thumb.alt : '';
      cap.textContent = fc ? fc.textContent : '';
      dlg.showModal();
    });

    dlg.addEventListener('click', function (e) {
      if (e.target !== big) dlg.close();
    });
    dlg.addEventListener('close', function () { big.removeAttribute('src'); });
  }

  /* ---------- Writing list ----------
     <ol data-posts data-base="writing/" data-limit="3"> is filled from writing/posts.json.
     The homepage section and nav link stay hidden until there is at least one post. */
  var lists = document.querySelectorAll('[data-posts]');
  if (!lists.length || !window.fetch) return;

  var base = lists[0].getAttribute('data-base') || '';
  fetch(base + 'posts.json', { cache: 'no-cache' })
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (posts) {
      posts = (posts || []).filter(function (p) { return !p.draft; })
        .sort(function (a, b) { return a.date < b.date ? 1 : -1; });

      lists.forEach(function (ol) {
        var limit = parseInt(ol.getAttribute('data-limit') || '0', 10);
        var b = ol.getAttribute('data-base') || '';
        (limit ? posts.slice(0, limit) : posts).forEach(function (p) {
          var li = document.createElement('li');
          var d = new Date(p.date + 'T12:00:00');
          li.innerHTML =
            '<time datetime="' + p.date + '"></time>' +
            '<div><a class="post-title"></a><p class="post-summary"></p></div>';
          li.querySelector('time').textContent =
            d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
          var link = li.querySelector('a');
          link.href = b + p.slug + '.html';
          link.textContent = p.title;
          var sum = li.querySelector('.post-summary');
          if (p.summary) sum.textContent = p.summary; else sum.remove();
          ol.appendChild(li);
        });
      });

      if (posts.length) {
        document.querySelectorAll('#writing, [data-writing-link]').forEach(function (el) {
          el.hidden = false;
        });
      } else {
        document.querySelectorAll('[data-posts-empty]').forEach(function (el) { el.hidden = false; });
      }
    })
    .catch(function () {});
})();
