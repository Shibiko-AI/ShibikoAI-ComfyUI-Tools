import { api } from '../../scripts/api.js';
import { app } from '../../scripts/app.js';
import { $el } from '../../scripts/ui.js';

function loadCSS(url) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    link.onload = resolve;
    link.onerror = reject;
    document.head.appendChild(link);
  });
}

function loadHljsStyleBlock() {
  if (document.getElementById('hljs-style')) {
    return;
  }

  const style = document.createElement('style');
  style.id = 'hljs-style';
  style.innerHTML = `
    .get-position-style {
      left: 0px;
      top: 0px;
      width: 100%;
      height: 100%;
      font-size: 10px;
    }
    
    .get-position-style pre {
      height: calc(100% - 2rem);
    }
    
    pre code.hljs {
      padding: 1.25em 0.5rem 0.5rem 0.5rem;
    }
    
    code.hljs {
      display: flex;
      flex: 1;
      border: 1px solid;
      border-radius: 0.25rem;
      border-color: var(--border-color);
      color: #abb2bf;
      background: #282c34;
      height: 100%;
    }
    
    .hljs-ln-numbers {
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      -khtml-user-select: none;
      -moz-user-select: none;
      -ms-user-select: none;
      user-select: none;
  
      text-align: right;
      color: #5c6370;
      border-right: 1px solid #5c6370;
      vertical-align: top;
      padding-right: 8px !important;
    }
    
    .hljs-ln-code {
      padding-left: 8px !important;
    }
  `;
  document.body.appendChild(style);
}

function loadScript(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.onload = () => resolve(window);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function get_position_style(ctx, widget_width, y, node_height) {
  const MARGIN = 16;

  /* Create a transform that deals with all the scrolling and zooming */
  const elRect = ctx.canvas.getBoundingClientRect();
  const initialTransform = ctx.getTransform();

  const transform = new DOMMatrix()
    .scaleSelf(elRect.width / ctx.canvas.width, elRect.height / ctx.canvas.height)
    .multiplySelf(initialTransform)
    .translateSelf(MARGIN, y);

  return {
    position: 'absolute',
    transform: transform.toString(),
    transformOrigin: '0 0',
    maxWidth: `${widget_width - MARGIN * 2}px`,
    minHeight: `${node_height - 56 - MARGIN * 2}px`,
    maxHeight: `${node_height - 56 - MARGIN * 2}px`,    // we're assuming we have the whole height of the node
  };
}

function create_code_widget(code = '# Waiting for code...', language = 'python', id = 0) {
  /** @type {IWidget} */
  let widget = {
    node: id,
    type: 'CODE',
    name: 'CODE',
    html: $el('section', { className: 'get-position-style' }),
    draw(ctx, node, widget_width, y) {
      Object.assign(this.html.style, get_position_style(ctx, widget_width, y, node.size[1]));
    },
  };

  const preBlock = $el('pre', {});
  const innerHTML = hljs.highlight(code, { language }).value;
  const codeBlock = $el('code', { id: `any-node-show-code-${id}`, className: 'language-python', innerHTML });
  preBlock.appendChild(codeBlock);
  widget.html.appendChild(preBlock);
  document.body.appendChild(widget.html);

  api.addEventListener(`any-node-show-code-${id}`, (event) => {
    console.log('API EVENT', event);
    const { code, language, unique_id } = event.detail;
    update_code_widget(code, language, unique_id);
  });

  return widget;
}

function update_code_widget (code = '# Waiting for code...', language = 'python', id = 0) {
  const el = document.getElementById(`any-node-show-code-${id}`);
  el.innerHTML = hljs.highlight(code + '\n\n', { language }).value;
  highlight();
}

function highlight() {
  try {
    hljs.highlightAll();
    hljs.initLineNumbersOnLoad();
  } catch (e) {}
}

const CDN_BASE_URL = 'https://cdnjs.cloudflare.com/ajax/libs';
Promise.all([
  loadScript(`${CDN_BASE_URL}/highlight.js/11.9.0/highlight.min.js`),
  loadCSS(`${CDN_BASE_URL}/highlight.js/11.9.0/styles/atom-one-dark.min.css`),
])
  .then(() => loadScript(`${CDN_BASE_URL}/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js`))
  .then(() => {
    // No vulnerabilities here so suppress the warning
    hljs.configure({ ignoreUnescapedHTML: true });

    app.registerExtension({
      name: 'AnyNodeShowCode',
      async sleep (ms=0) {
        return new Promise(resolve => setTimeout(resolve, ms));
      },
      async nodeCreated(node) {
        await this.sleep(0); // Wait for node object to be updated
        if (node.type === 'AnyNodeShowCode') {
          const widget = create_code_widget('# Waiting for code...', 'python', node.id);
          loadHljsStyleBlock();
          highlight();

          node.serialize_widgets = false;
          node.addCustomWidget(widget);
          node.onRemoved = function () {
            widget.html.remove();
            // const { [`any-node-show-code-${widget.node}`]:[listener] } = getEventListeners(api);
            // api.removeEventListener(`any-node-show-code-${widget.node}`, listener);
          };
        }
      },
    });
  });
