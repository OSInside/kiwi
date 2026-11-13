/*
 * Mark the section of the page which is currently read in the
 * "On this page" navigation, see .templates/layout.html. The current
 * section is the last one whose heading scrolled above the upper
 * part of the window. At the end of the page the headings of the
 * last sections can't scroll up that far, there the last section
 * is the current one
 */
document.addEventListener('DOMContentLoaded', function () {
    var links = document.querySelectorAll('.kiwi-page-toc ul ul a[href^="#"]');
    var current = 'kiwi-page-toc-current';
    var entries = [];
    links.forEach(function (link) {
        var section = document.getElementById(
            decodeURIComponent(link.getAttribute('href').substring(1))
        );
        if (section) {
            entries.push({ link: link, section: section });
        }
    });
    if (! entries.length) {
        return;
    }

    function update() {
        var limit = window.innerHeight / 4;
        var active = entries[0];
        var bottom = document.documentElement.scrollHeight - 2;
        entries.forEach(function (entry) {
            if (entry.section.getBoundingClientRect().top <= limit) {
                active = entry;
            }
        });
        if (window.innerHeight + window.scrollY >= bottom) {
            active = entries[entries.length - 1];
        }
        entries.forEach(function (entry) {
            entry.link.classList.toggle(current, entry === active);
        });
    }

    var scheduled = false;
    window.addEventListener('scroll', function () {
        if (! scheduled) {
            scheduled = true;
            window.requestAnimationFrame(function () {
                scheduled = false;
                update();
            });
        }
    }, { passive: true });
    update();
});

/*
 * Add a copy button to the code blocks. Code blocks with commands
 * prefixed by a "$ " prompt copy only the commands, without the
 * prompt and without the command output. Commands continued on
 * the next line by a trailing backslash are copied completely
 */
function kiwiCodeToCopy(text) {
    var lines = text.replace(/\n$/, '').split('\n');
    var commands = [];
    var continued = false;
    lines.forEach(function (line) {
        if (continued) {
            commands.push(line);
        } else if (line.indexOf('$ ') === 0) {
            line = line.substring(2);
            commands.push(line);
        } else {
            return;
        }
        continued = /\\$/.test(line);
    });
    return commands.length ? commands.join('\n') : lines.join('\n');
}

function kiwiCopyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
        var area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.appendChild(area);
        area.select();
        var copied = document.execCommand('copy');
        document.body.removeChild(area);
        if (copied) {
            resolve();
        } else {
            reject(new Error('copy failed'));
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    var label = 'Copy to clipboard';
    document.querySelectorAll('.rst-content div[class^="highlight-"]').forEach(
        function (block) {
            var pre = block.querySelector('pre');
            if (! pre) {
                return;
            }
            var button = document.createElement('button');
            var icon = document.createElement('span');
            var timer = null;
            button.type = 'button';
            button.className = 'kiwi-copy';
            button.title = label;
            button.setAttribute('aria-label', label);
            icon.className = 'fa fa-clipboard';
            icon.setAttribute('aria-hidden', 'true');
            button.appendChild(icon);
            button.addEventListener('click', function () {
                kiwiCopyText(kiwiCodeToCopy(pre.textContent)).then(function () {
                    icon.className = 'fa fa-check';
                    button.classList.add('kiwi-copy-done');
                    button.title = 'Copied';
                    clearTimeout(timer);
                    timer = setTimeout(function () {
                        icon.className = 'fa fa-clipboard';
                        button.classList.remove('kiwi-copy-done');
                        button.title = label;
                    }, 2000);
                });
            });
            block.appendChild(button);
        }
    );
});
